import os
import pandas as pd
import rdflib
from enum import Enum
from entity_recognizer import EntityRecognizer
from embeddings_recognition import EmbeddingRecognizer
from Graph import Graph

# Define namespaces
WD = rdflib.Namespace('http://www.wikidata.org/entity/')
WDT = rdflib.Namespace('http://www.wikidata.org/prop/direct/')
DDIS = rdflib.Namespace('http://ddis.ch/atai/')
RDFS = rdflib.namespace.RDFS
SCHEMA = rdflib.Namespace('http://schema.org/')

current_directory = os.path.dirname(os.path.abspath(__file__))
data_folder = os.path.join(current_directory, "data")
CROWD_FILE = os.path.join(data_folder, "crowd_bot.csv")

class AnswerLabel(Enum):
    No = 0
    Position = 1
    Value = 2
    Correct = 3
    Predicate = 4

class CrowdResponse:
    def __init__(self, graph: Graph, level: AnswerLabel, message: str, stats: str | None):
        self.level = level
        self.message = message
        self.stats = stats
        self.embedding_recognizer = EmbeddingRecognizer()
        self.graph = graph

    def __str__(self):
        return f"{self.level.name}: {self.message} ({self.stats if self.stats else 'No stats available'})"

    def get_text(self):
        stat = f"\n({self.stats})" if self.stats else ""
        return f"However, the crowd has an answer: {self.message}{stat}" if self.level != AnswerLabel.No else ""

class CrowdResponder:
    def __init__(self, embedding_recognizer: EmbeddingRecognizer, graph: Graph, file: str = CROWD_FILE):
        self.df = pd.read_csv(file, sep='\t')
        self.embedding_recognizer = embedding_recognizer
        self.graph = graph

    def get_batch_rating(self, batch_id: str) -> str:
        # copied results crowd_calculate.py
        d = {'7QT': 0.142857, '8QT': -0.212121, '9QT': "-0.125320"}
        return str(d.get(batch_id, "Rating not available"))

    def add_label_to_node(self, value: str) -> str:
        if "wikidata" in value:
            node = rdflib.URIRef(value)
            lbl = self.graph.entity_2_label(node)
            return f"{lbl}\n({value})"
        return value

    def response(self, query: str, predicate: rdflib.term.URIRef) -> CrowdResponse:
        if not predicate:
            return CrowdResponse(self.graph, AnswerLabel.No, "Sorry, I couldn't find any predicates in your question. Should we try another question?", None)

        recognized_entity = self.embedding_recognizer.get_crowd_entity(query)
        if not recognized_entity:
            return CrowdResponse(self.graph, AnswerLabel.No, "Sorry, I couldn't find that entity in the dataset. Should we try another question?", None)

        result = self.df[(self.df["Input1ID"] == recognized_entity.node) & (self.df["Input2ID"] == predicate.toPython())]
        if result.empty:
            return self.get_fixed_predicate_answer(recognized_entity.node, predicate)

        majority, stats = self.__calc_stats(result)
        correct_value = result["Input3ID"].values[0]
        if majority > 0:
            correct_value = self.add_label_to_node(correct_value)
            return CrowdResponse(self.graph, AnswerLabel.Correct, f"The crowd agrees that the answer is correct. The answer is {correct_value}", stats)

        values = result["FixValue"].tolist()
        pos = result['FixPosition'].values
        if not values:
            return CrowdResponse(self.graph, AnswerLabel.Position, f"The crowd found errors but did not propose a fixed value. Errors were found at: {pos}", stats)

        if pos and (pos[0] == "Subject" or pos[0] == "Predicate"):
            correct_value = self.add_label_to_node(correct_value)
            return CrowdResponse(self.graph, AnswerLabel.Value, f"The crowd was asked if {correct_value} is correct. They proposed a correction {values[0]} for the {pos[0]}.", stats)

        value = self.add_label_to_node(values[0])
        return CrowdResponse(self.graph, AnswerLabel.Value, f"The crowd found some errors. The proposed fixed value is: {value}.", stats)

    def __calc_stats(self, result) -> tuple[int, str]:
        c = result["CORRECT"].values[0]
        ic = result["INCORRECT"].values[0]
        majority = c - ic
        batch_rating_text = self.get_batch_rating(result["HITTypeId"].values[0])
        stats = f"Voted {c} Correct and {ic} Incorrect. {batch_rating_text if batch_rating_text else 'Rating information not available'}"
        return majority, stats

    def get_fixed_predicate_answer(self, subject: str, predicate: rdflib.term.URIRef) -> CrowdResponse:
        result = self.df[(self.df["Input1ID"] == subject) & (self.df["FixValue"] == predicate.toPython())]
        if result.empty:
            return CrowdResponse(self.graph, AnswerLabel.No, "No answer found in the crowd dataset.")

        _, stats = self.__calc_stats(result)
        correct_value = self.add_label_to_node(result["Input3ID"].values[0])
        return CrowdResponse(self.graph, AnswerLabel.Predicate, f"The crowd suggests the value {correct_value} for this question.", stats)

    def retrieve_batch_rating(self, batch_id: str) -> str:
        # Placeholder for the function to retrieve batch rating dynamically
        return "Rating not available"

if __name__ == '__main__':
    recognizer = EmbeddingRecognizer()
    graph = Graph("speakeasy-python-client-library/usecases/data/pickle_graph.pickel")
    crowd_path = "speakeasy-python-client-library/usecases/data/crowd_bot.csv"
    crowd = CrowdResponder(recognizer, graph, crowd_path)

    query = "Can you tell me the publication date of Tom Meets Zizou?"
    predicate = recognizer.get_predicates(query)
    answer = crowd.response(query, predicate.predicate if predicate else None)
    print(answer)
