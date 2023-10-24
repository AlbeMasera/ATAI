from transformers import pipeline, set_seed

set_seed(111)

ner_pipeline = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english")

entities = ner_pipeline("Anna likes studying at UZH.", aggregation_strategy="simple")

for entity in entities:
    print(f"{entity['word']}: {entity['entity_group']} ({entity['score']:.2f})")
