import rdflib
from typing import List
from Graph import Graph

class MovieRecommender:
    def __init__(self, graph, embedding_answerer):
        self.graph = graph
        self.embedding_answerer = embedding_answerer

    def recommend(self, movie_titles: List[str], n_recommendations=5) -> List[str]:
        movie_nodes = [self.graph.get_movie_with_label(title)[0] for title in movie_titles if self.graph.get_movie_with_label(title)]

        if not movie_nodes:
            return ["Sorry, I'm not familiar with that movie. Try another one?"]

        similar_movies = self.embedding_answerer.get_n_closest(movie_nodes, n=n_recommendations)

        if not similar_movies:
            return ["This one seems one of a kind.. Should we try another one?"]

        # Filter out the input movies
        recommended_movies = [movie for movie in similar_movies if movie not in movie_nodes]

        # Convert RDF nodes to readable movie titles
        recommended_movie_titles = [self.graph.entity_to_label(movie).toPython() for movie in recommended_movies]

        return recommended_movie_titles
