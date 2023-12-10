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
        model = AutoModelForTokenClassification.from_pretrained(NER_MODEL_NAME).to("cpu")
        self.ner_pipeline = NerPipeline(
            model=model, tokenizer=tokenizer, device=-1, aggregation_strategy="average"
        )

    def extract_entities(self, query):
        # Run the query through the NER pipeline to get predictions
        predictions = self.ner_pipeline(query)
        
        # Extract entities from the predictions
        entities = []
        for prediction in predictions:
            entities.append(
                NamedEntity(
                    prediction["entity_group"],
                    prediction["word"],
                    prediction["start"],
                    prediction["end"],
                    query[prediction["start"]:prediction["end"]],
                )
            )
        return entities

    def get_single_entity(self, sentence, is_question=False):
        sentence = utils.add_sentence_ending(sentence, is_question=is_question)
        
        # Directly use extract_entities which now only needs the sentence
        entities = self.extract_entities(sentence)

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

    '''
    def extract_movie_titles(self, sentence):
        predictions = self.ner_pipeline(sentence)
        movie_titles = []

        for prediction in predictions:
            if prediction['entity_group'] == 'WORK_OF_ART':  # assuming WORK_OF_ART can represent movie titles
                movie_titles.append(prediction['word'])

        return movie_titles
    '''
