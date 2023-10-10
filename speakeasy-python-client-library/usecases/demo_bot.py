from rdflib import Graph
from speakeasypy import Speakeasy, Chatroom
from typing import List
import time

import re  # Regular expressions

DEFAULT_HOST_URL = "https://speakeasy.ifi.uzh.ch"
listen_freq = 2


# define an empty knowledge graph
graph = Graph()
# load a knowledge graph
graph.parse(source="speakeasy-python-client-library/graph/14_graph.nt", format="turtle")

LATIN_1_CHARS = (
    ('\\\\xe2\\\\x80\\\\x99', "'"),
    ('\\\\xc3\\\\xa9', 'e'),
    ('\\\\xe2\\\\x80\\\\x90', '-'),
    ('\\\\xe2\\\\x80\\\\x91', '-'),
    ('\\\\xe2\\\\x80\\\\x92', '-'),
    ('\\\\xe2\\\\x80\\\\x93', '-'),
    ('\\\\xe2\\\\x80\\\\x94', '-'),
    ('\\\\xe2\\\\x80\\\\x94', '-'),
    ('\\\\xe2\\\\x80\\\\x98', "'"),
    ('\\\\xe2\\\\x80\\\\x9b', "'"),
    ('\\\\xe2\\\\x80\\\\x9c', '"'),
    ('\\\\xe2\\\\x80\\\\x9c', '"'),
    ('\\\\xe2\\\\x80\\\\x9d', '"'),
    ('\\\\xe2\\\\x80\\\\x9e', '"'),
    ('\\\\xe2\\\\x80\\\\x9f', '"'),
    ('\\\\xe2\\\\x80\\\\xa6', '...'),
    ('\\\\xe2\\\\x80\\\\xb2', "'"),
    ('\\\\xe2\\\\x80\\\\xb3', "'"),
    ('\\\\xe2\\\\x80\\\\xb4', "'"),
    ('\\\\xe2\\\\x80\\\\xb5', "'"),
    ('\\\\xe2\\\\x80\\\\xb6', "'"),
    ('\\\\xe2\\\\x80\\\\xb7', "'"),
    ('\\\\xe2\\\\x81\\\\xba', "+"),
    ('\\\\xe2\\\\x81\\\\xbb', "-"),
    ('\\\\xe2\\\\x81\\\\xbc', "="),
    ('\\\\xe2\\\\x81\\\\xbd', "("),
    ('\\\\xe2\\\\x81\\\\xbe', ")")
)

class Agent:
    def __init__(self, username, password):
        self.username = username
        # Initialize the Speakeasy Python framework and login.
        self.speakeasy = Speakeasy(
            host=DEFAULT_HOST_URL, username=username, password=password
        )
        self.speakeasy.login()  # This framework will help you log out automatically when the program terminates.

    def handle_utf8(self,query):
        temp = repr(bytes(query, encoding = 'utf-8', errors='ignore'))[2:-1]

        for _hex, _char in LATIN_1_CHARS:
            res = temp.replace(_hex, _char)
        
        return res

    def handle_none(self,query):
        return self.handle_utf8('None' if query is None else str(query))

    def sparql_query(self, query):
        # clean input
        query = query.replace("'''", "\n")
        query = query.replace("‘’’", "\n")
        query = query.replace("PREFIX", "\nPREFIX")

        try:
            result = graph.query(query)
            # Handle different conditions
            processed_result = []
            for item in result:
                try:
                    # Unpack as (str, int)
                    s, nc = item
                    processed_result.append((str(self.handle_none(s)), int(self.handle_none(nc))))
                except ValueError:
                    try:
                        # Unpack as (str, str)
                        s, nc = item
                        processed_result.append((str(self.handle_none(s)), str(self.handle_none(nc))))
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

                    # Send a message to the corresponding chat room using the post_messages method of the room object.
                    room.post_messages(f"Received your message!  ")
                    # Mark the message as processed, so it will be filtered out when retrieving new messages.

                    if self.is_sparql(query):
                        respond = self.sparql_query(message.message)
                        room.post_messages(f"Query answer: '{respond}' ")
                    else:
                        room.post_messages("Hi! Please enter a valid SPARQL query.")

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
