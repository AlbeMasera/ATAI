from typing import List
from enum import Enum
import rdflib.term
from rdflib.term import IdentifiedNode, Node, Identifier
from random import randint
import utils

class ErrorMessages(Enum):
    GENERIC_ERROR = "Sorry, an error occured"
    MOVIE_NOT_FOUND = "Could not find a movie with the name: {}"
    PERSON_NOT_FOUND = "Could not find a person with the name: {}"

# Generate and manage answers based on given input
class Answer(object):
    # Initialize the Answer object with a given answer string.
    def __init__(self, answer: str):
        self._text = answer

    def __str__(self):
        return f"Answer: {self.get_text()}"
    
    # Get the formatted answer text
    def get_text(self) -> str:
        return utils.add_sentence_ending(self._text, is_question=False)

    # Generate a direct answer based on a given RDF node
    @classmethod
    def direct_answer_from_query(cls, node: rdflib.term.IdentifiedNode):
        return cls(f"The answer to your question is {node.toPython()}.")
    
    # Generate a suggested answer based on a given RDF node
    @classmethod
    def suggested_answer_from_node(cls, node: IdentifiedNode):
        return cls("I think you are looking for {}".format(node.toPython()))

    # Generate an answer based on a given movie RDF node
    @classmethod
    def answer_movie_graph_node(cls, movie: IdentifiedNode):
        return cls("I think you are looking for the movie {}".format(movie.toPython()))
    
    # Generate an answer based on a movie director RDF node
    @classmethod
    def answer_director_graph_node(cls, directors: List[IdentifiedNode], ori_movie: str):
        if not directors or not len(directors):
            return movie_not_found(ori_movie)

        # original movie name has multiple directors
        if len(directors) > 1:
            d = "\n".join([f"-> {d.toPython()}" for d in directors])
            return f"Found multiple movies with the name '{ori_movie}' directed by different directors:\n{d}."

        return cls(
            _get_random_answer_from_array(
                "I think you are looking for the director {."
            ).format(directors[0].toPython())
        )

    # Append crowd opinion to the answer 
    def append_crowd_opinion(self, crowd_opinion: str):
        if crowd_opinion is None or not any(crowd_opinion):
            return self
        return Answer(f"{self.get_text()} \n\n{crowd_opinion}")

    # Append hint to the answer
    def append_hint(self, hint: None):
        if hint is None or not any(hint):
            return self
        return Answer(f"{self.get_text()}\n\n{hint}")

    # Get a random answer from a given list of answers
    def _get_random_answer_from_array(array: List[str]) -> str: 
        return array[randint(0, len(array) - 1)]

    # Generate a generic error answer
    @classmethod
    def error(cls):
        return cls(error_f())

    # Generate answer if the node was not found
    @classmethod
    def node_not_found(cls, node_name):
        return cls(f"Could not find a node {node_name}")

    # Generate answer if movie was not found
    @classmethod
    def movie_not_found(cls, movie_name):
        return cls(ErrorMessages.MOVIE_NOT_FOUND.value.format(movie_name))

    # Generate answer if person was not found
    @classmethod
    def person_not_found(cls, per_name):
        return cls(ErrorMessages.PERSON_NOT_FOUND.value.format(per_name))

    # Generate answer based on a given error message
    @classmethod
    def from_error(cls, error: str):
        return "Error occured"

if __name__ == "__main__":
    mn = IdentifiedNode(Identifier("Pirates"))
    a = Answer.answer_movie_graph_node(mn)

    print(a.get_text())
