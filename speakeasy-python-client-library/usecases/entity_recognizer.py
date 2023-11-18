import utils
from transformers import AutoTokenizer, AutoModelForTokenClassification, NerPipeline

NER_MODEL_NAME = "dslim/bert-base-NER-uncased"


class NamedEntity:
    def __init__(self, entity_type, word, start, end, original_text):
        self.entity_type = entity_type
        self.word = word
        self.start = start
        self.end = end
        self.original_text = original_text


class EntityRecognizer:
    def __init__(self):
        tokenizer = AutoTokenizer.from_pretrained(NER_MODEL_NAME, device=-1)
        model = AutoModelForTokenClassification.from_pretrained(NER_MODEL_NAME).to(
            "cpu"
        )
        self.ner_pipeline = NerPipeline(
            model=model, tokenizer=tokenizer, device=-1, aggregation_strategy="average"
        )

    @staticmethod
    def extract_entities(query, predictions):
        entities = []
        for prediction in predictions:
            original_text = query[prediction["start"] : prediction["end"]]
            entities.append(
                NamedEntity(
                    prediction["entity_group"],
                    prediction["word"],
                    prediction["start"],
                    prediction["end"],
                    original_text,
                )
            )
        return entities

    def get_single_entity(self, sentence, is_question=False):
        sentence = utils.add_sentence_ending(sentence, is_question=is_question)
        predictions = self.ner_pipeline(sentence)
        entities = self.extract_entities(sentence, predictions)

        if len(entities) == 1:
            return entities[0]

        entities.sort(key=lambda x: x.start)
        start_entity = entities[0]
        end_entity = max(entities, key=lambda x: x.end)
        merged_text = sentence[start_entity.start : end_entity.end]

        return NamedEntity(
            "MISC",
            f"{start_entity.word} -> {end_entity.word}",
            start_entity.start,
            end_entity.end,
            merged_text,
        )


if __name__ == "__main__":
    query2 = "What is the <relationLabel> of Weathering with You"
    query3 = "What is the <genre> of Good Neighbors?"
    query1 = "What is the <MPAA film rating> of Weathering with You?"

    r1 = "Recommend me a movie like The Dark Knight."
    r2 = "Recommend me a movie like The Dark Knight and The Dark Knight Rises."
    r3 = "Recommend me a movie like The Dark Knight and The Dark Knight Rises and The Dark Knight Returns."
    r4 = "Recommend movies similar to Hamlet and Othello."
    r4 = "Given that I like The Lion King, Pocahontas, and The Beauty and the Beast, can you recommend some movies?"
    r5 = (
        "Recommend movies like Nightmare on Elm Street, Friday the 13th, and Halloween."
    )
    r6 = "Recommend movies similar to Hamlet and Othello.	"

    f1 = "Who is the <director> of Star Wars: Episode VI - Return of the Jedi?	"
    f2 = "Who is the <director> of Star Wars: Episode VI - Return of the Jedi?"
    f3 = "Who is the director of Star Wars: Episode VI - Return of the Jedi? "

    e1 = "Who is the screenwriter of The Masked Gang: Cyprus?"

    w1 = "When was The Godfather released? "

    ec = EntityRecognizer()
    print(ec.get_single_entity(w1).original_text)
