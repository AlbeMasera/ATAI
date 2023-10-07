from rdflib import Graph
from speakeasypy import Speakeasy, Chatroom
from typing import List
import time

from SPARQLWrapper import SPARQLWrapper, JSON
import re  # Regular expressions

DEFAULT_HOST_URL = "https://speakeasy.ifi.uzh.ch"
listen_freq = 2


# define an empty knowledge graph
graph = Graph()
# load a knowledge graph
graph.parse(source="speakeasy-python-client-library/graph/14_graph.nt", format="turtle")


class Agent:
    def __init__(self, username, password):
        self.username = username
        # Initialize the Speakeasy Python framework and login.
        self.speakeasy = Speakeasy(
            host=DEFAULT_HOST_URL, username=username, password=password
        )
        self.speakeasy.login()  # This framework will help you log out automatically when the program terminates.

    def sparql_query(self, query):
        # clean input
        query = query.replace("'''", "\n")
        query = query.replace("‘’’", "\n")
        query = query.replace("PREFIX", "\nPREFIX")

        try:
            result = [str(s) for s, in graph.query(query)]
        except:
            result = "Error"

        return result

    @staticmethod
    def is_sparql(query):
        # Determine if a string is a SPARQL query
        sparql_keywords = ["SELECT", "ASK", "DESCRIBE", "CONSTRUCT", "PREFIX"]
        return any(
            re.search(rf"\b{keyword}\b", query, re.IGNORECASE)
            for keyword in sparql_keywords
        )

    def listen(self):
        while True:
            # only check active chatrooms (i.e., remaining_time > 0) if active=True.
            rooms: List[Chatroom] = self.speakeasy.get_rooms(active=True)
            for room in rooms:
                if not room.initiated:
                    # send a welcome message if room is not initiated
                    room.post_messages(
                        f"Hello! This is a welcome message from {room.my_alias}."
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
                    query = message.message.strip()

                    if self.is_sparql(query):
                        try:
                            sparql = SPARQLWrapper("INSERT SPARQL ENDPOINT")
                            sparql.setQuery(query)
                            sparql.setReturnFormat(JSON)
                            results = sparql.query().convert()

                            room.post_messages({results})
                        except Exception as e:
                            room.post_messages(f"Error executing query: {str(e)}")
                    else:
                        room.post_messages("Hi! Please enter a valid SPARQL query.")

                    # Send a message to the corresponding chat room using the post_messages method of the room object.
                    room.post_messages(f"Received your message!  ")
                    # Mark the message as processed, so it will be filtered out when retrieving new messages.

                    respond = self.sparql_query(message.message)

                    room.post_messages(f"Query answer: '{respond}' ")

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

                    room.post_messages(f"Received your reaction: '{reaction.type}' ")
                    room.mark_as_processed(reaction)

            time.sleep(listen_freq)

    @staticmethod
    def get_time():
        return time.strftime("%H:%M:%S, %d-%m-%Y", time.localtime())


if __name__ == "__main__":
    demo_bot = Agent("kindle-pizzicato-wheat_bot", "zJD7llj0A010Zg")
    demo_bot.listen()


"""
COMMENT: I think for SPARQL endpoint, the data has to be on a server or have to setup endpoints. We probably have to locally query with rdflib ?
In that case:

pip install rdflib

import rdflib

graph = rdflib.Graph()

graph = rdflib.Graph()
graph.parse('./14_graph.nt', format='turtle')   # is this the correct one?

def execute_query(query):
    try:
        results = graph.query(query)
        # Format
        result_list = [row for row in results]
        return result_list
    except Exception as e:
        return str(e)
"""
