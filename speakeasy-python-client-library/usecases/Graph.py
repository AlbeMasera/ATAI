import os
import pickle
from typing import List, Optional
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
        # Use the film_name variable directly in the FILTER regex
        query = utils.GET_FILM_BY_NAME_FILTER % {
            "filmName": utils.lower_remove_sent_endings_at_end(film_name)
        }
        res = list(self.g.query(HEADER_CONST + query))
        print(f"SPARQL query: {query}") #debug
        print(f"Query result: {res}") #debug
        return res[0] if len(res) > 0 else []

    def get_movie_rating(self, movie_uri: rdflib.URIRef, rating_predicate: str) -> Optional[float]:
        # Construct a SPARQL query to get the movie rating based on the predicate
        rating_query = f"""
        SELECT ?rating WHERE {{
            {movie_uri} wdt:{rating_predicate} ?rating .
        }}
        LIMIT 1
        """
        result = self.g.query(rating_query)
        print(result) #debug
        for row in result:
            return float(row.rating.value)
        return None