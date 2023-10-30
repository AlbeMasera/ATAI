import os
import pickle
from typing import List
import rdflib
from rdflib import Namespace, query
from rdflib.term import IdentifiedNode
import utils

WD = Namespace("http://www.wikidata.org/entity/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")
SCHEMA = Namespace("http://schema.org/")
DDIS = Namespace("http://ddis.ch/atai/")
RDFS = rdflib.namespace.RDFS

HEADER_CONST = """
        PREFIX ddis: <http://ddis.ch/atai/>
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX schema: <http://schema.org/>
    """

GET_FILM_BY_NAME_FILTER = """
            SELECT DISTINCT ?film ?queryByTitle WHERE{
                ?film wdt:P31/wdt:P279* wd:Q2431196.                                                                 
                ?film rdfs:label ?queryByTitle.                                                          
                FILTER(REGEX(?queryByTitle, "%(filmName)s", "i"))
            }
            LIMIT 1
        """


class Graph:
    def __init__(self, filepath: str, is_pickle: bool = False):
        if not is_pickle:
            self.g: rdflib.Graph = rdflib.Graph()
            self.g.parse(filepath, format="turtle")

            with open(pickle_graph_path, "wb") as file:
                pickle.dump(self.g, file)
        else:
            with open(filepath, "rb") as graph:
                self.g: rdflib.Graph = pickle.load(graph)

    def __query(self, query_str: str) -> query.Result:
        print("\n Executing Query: \n", query_str, "\n")
        return self.g.query(HEADER_CONST + query_str)

    def entity_to_label(self, entity: IdentifiedNode) -> IdentifiedNode | None:
        for x in self.g.objects(entity, RDFS.label, True):
            return x
        return None

    def get_movie_with_label(self, film_name: str) -> List[IdentifiedNode]:
        q = GET_FILM_BY_NAME_FILTER % {
            "filmName": utils.lower_remove_sent_endings_at_end(film_name)
        }
        res = list(self.__query(q))
        return res[0] if len(res) > 0 else []
