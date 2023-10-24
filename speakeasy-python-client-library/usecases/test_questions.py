import graphlib
import pickle
from rdflib import Graph
import spacy
from nltk.corpus import wordnet as wn

# Load SpaCy English NLP model
nlp = spacy.load("en_core_web_sm")

# Parse the natural language query

nlp = spacy.load("en_core_web_sm")

query = "Who is Aldo Moro?"


def nounify(verb_word):
    set_of_related_nouns = []

    for lemma in wn.lemmas(wn.morphy(verb_word, wn.VERB), pos="v"):
        for related_form in lemma.derivationally_related_forms():
            for synset in wn.synsets(related_form.name(), pos=wn.NOUN):
                if wn.synset("person.n.01") in synset.closure(lambda s: s.hypernyms()):
                    set_of_related_nouns.append(synset)

    return set_of_related_nouns[0].name().split(".")[0]


def info(query):
    doc = nlp(query)

    for word in doc.ents:
        print(word.text, word.label_)
    # Initialize variables to store the subject, predicate, and object
    subject = ""
    predicate = ""
    obj = ""

    # Iterate through the words in the sentence to find the subject, predicate, and object
    for token in doc:
        # If the word is the main verb, it is the predicate
        if "ROOT" in token.dep_:
            predicate = token.text

        # If the word is a subject, it is the subject
        if "subj" in token.dep_ or "nsubj" in token.dep_:
            subject = token.text

        # If the word is an object, it is the object
        if "obj" in token.dep_ or token.ent_type_:
            obj = obj + " " + token.text

    if subject == "Who":
        subject = nounify(predicate)

    # Print the extracted subject, predicate, and object
    return subject, predicate, obj


def sparql_query(query):
    # clean input
    query = query.replace("'''", "\n")
    query = query.replace("‘’’", "\n")
    query = query.replace("PREFIX", "\nPREFIX")

    try:
        result = graphlib.query(query)
        # Handle different conditions
        processed_result = []
        for item in result:
            processed_result.append(item[0])
        result = processed_result
    except Exception as e:
        result = f"Error: {str(e)}"

    return result


doc = nlp(query)

for ent in doc.ents:
    print(f"{ent.label_} : {ent.text}")


'''
subject, predicate, obj = info(query)
print(subject, predicate, obj)
# Construct the SPARQL query
msg = f"""
PREFIX ddis: <http://ddis.ch/atai/>   

PREFIX wd: <http://www.wikidata.org/entity/>   

PREFIX wdt: <http://www.wikidata.org/prop/direct/>   

PREFIX schema: <http://schema.org/>   

SELECT ?x WHERE {{

     ?z rdfs:label "{obj.strip()}"@en .  

    ?z wdt:P57 ?y . 

    ?y rdfs:label ?x .  

}}

LIMIT 1
"""

print(msg)


# define an empty knowledge graph
graph = Graph()


# load a knowledge graph
# open the file where we stored the pickled data
file = open("important", "rb")

# dump information to that file
graph = pickle.load(file)

print(sparql_query(msg))
'''
