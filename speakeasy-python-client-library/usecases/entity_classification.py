import os
import rdflib
import multimedia
import utils
import re
import random
from entity_recognizer import EntityRecognizer
import embeddings_recognition as embeddings_rec
import embeddings
import crowd_response
from graph import Graph
import recomender

CROWD_PATH = "speakeasy-python-client-library/usecases/data/crowd_bot.csv"


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
        self.crowd = crowd_response.CrowdResponder(
            self.entity_recognizer, self.graph, CROWD_PATH
        )

    def start(self, query: str) -> str:
        # Preprocess query
        cleaned_query = utils.remove_different_minus_scores(query)

        # Get predicates using embedding recognizer
        predicate = self.embedding_recognizer.get_predicates(cleaned_query)

        print(predicate)

        if (
            not predicate
            or "picture" in cleaned_query.lower()
            or "photo" in cleaned_query.lower()
        ):
            for i in utils.RECCOMENDATION_WORDS:
                entities = self.entity_recognizer.get_entities(cleaned_query)

                if i in cleaned_query.lower():
                    # Ansewer the question using reccomentation
                    answer = self.recomender.recommend_embedding(entities)
                    template = random.choice(self.RECOMMENDATION_RESPONSE_TEMPLATES)
                    formatted_response = template.format(answer)

                    # Motivate the answer
                    formatted_response += (
                        "\n\n"
                        + "I recommend this movie because it is similar to the movies "
                        + (", ".join(entities))
                        + " you like."
                        + "\n"
                        + "The genre of the movie is "
                        + str(self.graph.get_genre(answer)[0])
                    )

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
            try:
                # Answer the question using embeddings
                answer = self.answer_embedding_question(
                    predicate.fixed_query, is_predicate_in_embeddings
                )
            except:
                answer = ""

        else:
            prediction = self.entity_recognizer.get_single_entity(
                query, is_question=True
            )

            entity: rdflib.IdentifiedNode | None = None

            res = self.graph.get_movie_with_label(prediction.original_text)
            entity = res[0]
            try:
                # Answer the question using KG
                answer = str(self.graph.get_answer(predicate.predicate, entity)[0])
            except:
                answer = ""

        # Answer the question using crowd
        if not answer:
            answer_crowd = self.crowd.response(
                query, predicate.predicate if predicate else None
            )
            return answer_crowd.response

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
    q1 = "who is director of Alice in Wonderland"
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

    m1 = "Show me a picture of The Lion King."
    m2 = "Show me a picture of Tom Holland."

    c1 = "What is the box office of The Princess and the Frog?"
    c2 = "Who is the executive producer of X-Men: First Class?"
    c3 = "Can you tell me the publication date of Tom Meets Zizou?"

    ec = EntryClassifier()

    print(ec.start(q1))
    print(ec.start(r4))
    print(ec.start(m1))
    print(ec.start(m2))
    print(ec.start(c1))
    print(ec.start(c2))
    print(ec.start(c3))
