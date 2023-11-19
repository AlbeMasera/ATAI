import os
import rdflib
import csv
import numpy as np
from graph import Graph


current_directory = os.path.dirname(os.path.abspath(__file__))


GRAPH_PICKLE = os.path.join(current_directory, "pickle_graph.pickel")
WD = rdflib.Namespace("http://www.wikidata.org/entity/")
WDT = rdflib.Namespace("http://www.wikidata.org/prop/direct/")
DDIS = rdflib.Namespace("http://ddis.ch/atai/")
RDFS = rdflib.namespace.RDFS
SCHEMA = rdflib.Namespace("http://schema.org/")


with open(os.path.join(current_directory, "relation_ids.del"), "r") as ifile:
    rel2id = {
        rdflib.term.URIRef(rel): int(idx)
        for idx, rel in csv.reader(ifile, delimiter="\t")
    }
    id2rel = {v: k for k, v in rel2id.items()}

graph = Graph(GRAPH_PICKLE)

ent2lbl = {ent: str(lbl) for ent, lbl in graph.g.subject_objects(RDFS.label)}

relation_emb: np.ndarray = np.load(
    os.path.join(current_directory, "relation_embeds.npy")
)

relationLabels = dict()
for k, v in id2rel.items():
    label = ent2lbl.get(v)
    if label:
        p = relation_emb[k]
        if p.all():
            # print(f"{v} -> {label}")
            relationLabels[label] = k
        else:
            print(f"Cannot find {v} in Embedding")
    print(f"Cannot find {v} in Subjects")

print()
print(relationLabels)
