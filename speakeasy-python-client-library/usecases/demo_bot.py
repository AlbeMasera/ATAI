import time
import pickle
import re
import spacy
import graphlib
import numpy as np
import csv
import os
import random
from rdflib import Graph, URIRef
from speakeasypy import Speakeasy, Chatroom
from typing import List
from nltk.corpus import wordnet as wn
from transformers import pipeline, set_seed
from sklearn.metrics import pairwise_distances

from embeddings import EmbeddingAnswerer
from entity_classification import EntryClassifier
<<<<<<< Updated upstream
from entity_recognizer import EntityRecognizer
from query_utils import is_recommendation_query
from recommender import MovieRecommender
=======
from crowd_response import CrowdResponder
from embeddings_recognition import EmbeddingRecognizer
>>>>>>> Stashed changes

DEFAULT_HOST_URL = "https://speakeasy.ifi.uzh.ch"
listen_freq = 2


class Agent:
    def __init__(self, username, password):
        self.username = username
        # Initialize the Speakeasy Python framework and login.
        self.speakeasy = Speakeasy(
            host=DEFAULT_HOST_URL, username=username, password=password
        )
        self.speakeasy.login()  # This framework will help you log out automatically when the program terminates.
<<<<<<< Updated upstream
 
        self.graph = Graph()
        pickle_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "pickle_graph.pickel")

        self.embedding_answerer = EmbeddingAnswerer()
        self.entity_recognizer = EntityRecognizer()
        self.ec = EntryClassifier()

        self.movie_recommender = MovieRecommender(self.graph, self.embedding_answerer)
        
=======
        
        self.graph = Graph(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "data",
                "pickle_graph.pickel",
            )
        )
        
        self.embedding_recognizer = EmbeddingRecognizer()
        self.ec = EntryClassifier()

        current_directory = os.path.dirname(os.path.abspath(__file__))
        data_folder = os.path.join(current_directory, "data")
        CROWD_ENTITIES = os.path.join(data_folder, "entities_crowd.csv")

        self.crowd_response = CrowdResponder(self.embedding_recognizer, self.graph, CROWD_ENTITIES)
>>>>>>> Stashed changes

    def handle_none(self, query):
        return self.handle_utf8("None" if query is None else str(query))

    def sparql_query(self, query):
        # clean input
        query = query.replace("'''", "\n")
        query = query.replace("‘’’", "\n")
        query = query.replace("PREFIX", "\nPREFIX")

        try:
            result = self.graph.query(query)
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

    @staticmethod
    def is_sparql(query):
        # Determine if a string is a SPARQL query
        sparql_keywords = ["SELECT", "ASK", "DESCRIBE", "CONSTRUCT", "PREFIX"]
        return any(
            re.search(rf"\b{keyword}\b", query, re.IGNORECASE)
            for keyword in sparql_keywords
        )
    
    
    def handle_query(self, query):
        entities = self.entity_recognizer.extract_entities(query)

        if self.is_recommendation_query(query):
            movie_titles = [entity.word for entity in entities if entity.entity_type in ['WORK_OF_ART', 'ORG', 'MISC']]
            return self.handle_recommendation_query(movie_titles)
        else:
            # Handle standard queries
            return self.ec.start(query)  # EntryClassifier instance

        
    def handle_recommendation_query(self, movie_titles):
        # Get recommendations directly using the movie_titles
        recommendations = self.movie_recommender.recommend(movie_titles)
        return f"Recommended movies: {', '.join(recommendations)}"

        '''
        # Extract movie titles from the query using entity_recognizer
        entities = self.entity_recognizer.extract_entities(query)
        movie_titles = [entity.word for entity in entities if entity.entity_type in ['WORK_OF_ART', 'ORG', 'MISC']]
        ''' 

    def listen(self):
        # Define response templates
        response_templates = [
            "Good question, let's see...",
            "I hear you, let me quickly have a look.",
            "Interesting query, I'm on it!",
            "Hmm, checking now...",
        ]

        while True:
            # only check active chatrooms (i.e., remaining_time > 0) if active=True.
            rooms: List[Chatroom] = self.speakeasy.get_rooms(active=True)
            for room in rooms:
                if not room.initiated:
                    # send a welcome message if room is not initiated
                    room.post_messages(
                        f"Hello and welcome! This is {room.my_alias}.\n" 
                        f"I'm happy to answer your questions. Ask away :)"
                    )
                    room.initiated = True
                # Retrieve messages from this chat room.
                # If only_partner=True, it filters out messages sent by the current bot.
                # If only_new=True, it filters out messages that have already been marked as processed.
                for message in room.get_messages(only_partner=True, only_new=True):
                    print(
                        f"\t- Chatroom {room.room_id} "
                        f"- new message #{message.ordinal}: '{message.message}' "
                        f"- {self.get_time()}"
                    )

                    # Implement your agent here #
                    #
                    # Extract query from message
                    query = message.message

                    # Select a random response template
                    response_message = random.choice(response_templates)

                    # Send a randomized response message
                    room.post_messages(response_message)

                    # Check if it's a recommendation query
                    if is_recommendation_query(query):
                        # Handle recommendation query
                        response_message = self.handle_recommendation_query(query)
                        room.post_messages(response_message)
                    elif self.is_sparql(query):
                        respond = self.sparql_query(message.message)
                        room.post_messages(f"Query answer: '{respond}' ")
                    else:
                        try:
                            respond = self.ec.start(query)
<<<<<<< Updated upstream
=======
                            print(f"Respond: {respond}")

                            predicate = self.embedding_recognizer.get_predicates(query)
                            crowd_response = self.crowd_responder.response(query, predicate.predicate if predicate else None)
                            if crowd_response.level != AnswerLabel.No:
                                crowd_text = crowd_response.get_text()
                                respond += f"\nCrowd Insight: {crowd_text}"

>>>>>>> Stashed changes
                            room.post_messages(respond)
                        except Exception as e:
                            print(f"{str(e)}")
                            room.post_messages("Sorry, I ran into an issue here. Should we try another question instead?")

                    room.mark_as_processed(message)
                # Retrieve reactions from this chat room.
                # If only_new=True, it filters out reactions that have already been marked as processed.
                for reaction in room.get_reactions(only_new=True):
                    print(
                        f"\t- Chatroom {room.room_id} "
                        f"- new reaction #{reaction.message_ordinal}: '{reaction.type}' "
                        f"- {self.get_time()}"
                    )

                    # Implement your agent here #

                    room.post_messages(f"Oh wow.. Thanks for the reaction '{reaction.type}'.")
                    room.mark_as_processed(reaction)

            time.sleep(listen_freq)

    @staticmethod
    def get_time():
        return time.strftime("%H:%M:%S, %d-%m-%Y", time.localtime())


if __name__ == "__main__":
    demo_bot = Agent("kindle-pizzicato-wheat_bot", "zJD7llj0A010Zg")
    demo_bot.listen()
