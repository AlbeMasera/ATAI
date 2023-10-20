# define an empty knowledge graph
import pickle
from rdflib import Graph


graph = Graph()
# load a knowledge graph
graph.parse(source="speakeasy-python-client-library/graph/14_graph.nt", format="turtle")

# open a file, where you ant to store the data
file = open("important", "wb")

# dump information to that file
pickle.dump(graph, file)

# close the file
file.close()
