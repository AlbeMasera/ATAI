from typing import List

import rdflib.term
from rdflib.term import IdentifiedNode, Node, Identifier
from random import randint

import utils


def error_f():
    return "In the program code occurred an error. My apologies"


def movie_not_found(movie_name: str) -> str:
    return f"Could not find a movie with the name: {movie_name}"


def per_not_found(per_name: str) -> str:
    return f"Could not find a person with the name: {per_name}"


def _get_random_answer_from_array(array: list[str]) -> str:
    return array[randint(0, len(array) - 1)]


class Answer(object):
    def __init__(self, answer: str):
        self._text = answer

    def get_text(self) -> str:
        return utils.add_sentence_ending(self._text, is_question=False)

    def __str__(self):
        return f"Answer: {self.get_text()}"

    def with_crowd_opinion(self, crowd_opinion: str):
        if crowd_opinion is None or not any(crowd_opinion):
            return self
        return Answer(f"{self.get_text()} \n\n{crowd_opinion}")

    def with_hint(self, hint: None):
        if hint is None or not any(hint):
            return self
        return Answer(f"{self.get_text()}\n\n{hint}")

    @classmethod
    def error(cls):
        return cls(error_f())

    @classmethod
    def from_question(cls, node: rdflib.term.IdentifiedNode):
        return cls(f"The answer to your question is {node.toPython()}")

    @classmethod
    def node_not_found(cls, node_name):
        # print(f"[-] Could not find a node with the name {node_name}")
        return cls(f"Could not find a node with the name {node_name}")

    @classmethod
    def movie_not_found(cls, movie_name):
        # print(f"[-] Could not find a movie with the name {movie_name} in graph.")
        return cls(movie_not_found(movie_name))

    @classmethod
    def person_not_found(cls, per_name):
        # print(f"[-] Could not find a person with the name {per_name} in graph.")
        return cls(per_not_found(per_name))

    @classmethod
    def from_error(cls, error: str):
        # print(f"[-] ERROR: {error}")
        return "error"

    @classmethod
    def from_movie_graph_node(cls, movie: IdentifiedNode):
        return cls("I think you are looking for the movie: {}".format(movie.toPython()))

    @classmethod
    def from_recommendation(cls, movie: IdentifiedNode, hints: str):
        if not hints or not any(hints):
            return cls(f"I recommend you to watch the movie {movie.toPython()}")

        return cls(
            f"I recommend you to watch the movie {movie.toPython()}\n\nReasons for my choice:\n{hints}"
        )

    @classmethod
    def from_embedding_recommendation(
        cls, movie: IdentifiedNode, movie_link: IdentifiedNode, hints: str
    ):
        if not hints or not any(hints):
            return cls(f"I recommend you to watch the movie {movie.toPython()}")

        return cls(
            f"I recommend you to watch the movie {movie.toPython()}\n({movie_link.toPython()})\n\nReasons for my choice:\n{hints}"
        )

    @classmethod
    def from_general_graph_node(cls, node: IdentifiedNode):
        return cls("I think your are looking for {}".format(node.toPython()))

    @classmethod
    def from_director_graph_node(cls, directors: List[IdentifiedNode], ori_movie: str):
        if not directors or not len(directors):
            return movie_not_found(ori_movie)

        if len(directors) > 1:
            d = "\n".join([f"-> {d.toPython()}" for d in directors])
            return f"Found multiple films with the name '{ori_movie}' and therefore found multiple director names:\n{d}"

        return cls(
            _get_random_answer_from_array(
                "I think you are looking for the director {}"
            ).format(directors[0].toPython())
        )


if __name__ == "__main__":
    mn = IdentifiedNode(Identifier("Pirates"))
    a = Answer.from_movie_graph_node(mn)

    print(a.get_text())
