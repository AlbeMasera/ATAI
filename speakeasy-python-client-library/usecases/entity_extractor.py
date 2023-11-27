import os
import rdflib
import csv
import numpy as np
from graph import Graph


current_directory = os.path.dirname(os.path.abspath(__file__))

GRAPH_PICKLE = os.path.join(current_directory, "data/pickle_graph.pickel")

# Load relation IDs from file
with open(os.path.join(current_directory, "data/relation_ids.del"), "r") as ifile:
    rel2id = {
        rdflib.term.URIRef(rel): int(idx)
        for idx, rel in csv.reader(ifile, delimiter="\t")
    }
    id2rel = {v: k for k, v in rel2id.items()}

# Create a Graph object
graph = Graph(GRAPH_PICKLE)

# Create a dictionary mapping entities to labels
ent2lbl = {
    ent: str(lbl) for ent, lbl in graph.g.subject_objects(rdflib.namespace.RDFS.label)
}

# Load relation embeddings
relation_emb = np.load(os.path.join(current_directory, "data/relation_embeds.npy"))

# Initialize relationLabels dictionary
relationLabels = {}

# Iterate over id2rel items
for k, v in id2rel.items():
    label = ent2lbl.get(v)
    if label and np.all(relation_emb[k]):
        relationLabels[label] = k

# Print the resulting relationLabels dictionary
print(relationLabels)
