import os
import pandas, rdflib
import Graph
from enum import Enum
from collections import Counter
from typing import Unions
from embeddingsRec import EmbeddingRecogniser

WD = rdflib.Namespace("http://www.wikidata.org/entity/")
WDT = rdflib.Namespace("http://www.wikidata.org/prop/direct/")
DDIS = rdflib.Namespace("http://ddis.ch/atai/")
RDFS = rdflib.namespace.RDFS
SCHEMA = rdflib.Namespace("http://schema.org/")


# Get the absolute path to the current directory
current_directory = os.path.dirname(os.path.abspath(__file__))

# Define the relative path to the "data" folder
data_folder = os.path.join(current_directory, "data")

# Use absolute paths for loading files from the "data" folder
CROWD_FILE = os.path.join(data_folder, "crowd_data.tsv")

# Enumeration to represent different levels of answers
class AnswerLevel(Enum):
    No = 0
    Position = 1
    Value = 2
    Correct = 3
    Predicate = 4

# Represents the answer from the crowd
class CrowdAnswer:
    def __init__(self, level: AnswerLevel, message: str, stats: Union[str, None]):
        self.level = level
        self.message = message
        self.stats = stats

    def __str__(self):
        return f"{self.level.name}: {self.message} ({self.stats})"

    # Returns the text representation of the crowd's answer
    def get_text(self):
        if self.level == AnswerLevel.No:
            return ""

        stat = f"\n({self.stats})" if self.stats else ""
        return f"The answer retrieved from crowd data is {self.message}{stat}"

# Get answers from a crowd-sourced dataset
class CrowdAnswerer:
    def __init__(
        self, recogniser: EmbeddingRecogniser, graph: Graph, file: str = CROWD_FILE
    ):
        self.df = pandas.read_csv(file, sep="\t")
        self.graph = graph
        self.recogniser = recogniser

        assert self.graph is not None
    
    # Adds labels to nodes if they belong to Wikidata
    def __add_lbl_if_node(self, value: str) -> str:
        if any(value) and "wikidata" in value:
            node = rdflib.URIRef(value)
            lbl = self.graph.entity_2_label(node)
            return f"{lbl}\n({value})"
        return value

    # Determines if the crowd might have an answer to a given query based on the recognized predicate and entity.
    def might_answer(self, query: str, predicate: rdflib.term.URIRef) -> CrowdAnswer:
        # Check if the predicate is recognized
        if not predicate:
            print("Could not retrieve crowd answer. Predicate is not recognized.")
            return CrowdAnswer(
                AnswerLevel.No,
                "I could not find any predicates in your question.",
                None,
            )
        # Try to recognize an entity from the query
        recognised_entity = self.recogniser.get_crowd_entity(query)
        if not recognised_entity:
            print("Could not retrieve crowd answer. Entity is not recognized.")
            return CrowdAnswer(
                AnswerLevel.No,
                "I could not find any entity in the crowd dataset.",
                None,
            )
        # Search for the recognized entity and predicate in the crowd dataset
        result = self.df[
            (self.df["Input1ID"] == recognised_entity.node)
            & (self.df["Input2ID"] == predicate.toPython())
        ]
        if result.empty:
            print("Could not retrieve crowd answer. No answer could be found.")
            return self.get_fixed_predicate_answer(recognised_entity.node, predicate)

        # Check if the crowd agrees on the correct value
        correct_value = result["Input3ID"].values[0]
        if majority > 0:
            correct_value = self.__add_lbl_if_node(correct_value)
            return CrowdAnswer(
                AnswerLevel.Correct,
                f"The crowd has voted that the answer is correct. The answer is {correct_value}",
                stats,
            )
        # Check if the crowd suggests a fixed value or position
        values = result["FixValue"].tolist()
        pos = result["FixPosition"].values
        if not any(values):
            print("Could not find a correct value.")
            return CrowdAnswer(
                AnswerLevel.Position,
                f"The crowd found some mistakes, but did not propose the fixed value. The error at the following position was found: {pos}",
                stats,
            )
        # Check if the crowd suggests a correction for the subject or predicate
        if any(pos) and pos[0] == "Subject" or pos[0] == "Predicate":
            correct_value = self.__add_lbl_if_node(correct_value)
            print("Crowd answer: Strange POS.s")
            return CrowdAnswer(
                AnswerLevel.Value,
                f"The crowd was asked if {correct_value} is correct. They proposed a correction {values[0]} for the {pos[0]}.",
                stats,
            )
        # Return the crowd's proposed fixed value
        value = self.__add_lbl_if_node(values[0])
        return CrowdAnswer(
            AnswerLevel.Value,
            f"The crowd found some mistakes. The proposed fixed value is: {value}.",
            stats,
        )
        # Calculate the majority vote and statistics from the crowd dataset
        majority, stats = self.__calc_stats(result)