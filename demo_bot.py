from rdflib import Graph, URIRef
from speakeasypy import Speakeasy, Chatroom
from typing import List
from nltk.corpus import wordnet as wn
from transformers import pipeline, set_seed
from sklearn.metrics import pairwise_distances
import time
import pickle
import re  # Regular expressions
import spacy
import graphlib
import numpy as np
import csv
import os
import random
from entity_classification import EntryClassifier

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
        self.ec = EntryClassifier()

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
    
    # ADD DIRECTOR RECOM
    def is_recommendation_query(self, query):
        recommendation_keywords = ["recommend", "recommendation", "recommend movies like", "similar to", "like", "suggest"]
        return any(keyword in query.lower() for keyword in recommendation_keywords)

    def handle_query(self, query):
        entities = self.entity_recognizer.extract_entities(query)

        if self.is_recommendation_query(query):
            # Extract movie titles from entities
            movie_titles = [entity['entity'] for entity in entities if entity['type'] == 'WORK_OF_ART']  # or another relevant type
            # Handle as a recommendation query
            return self.handle_recommendation_query(movie_titles)
        else:
            # Handle as a standard query
            # Further logic to process standard queries
            pass

    def handle_recommendation_query(self, movie_titles):
        # Logic to process recommendation query
        # ...
        return f"Recommendations based on: {', '.join(movie_titles)}"

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
                        f"Hello and welcome! This is {room.my_alias}. I'm happy to answer your questions, ask away :)"
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
                    if self.is_recommendation_query(query):
                        # Handle recommendation query
                        response_message = self.handle_recommendation_query(query)
                        room.post_messages(response_message)
                    elif self.is_sparql(query):
                        respond = self.sparql_query(message.message)
                        room.post_messages(f"Query answer: '{respond}' ")
                    else:
                        try:
                            respond = self.ec.start(query)
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
