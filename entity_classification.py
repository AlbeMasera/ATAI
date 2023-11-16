import os
import rdflib
import utils
import random
from entity_recognizer import EntityRecognizer
import embeddings_recognition as embeddings_rec
import embeddings
from Graph import Graph


class EntryClassifier:
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

        # Answer the question using embeddings and NER
        return self.answer_embedding_question(
            predicate.fixed_query, is_predicate_in_embeddings
        )

    def answer_embedding_question(
        self, query: str, relation: embeddings.EmbeddingRelation
    ) -> str:
        prediction = self.entity_recognizer.get_single_entity(query, is_question=True)
        entity: rdflib.IdentifiedNode | None = None

        res = self.graph.get_movie_with_label(prediction.original_text)
        entity = res[0]

        answer_entity = self.embedding_answerer.calculate_embedding_node(
            entity, relation.relation_key
        )

        answer_label = self.graph.entity_to_label(answer_entity)
        #return "I think you are looking for {}".format(answer_label.toPython())
        
        # Define response templates
        response_templates = [
            "I think the answer you are looking for is {}.",
            "The answer to your question is {}.",
            "Your query led me to {}."
            "According to the dataset, the answer is {}."
        ]

        # Select a random template
        template = random.choice(response_templates)

        # Format the template with the answer label
        return template.format(answer_label.toPython())


if __name__ == "__main__":
    q = "who is director of Alice in Wonderland" 
    q2 = "who is director of Pirates of the Caribbean: On Stranger Tides"
    q3 = "who is director of Shrek"
    q4 = "who is director of The Dark Knight"
    q5 = "who is the director of Inception"

    f0 = "Who is the director of Good Will Hunting?	"
    f1 = "Who directed The Bridge on the River Kwai?	"
    f2 = "Who is the director of Star Wars: Episode VI - Return of the Jedi?	"

    e1 = "Who is the screenwriter of The Masked Gang: Cyprus?"
    e2 = "What is the MPAA film rating of Weathering with You?" #problem
    e3 = "What is the genre of Good Neighbors?"

    w1 = "When was The Godfather released? " #problem

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

    t1 = "What is the IMDB rating of Inception?" #problem: Sorry, I couldn't find that movie in the database.

    ec = EntryClassifier()
    result = ec.start(e3)

    print(result)
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