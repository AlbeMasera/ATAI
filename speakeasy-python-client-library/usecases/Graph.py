import os
import pickle
from typing import List
import rdflib
from rdflib import Namespace, query
from rdflib.term import IdentifiedNode
import utils
import re


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

    def get_answer(self, predicate: str, entity: str) -> str:
        entity = re.search(r"[QP]\d+", entity)
        predicate = re.search(r"[QP]\d+", predicate)
        query = f"""
        SELECT ?result WHERE {{
        wd:{entity.group()} wdt:{predicate.group()} ?result .
        }}
        LIMIT 1
        """
        return self.sparql_query(HEADER_CONST + query)

    def handle_none(self, query):
        return "None" if query is None else str(query)

    def sparql_query(self, query):
        # clean input
        query = query.replace("'''", "\n")
        query = query.replace("‘’’", "\n")
        query = query.replace("PREFIX", "\nPREFIX")

        try:
            result = self.g.query(query)
            # Handle different conditions
            processed_result = []
            for item in result:
                try:
                    # Unpack as (str, int)
                    s, nc = item
                    processed_result.append(
                        (str(self.handle_none(s)), int(self.handle_none(nc)))
                    )
                except ValueError:
                    try:
                        # Unpack as (str, str)
                        s, nc = item
                        processed_result.append(
                            (str(self.handle_none(s)), str(self.handle_none(nc)))
                        )
                    except ValueError:
                        # String value
                        processed_result.append(str(self.handle_none(item[0])))
            result = processed_result
        except Exception as e:
            result = f"Error: {str(e)}"

        return result

    def get_imdb_id_with_label(self, label: str) -> List[IdentifiedNode]:
        query = utils.GET_IMDB_ID_BY_NAME_FILTER % {
            "filmName": utils.lower_remove_sent_endings_at_end(label)
        }
        print(query)
        return self.sparql_query(HEADER_CONST + query)

    def get_genre(self, entity: str) -> str:
        query = utils.GET_GENRE_BY_LABLE % {
            "filmName": utils.lower_remove_sent_endings_at_end(entity)
        }
        print(query)
        return self.sparql_query(HEADER_CONST + query)
