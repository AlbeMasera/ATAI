import utils
from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import NerPipeline

NER_MODEL = "dslim/bert-base-NER-uncased"


class NerGroups(object):
    def __init__(
        self, entity_group: str, word: str, start: int, end: int, original_text: str
    ):
        self.label = entity_group
        self.word = word
        self.start = start
        self.end = end
        self.original_text = original_text

    def __str__(self):
        return f"NerGroups[{self.label} {self.word} {self.original_text} {self.start} {self.end}]"

    def __repr__(self):
        return self.__str__()


class EntityRecognition(object):
    def __init__(self):
        # load the NER tagger
        tokenizer = AutoTokenizer.from_pretrained(NER_MODEL, device=-1)
        model = AutoModelForTokenClassification.from_pretrained(NER_MODEL).to("cpu")

        # maybe change grouping strategy later
        self.pipeline = NerPipeline(
            model=model, tokenizer=tokenizer, device=-1, aggregation_strategy="average"
        )

        assert self.pipeline, "Should contain pipeline"

    @staticmethod
    def fix_spans(query: str, predictions: list[dict]) -> list[NerGroups]:
        out = []
        for p in predictions:
            original_text = query[p["start"] : p["end"]]

            # add to list
            out.append(
                NerGroups(
                    p["entity_group"], p["word"], p["start"], p["end"], original_text
                )
            )

        # prev = out[0]
        # out2 = []
        # for group in out[1:]:
        #     if group.start <= prev.start + 3 and prev.entity_group == group.entity_group:
        #         prev.word = f"{prev.word} {group.word}"
        #         prev.end = group.end
        #         prev.original_text = query[prev.start:prev.end]
        #         out2.append(prev)
        #     else:
        #         out2.append(prev)
        #         prev = group

        return out

    def get_single_prediction(
        self, sentence: str, is_question=False
    ) -> None | NerGroups:
        predictions: list[NerGroups] = self.get_predictions(sentence, is_question)
        if not predictions:
            return None
        if len(predictions) < 2:
            return predictions[0] if len(predictions) == 1 else []

        # predications more than 2 => clue together
        predictions.sort(key=lambda x: x.start)
        start = predictions[0]

        end = sorted(predictions, key=lambda x: x.end)[-1]

        org_text = sentence[start.start : end.end]
        return NerGroups(
            "MISC", f"{start.word} -> {end.word}", start.start, end.end, org_text
        )

    def get_predictions(self, sentence: str, is_question=False) -> list[NerGroups]:
        print(f"[.] NER: {sentence}")
        # add sentence end => NER result better for name at end of sentence
        sentence = utils.add_sentence_ending(sentence, is_question=is_question)

        # run NER over sentence
        predictions: list[dict] = self.pipeline(sentence)

        return self.fix_spans(sentence, predictions)
