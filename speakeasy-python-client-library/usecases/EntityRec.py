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
        tokenizer = AutoTokenizer.from_pretrained(NER_MODEL, device=0)
        model = AutoModelForTokenClassification.from_pretrained(NER_MODEL).to("cuda:0")

        # maybe change grouping strategy later
        self.pipeline = NerPipeline(
            model=model, tokenizer=tokenizer, device=0, aggregation_strategy="average"
        )

        assert self.pipeline, "Should contain pipeline"

    def get_predictions(self, sentence: str, is_question=False) -> list[NerGroups]:
        print(f"[.] NER: {sentence}")
        # add sentence end => NER result better for name at end of sentence
        sentence = utils.add_sentence_ending(sentence, is_question=is_question)

        # run NER over sentence
        predictions: list[dict] = self.pipeline(sentence)

        return self.fix_spans(sentence, predictions)
