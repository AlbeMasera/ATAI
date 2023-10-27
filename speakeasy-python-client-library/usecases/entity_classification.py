from typing import Tuple
import rdflib
from transformers import pipeline

from Project.NER.EntityRecognition import EntityRecognition, NerGroups
from Project.Graph.krParser import FilmGraph
from Project.crowd import crowdAnswerer
from Project.model.answer import Answer
from Project.model import utility
from Project.embedding import embeddings, embeddingRecogniser
from Project.Recommender import MovieRecommender
import Project.media.multiMediaProcessor as mMP
from Project.media.multiMediaProcessor import MultiMediaProcessor

GRAPH_FILE = "../Project/Resources/14_graph.nt"
GRAPH_FILE_SMALL = "../Project/Resources/small_graph.ttl"
GRAPH_PICKLE = "../Project/Graph/graph_pickle_2.pickle"

MMP_PICKLE = "../Project/media/multimediaprocessor.pickle"


class EntryClassification(object):
    def __init__(self):
        # self.questionClassifier = pipeline("text-classification", model=questionClassifier)
        self.multiMediaProcessor = mMP.from_pickle(MMP_PICKLE)
        self.ner = EntityRecognition()
        self.embeddingAnswer = embeddings.EmbeddingAnswerer()
        self.graph = FilmGraph(GRAPH_PICKLE, is_pickle=True)
        self.movieRecommendation = MovieRecommender.MovieRecommender(
            self.graph, self.embeddingAnswer
        )
        self.embeddingRecogniser = embeddingRecogniser.EmbeddingRecogniser()
        self.crowd = crowdAnswerer.CrowdAnswerer(self.embeddingRecogniser, self.graph)

        assert len(self.graph.g) > 0, "Graph is empty"
        print("[+] Answerer READY")

    # Start function of all the question answering
    def start(self, query: str) -> Answer:
        query = utility.remove_different_minus_scores(query)
        print("[+] start classification")

        predicate = self.embeddingRecogniser.get_predicates(query)

        if predicate:
            crowd_answer = self.crowd.might_answer(query, predicate.predicate)
            if not crowd_answer:
                crowd_answer = crowdAnswerer.CrowdAnswer(
                    crowdAnswerer.AnswerLevel.No,
                    "There was an error in the crowd answerer.",
                    None,
                )

            print(f"[+] found PREDICATE in question")
            em_rl = self.embeddingAnswer.is_predicate_in_embedding(predicate.label)
            if em_rl:
                print(f"[+] found EMBEDDING in question {em_rl.relation_label}")
                answer, answered = self.answer_embedding_question(
                    predicate.fixed_query, em_rl
                )
                if answered:
                    return answer.with_crowd_opinion(crowd_answer.get_text())
                print(f"[X] EMBEDDING did not answer question")

            print("[!] not Embedding")
            print("[+] Try answer STATIC question")
            return self.answer_statical_question(
                predicate.predicate, query
            ).with_crowd_opinion(crowd_answer.get_text())

        return Answer.from_error("This seems to be a question that I cannot answer.")
