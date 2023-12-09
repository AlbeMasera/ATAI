import os
import rdflib
import multimedia
import utils
import re
import random
from entity_recognizer import EntityRecognizer
import embeddings_recognition as embeddings_rec
import embeddings
from graph import Graph
import recomender


class EntryClassifier:
    FACTUAL_RESPONSE_TEMPLATES = [
        "I think the answer you are looking for is {}.",
        "The answer to your question is {}.",
        "Your query led me to {}.",
        "According to the dataset, the answer is {}.",
    ]

    RECOMMENDATION_RESPONSE_TEMPLATES = [
        "I would recommend {}.",
        "Based on your interest, I recommend {}.",
        "I think you would enjoy {}.",
    ]

    IMAGES_RESPONSE_TEMPLATES = [
        "Here is a picture of {}. \n{}",
        "I found this picture of {}. \n{}",
        "I think this picture of {} is relevant. \n{}",
    ]

    def __init__(self):
        # Initialize components
        self.entity_recognizer = EntityRecognizer()
        self.embedding_answerer = embeddings.EmbeddingAnswerer()
        self.graph = Graph(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "data",
                "pickle_graph.pickel",
            )
        )
        self.recomender = recomender.MovieRecommender(self.graph)
        self.embedding_recognizer = embeddings_rec.EmbeddingRecognizer()
        self.multimedia = multimedia.Multimedia(self.graph)

    def start(self, query: str) -> str:
        # Preprocess query
        cleaned_query = utils.remove_different_minus_scores(query)

        # Get predicates using embedding recognizer
        predicate = self.embedding_recognizer.get_predicates(cleaned_query)

        if not predicate:
            for i in utils.RECCOMENDATION_WORDS:
                entities = self.entity_recognizer.get_entities(cleaned_query)

                if i in cleaned_query.lower():
                    # Ansewer the question using reccomentation
                    answer = self.recomender.recommend_embedding(entities)
                    template = random.choice(self.RECOMMENDATION_RESPONSE_TEMPLATES)
                    formatted_response = template.format(answer)
                    return formatted_response
                else:
                    # Answer the question using multimedia
                    answer = self.multimedia.get_image_from_lable(entities[0])
                    if answer:
                        template = random.choice(self.IMAGES_RESPONSE_TEMPLATES)
                        formatted_response = template.format(entities[0], answer)
                        return formatted_response
                    else:
                        return "Sorry, I couldn't find an aswer for your question. Should we try another question?"

        # Check if predicate exists in embeddings
        is_predicate_in_embeddings = self.embedding_answerer.is_predicate_in_embedding(
            predicate.label
        )

        if is_predicate_in_embeddings:
            # Answer the question using embeddings
            answer = self.answer_embedding_question(
                predicate.fixed_query, is_predicate_in_embeddings
            )
            template = random.choice(self.FACTUAL_RESPONSE_TEMPLATES)
            formatted_response = template.format(answer)
            return formatted_response
        else:
            prediction = self.entity_recognizer.get_single_entity(
                query, is_question=True
            )

            entity: rdflib.IdentifiedNode | None = None

            res = self.graph.get_movie_with_label(prediction.original_text)
            entity = res[0]
            # Answer the question using KG
            answer = str(self.graph.get_answer(predicate.predicate, entity)[0])
        template = random.choice(self.FACTUAL_RESPONSE_TEMPLATES)
        formatted_response = template.format(answer)
        return formatted_response

    def answer_embedding_question(
        self, query: str, relation: embeddings.EmbeddingRelation
    ) -> str:
        # handle when questions

        prediction = self.entity_recognizer.get_single_entity(query, is_question=True)
        entity: rdflib.IdentifiedNode | None = None

        res = self.graph.get_movie_with_label(prediction.original_text)
        entity = res[0]

        answer_entity = self.embedding_answerer.calculate_embedding_node(
            entity, relation.relation_key
        )

        answer_label = self.graph.entity_to_label(answer_entity)
        return " {}".format(answer_label.toPython())


if __name__ == "__main__":
    q = "who is director of Alice in Wonderland"
    q2 = "who is director of Pirates of the Caribbean: On Stranger Tides"
    q3 = "who is director of Shrek"
    q4 = "who is director of The Dark Knight"

    f0 = "Who is the director of Good Will Hunting?	"
    f1 = "Who directed The Bridge on the River Kwai?	"
    f2 = "Who is the director of Star Wars: Episode VI - Return of the Jedi?	"

    e1 = "Who is the screenwriter of The Masked Gang: Cyprus?"
    e2 = "What is the MPAA film rating of Weathering with You?"
    e3 = "What is the genre of Shrek?"

    w1 = "When was The Godfather released? "

    r1 = "Recommend me a movie like The Dark Knight."
    r2 = "Recommend me a movie like The Dark Knight and The Dark Knight Rises."
    r3 = "Recommend me a movie like The Dark Knight and The Dark Knight Rises and The Dark Knight Returns."
    r4 = "Given that I like The Lion King, Pocahontas, and The Beauty and the Beast, can you recommend some movies?"
    r5 = (
        "Recommend movies like Nightmare on Elm Street, Friday the 13th, and Halloween."
    )
    r6 = "Recommend movies similar to Hamlet and Othello.	"

    t1 = "What is the IMDB rating of Cars?"

    ec = EntryClassifier()
    print(ec.start(e3))
