import os
import rdflib
import utils
from entity_recognizer import EntityRecognizer
import embeddings_recognition as embeddings_rec
import embeddings
from graph import Graph


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
        return "I think you are looking for {}".format(answer_label.toPython())
