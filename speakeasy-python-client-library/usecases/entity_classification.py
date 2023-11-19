import os
import rdflib
import utils
import re
from entity_recognizer import EntityRecognizer
import embeddings_recognition as embeddings_rec
import embeddings
from graph import Graph
import recomender


class EntryClassifier:
    def __init__(self):
        # Initialize components
        self.entity_recognizer = EntityRecognizer()
        self.embedding_answerer = embeddings.EmbeddingAnswerer()
        self.recomender = recomender.MovieRecommender()
        self.graph = Graph(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "data",
                "pickle_graph.pickel",
            )
        )
        self.embedding_recognizer = embeddings_rec.EmbeddingRecognizer()

    def start(self, query: str) -> str:
        # Preprocess query
        cleaned_query = utils.remove_different_minus_scores(query)

        # Get predicates using embedding recognizer
        predicate = self.embedding_recognizer.get_predicates(cleaned_query)

        # Check if predicate exists in embeddings
        is_predicate_in_embeddings = self.embedding_answerer.is_predicate_in_embedding(
            predicate.label
        )

        if is_predicate_in_embeddings:
            # Answer the question using embeddings
            return self.answer_embedding_question(
                predicate.fixed_query, is_predicate_in_embeddings
            )
        else:
            prediction = self.entity_recognizer.get_single_entity(
                query, is_question=True
            )
            entity: rdflib.IdentifiedNode | None = None

            res = self.graph.get_movie_with_label(prediction.original_text)
            entity = res[0]
            # Answer the question using KG
            return self.graph.get_answer(predicate.predicate, entity)

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
        return "I think you are looking for {}".format(answer_label.toPython())

    def answer_recommendation_question(self, query: str) -> str:
        print(f"[+] start RECOMMENDATION answering of q: {query}")
        predictions: list[
            embeddings_rec.PossiblePredicate
        ] = self.entity_recognizer.get_predicates(query, is_question=False)

        movies = [pre.original_text for pre in predictions]
        return self.recomender.recommend_embedding(movies)


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
    e3 = "What is the genre of Good Neighbors?"

    w1 = "When was The Godfather released? "

    mmq1 = "Show me a picture of Halle Berry."
    mmq2 = "What does Julia Roberts look like?"
    mmq3 = "Let me know what Sandra Bullock looks like."

    r1 = "Recommend me a movie like The Dark Knight."
    r2 = "Recommend me a movie like The Dark Knight and The Dark Knight Rises."
    r3 = "Recommend me a movie like The Dark Knight and The Dark Knight Rises and The Dark Knight Returns."
    r4 = "Given that I like The Lion King, Pocahontas, and The Beauty and the Beast, can you recommend some movies?"
    r5 = (
        "Recommend movies like Nightmare on Elm Street, Friday the 13th, and Halloween."
    )
    r6 = "Recommend movies similar to Hamlet and Othello.	"

    c1 = "What is the box office of The Princess and the Frog?	"
    c2 = "Can you tell me the publication date of Tom Meets Zizou?	"
    c3 = "Who is the executive producer of X-Men: First Class?	"

    t1 = "What is the IMDB rating of Cars?"

    ec = EntryClassifier()
    print(ec.start(t1))
    # print(ec.start(f1))
    # print(ec.start(f2))
    #
    # print(ec.start(r1))
    # print(ec.start(r2))
    # print(ec.start(r3))
    # print(ec.start(r4))
    # print(ec.start(r5))
    # print(ec.start(r6))
    #
    # print(ec.start(q))
    # print(ec.start(q2))
    # print(ec.start(q3))
    # print(ec.start(q4))
    # print(ec.start(e1))
    # print(ec.start(e2))
    # print(ec.start(e3))
    # print(ec.start(mmq1))
    # print(ec.start(mmq2))
    # print(ec.start(mmq3))
    #
    # print(ec.start(c1))
    # print(ec.start(c2))
    # print(ec.start(c3))

    # print(ec.movieRecommendation.recommend_embedding(["The Lion King", "Pocahontas", "The Beauty and the Beast"]))
    # print(ec.movieRecommendation.recommend_embedding(["Nightmare on Elm Street", "Friday the 13th", "Halloween"]))
    # print(ec.movieRecommendation.recommend_embedding(["Hangover"]))
    # print(ec.movieRecommendation.recommend_embedding(["genre"]))
    # print(ec.movieRecommendation.recommend_embedding(["The Dark Knight", "The Dark Knight Rises"]))
