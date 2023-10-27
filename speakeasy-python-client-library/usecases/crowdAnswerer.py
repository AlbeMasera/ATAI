import pandas, rdflib

import Graph
import rdflib
from enum import Enum
from collections import Counter

WD = rdflib.Namespace("http://www.wikidata.org/entity/")
WDT = rdflib.Namespace("http://www.wikidata.org/prop/direct/")
DDIS = rdflib.Namespace("http://ddis.ch/atai/")
RDFS = rdflib.namespace.RDFS
SCHEMA = rdflib.Namespace("http://schema.org/")

CROWD_FILE = "/home/luc/UZH/w22/AI/code/Project/crowd/crowd_bot.csv"


class AnswerLevel(Enum):
    No = 0
    Position = 1
    Value = 2
    Correct = 3
    Predicate = 4


class CrowdAnswer:
    def __init__(self, level: AnswerLevel, message: str, stats: str | None):
        self.level = level
        self.message = message
        self.stats = stats

    def __str__(self):
        return f"{self.level.name}: {self.message} ({self.stats})"

    def get_text(self):
        if self.level == AnswerLevel.No:
            return ""

        stat = f"\n({self.stats})" if self.stats else ""
        return f"However the crowd has an answer: {self.message}{stat}"


class CrowdAnswerer:
    def __init__(self, recogniser, graph: Graph, file: str = CROWD_FILE):
        self.df = pandas.read_csv(file, sep="\t")
        self.graph = graph

        assert self.graph is not None

    def __add_lbl_if_node(self, value: str) -> str:
        if any(value) and "wikidata" in value:
            node = rdflib.URIRef(value)
            lbl = self.graph.entity_2_label(node)
            return f"{lbl}\n({value})"
        return value

    def might_answer(self, query: str, predicate: rdflib.term.URIRef) -> CrowdAnswer:
        if not predicate:
            print("[X] ERROR CROWD Answer: no recognised predicate")
            return CrowdAnswer(
                AnswerLevel.No,
                "I could not find any predicates in your question.",
                None,
            )

        recognised_entity = self.recogniser.get_crowd_entity(query)
        if not recognised_entity:
            print("[.] CROWD Answer: no recognised entity")
            return CrowdAnswer(
                AnswerLevel.No,
                "I could not find any entity in the crowd dataset.",
                None,
            )

        result = self.df[
            (self.df["Input1ID"] == recognised_entity.node)
            & (self.df["Input2ID"] == predicate.toPython())
        ]
        if result.empty:
            print("[.] CROWD Answer: no normal answer found")
            return self.get_fixed_predicate_answer(recognised_entity.node, predicate)

        majority, stats = self.__calc_stats(result)

        correct_value = result["Input3ID"].values[0]
        if majority > 0:
            correct_value = self.__add_lbl_if_node(correct_value)
            return CrowdAnswer(
                AnswerLevel.Correct,
                f"The crowd has voted that the answer is correct. The answer is {correct_value}",
                stats,
            )

        values = result["FixValue"].tolist()
        pos = result["FixPosition"].values
        if not any(values):
            print("[.] CROWD Answer: no correct value found")
            return CrowdAnswer(
                AnswerLevel.Position,
                f"The crowd found some mistakes, but did not propose the fixed value. The error at the following position was found: {pos}",
                stats,
            )

        if any(pos) and pos[0] == "Subject" or pos[0] == "Predicate":
            correct_value = self.__add_lbl_if_node(correct_value)
            print("[.] CROWD Answer: POS WEIRD")
            return CrowdAnswer(
                AnswerLevel.Value,
                f"The crowd was asked if {correct_value} is correct. They proposed a correction {values[0]} for the {pos[0]}.",
                stats,
            )

        value = self.__add_lbl_if_node(values[0])
        return CrowdAnswer(
            AnswerLevel.Value,
            f"The crowd found some mistakes. The proposed fixed value is: {value}.",
            stats,
        )
