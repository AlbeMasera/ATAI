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


class Graph:
    def __init__(self, filepath: str):
        with open(filepath, "rb") as graph:
            self.g: rdflib.Graph = pickle.load(graph)
        
    def entity_to_label(self, entity: IdentifiedNode) -> IdentifiedNode | None:
        for x in self.g.objects(entity, RDFS.label, True):
            return x
        return None

    def get_movie_with_label(self, film_name: str) -> List[IdentifiedNode]:
        query = utils.GET_FILM_BY_NAME_FILTER % {
            "filmName": utils.lower_remove_sent_endings_at_end(film_name)
        }
        res = list(self.g.query(HEADER_CONST + query))
        return res[0] if len(res) > 0 else []
