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


DEFAULT_HOST_URL = "https://speakeasy.ifi.uzh.ch"
listen_freq = 2

script_dir = os.path.dirname(os.path.abspath(__file__))

base_dir = os.path.dirname(script_dir)

# construct path to graph and embeddings
graph_path = os.path.join(base_dir, 'graph', '14_graph_nt')

entity_emb_path = os.path.join(base_dir, 'embeddings', 'entity_embeds.npy')
relation_emb_path = os.path.join(base_dir, 'embeddings', 'relation_embeds.npy')

entity_ids_path = os.path.join(base_dir, 'embeddings', 'entity_ids.del')
relation_ids_path = os.path.join(base_dir, 'embeddings', 'relation_ids.del')

# define an empty knowledge graph
graph = Graph()

# Load the graph
# graph = rdflib.Graph().parse('14_graph.nt', format='turtle')

# load a knowledge graph
# open the file where we stored the pickled data
file = open("important", "rb")
# dump information to that file
graph = pickle.load(file)
# close the file
file.close()


LATIN_1_CHARS = (
    ("\\\\xe2\\\\x80\\\\x99", "'"),
    ("\\\\xc3\\\\xa9", "e"),
    ("\\\\xe2\\\\x80\\\\x90", "-"),
    ("\\\\xe2\\\\x80\\\\x91", "-"),
    ("\\\\xe2\\\\x80\\\\x92", "-"),
    ("\\\\xe2\\\\x80\\\\x93", "-"),
    ("\\\\xe2\\\\x80\\\\x94", "-"),
    ("\\\\xe2\\\\x80\\\\x94", "-"),
    ("\\\\xe2\\\\x80\\\\x98", "'"),
    ("\\\\xe2\\\\x80\\\\x9b", "'"),
    ("\\\\xe2\\\\x80\\\\x9c", '"'),
    ("\\\\xe2\\\\x80\\\\x9c", '"'),
    ("\\\\xe2\\\\x80\\\\x9d", '"'),
    ("\\\\xe2\\\\x80\\\\x9e", '"'),
    ("\\\\xe2\\\\x80\\\\x9f", '"'),
    ("\\\\xe2\\\\x80\\\\xa6", "..."),
    ("\\\\xe2\\\\x80\\\\xb2", "'"),
    ("\\\\xe2\\\\x80\\\\xb3", "'"),
    ("\\\\xe2\\\\x80\\\\xb4", "'"),
    ("\\\\xe2\\\\x80\\\\xb5", "'"),
    ("\\\\xe2\\\\x80\\\\xb6", "'"),
    ("\\\\xe2\\\\x80\\\\xb7", "'"),
    ("\\\\xe2\\\\x81\\\\xba", "+"),
    ("\\\\xe2\\\\x81\\\\xbb", "-"),
    ("\\\\xe2\\\\x81\\\\xbc", "="),
    ("\\\\xe2\\\\x81\\\\xbd", "("),
    ("\\\\xe2\\\\x81\\\\xbe", ")"),
)

class KnowledgeGraphRetriever:
    def __init__(self, graph_path, entity_emb_path, relation_emb_path, entity_ids_path, relation_ids_path):
        # Load the graph
        self.graph = Graph().parse(graph_path, format='turtle')
        
        # Load embeddings
        self.entity_emb = np.load(entity_emb_path)
        self.relation_emb = np.load(relation_emb_path)
        
        # Load dictionaries
        with open(entity_ids_path, 'r') as ifile:
            self.ent2id = {rdflib.term.URIRef(ent): int(idx) for idx, ent in csv.reader(ifile, delimiter='\t')}
            sself.id2ent = {v: k for k, v in self.ent2id.items()}
        with open(relation_ids_path, 'r') as ifile:
            self.rel2id = {rdflib.term.URIRef(rel): int(idx) for idx, rel in csv.reader(ifile, delimiter='\t')}
            self.id2rel = {v: k for k, v in self.rel2id.items()}
        
        self.ent2lbl = {ent: str(lbl) for ent, lbl in self.graph.subject_objects(rdflib.namespace.RDFS.label)}
        self.lbl2ent = {lbl: ent for ent, lbl in self.ent2lbl.items()}

        ent2lbl = {ent: str(lbl) for ent, lbl in graph.subject_objects(RDFS.label)}
        lbl2ent = {lbl: ent for ent, lbl in ent2lbl.items()}

        # Initialize NER pipeline
        self.ner_pipeline = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english")
        
        # Initialize SpaCy model
        self.nlp = spacy.load("en_core_web_sm")

    def find_similar_entities(self, entity_id, top_n=10):
        # Compute distance to all other entity embeddings
        dist = pairwise_distances(self.entity_emb[entity_id].reshape(1, -1), self.entity_emb).reshape(-1)
        # Order by similarity
        most_likely = dist.argsort()
        # Return top_n most similar entities
        return [(self.id2ent[idx], self.ent2lbl[self.id2ent[idx]], dist[idx]) for idx in most_likely[:top_n]]

    def predict_object(self, subject_id, predicate_id):
        # Combine subject and predicate embeddings according to the TransE scoring function
        lhs = self.entity_emb[subject_id] + self.relation_emb[predicate_id]
        # Compute distance to all other entity embeddings
        dist = pairwise_distances(lhs.reshape(1, -1), self.entity_emb).reshape(-1)
        # Find the most plausible object
        most_likely_object_id = dist.argsort()[0]
        return self.id2ent[most_likely_object_id]

    def handle_query(self, query):
        # Use NER to extract entities from the query
        entities = self.ner_pipeline(query, aggregation_strategy="simple")
        
        # Use SpaCy to parse the query and extract subject, predicate, and object
        doc = self.nlp(query)
        subject, predicate, obj = "", "", ""
        for token in doc:
            if "ROOT" in token.dep_:
                predicate = token.text
            if "subj" in token.dep_ or "nsubj" in token.dep_:
                subject = token.text
            if "obj" in token.dep_ or token.ent_type_:
                obj += " " + token.text
        
        # Use the extracted subject and predicate to predict the object using embeddings
        if subject in self.lbl2ent and predicate in self.rel2id:
            predicted_object = self.predict_object(self.ent2id[self.lbl2ent[subject]], self.rel2id[predicate])
            return predicted_object
        else:
            return "Could not handle the query."

class Agent:
    def __init__(self, username, password):
        # Initialize the KnowledgeGraphRetriever
        self.kg_retriever = KnowledgeGraphRetriever(graph_path, entity_emb_path, relation_emb_path, entity_ids_path, relation_ids_path)

        self.username = username
        # Initialize the Speakeasy Python framework and login.
        self.speakeasy = Speakeasy(
            host=DEFAULT_HOST_URL, username=username, password=password
        )

    def extract_entities(self, query):
        # Extract entities from the input query using NER
        entities = ner_pipeline(query=query, aggregation_strategy="simple")

        for entity in entities:
            print(f"{entity['word']}: {entity['entity_group']} ({entity['score']:.2f})")

        return entities

    def nounify(self, verb_word):
        """Convert verb to its closest noun form using WordNet."""
        set_of_related_nouns = []
        for lemma in wn.lemmas(wn.morphy(verb_word, wn.VERB), pos="v"):
            for related_form in lemma.derivationally_related_forms():
                for synset in wn.synsets(related_form.name(), pos=wn.NOUN):
                    if wn.synset("person.n.01") in synset.closure(lambda s: s.hypernyms()):
                        set_of_related_nouns.append(synset)
        return set_of_related_nouns[0].name().split(".")[0] if set_of_related_nouns else verb_word
    
    def parse_query(self, query):
        """Parse the user's query using SpaCy and extract subject, predicate, and object."""
        doc = self.nlp(query)
        subject = ""
        predicate = ""
        obj = ""
        for token in doc:
            if "ROOT" in token.dep_:
                predicate = token.text
            if "subj" in token.dep_ or "nsubj" in token.dep_:
                subject = token.text
            if "obj" in token.dep_ or token.ent_type_:
                obj = obj + " " + token.text
        if subject == "Who":
            subject = self.nounify(predicate)
        return subject, predicate, obj.strip()

    def construct_sparql_query(self, subject, predicate, obj):
        # Construct a SPARQL query based on the extracted subject, predicate, and object."""
        query_template = f"""
        PREFIX ddis: <http://ddis.ch/atai/>   
        PREFIX wd: <http://www.wikidata.org/entity/>   
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>   
        PREFIX schema: <http://schema.org/>   
        SELECT ?x WHERE {{
            ?z rdfs:label "{obj}"@en .  
            ?z wdt:P57 ?y . 
            ?y rdfs:label ?x .  
        }}
        LIMIT 1
        """
        return query_template

    def handle_utf8(self, query):
        temp = repr(bytes(query, encoding="utf-8", errors="ignore"))[2:-1]

        for _hex, _char in LATIN_1_CHARS:
            res = temp.replace(_hex, _char)

        return res

    def handle_none(self, query):
        return self.handle_utf8("None" if query is None else str(query))

    def sparql_query(self, query):
        # clean input
        query = query.replace("'''", "\n")
        query = query.replace("‘’’", "\n")
        query = query.replace("PREFIX", "\nPREFIX")

        try:
            result = graph.query(query)
            # handle different conditions
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

    def respond_to_query(self, query):
        # Use the KnowledgeGraphRetriever to handle the query
        response = self.kg_retriever.handle_query(query)
        return response

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
                    # Extract query from message
                    query = message.message.strip()

                    # Extract entities from message
                    entities = self.extract_entities(message.message)
                    for entity in entities:
                        print(f"{entity['word']}: {entity['entity_group']} ({entity['score']:.2f})")

                    # Parse the user's query using SpaCy
                    subject, predicate, obj = self.parse_query(message.message)
                    print(f"Subject: {subject}, Predicate: {predicate}, Object: {obj}")

                    # Construct the SPARQL query
                    sparql_query = self.construct_sparql_query(subject, predicate, obj)
                    print(sparql_query)

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
