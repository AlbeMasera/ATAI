from typing import Tuple
import os
from random import randint
from typing import List
import pandas as pd

import embeddings
from graph import Graph


class MovieRecommender(object):
    def __init__(self, graph: Graph):
        self.graph = graph
        self.embeddings = embeddings.EmbeddingAnswerer()

    def recommend_embedding(self, movie_names: List[str]) -> str:
        movie_names = [i for i in movie_names if i != "The" or i != "the" or len(i) < 3]
        movies, movie_nodes = self.get_movies_and_nodes(movie_names)

        if not movie_nodes:
            return self.recommend_random()

        closest = self.embeddings.get_n_closest(movie_nodes, 10)
        if not closest or not any(closest):
            return self.recommend_random()

        closest_set = set(closest)

        # remove given movies from result
        closest_set.difference_update(movie_nodes)

        # transform to movie label list
        lbl_2_ent = {self.graph.entity_to_label(x): x for x in closest_set}

        # filter out movies with the same label (e.g., remove newer versions of the same movie)
        movies = [x for x in lbl_2_ent.keys() if x not in movie_names]

        # get random element
        return str(movies[0])

    def get_movies_and_nodes(self, movie_names: List[str]) -> [List, List]:
        movies = []
        movie_nodes = []
        for mn in movie_names:
            result = self.graph.get_movie_with_label(mn)
            if result and any(result):
                movies.append(result)
                movie_nodes.append(result[0])
        return movies, movie_nodes

    def recommend_random(self) -> str:
        rand_movies = self.graph.get_movie_with_label(chr(randint(97, 122)))
        return str(self.graph.entity_to_label(rand_movies[0]))


if __name__ == "__main__":
    # m1 = "Hamlet"
    # m2 = "Othello"

    # Get the absolute path to the current directory
    current_directory = os.path.dirname(os.path.abspath(__file__))

    # Define the relative path to the "data" folder
    data_folder = os.path.join(current_directory, "data")

    # Use absolute paths for loading files from the "data" folder
    GRAPH_PICKLE = os.path.join(data_folder, "pickle_graph.pickel")

    g = Graph(GRAPH_PICKLE)

    mr = MovieRecommender(g)
    a = mr.recommend_embedding(["The Lion King ", "Pocahontas", "Beauty and the Beast"])
    print(a)

    b = mr.recommend_embedding(["Hamlet ", "Othello"])
    print(b)

    c = mr.recommend_embedding(
        ["Nightmare on Elm Street", "Friday the 13th", "Halloween"]
    )
    print(c)

    d = mr.recommend_embedding(["bohbohboh"])
    print(d)
