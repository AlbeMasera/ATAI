import pandas as pd
import rdflib
from sentence_transformers import SentenceTransformer
import numpy as np
from graph import Graph

src = "speakeasy-python-client-library/usecases/data/filtered_crowd_data.tsv"
output_csv = "speakeasy-python-client-library/usecases/data/entities_crowd.csv"
output_npy = "speakeasy-python-client-library/usecases/data/entities_crowd_emb.npy"

df = pd.read_csv(src, sep="\t")


# Extract entities
def extract_entities(df, graph):
    l = []
    WD = rdflib.Namespace("http://www.wikidata.org/entity/")
    WDT = rdflib.Namespace("http://www.wikidata.org/prop/direct/")
    DDIS = rdflib.Namespace("http://ddis.ch/atai/")

    for task_id in df["HITId"].unique():
        task_df = df[df["HITId"] == task_id]
        task_g = task_df.groupby(by="HITId").first()
        ent = f'{WD}{task_g["Input1ID"].values[0].strip("wd:")}'
        sub = rdflib.term.URIRef(ent)
        sub_lbl = graph.entity_to_label(sub)
        l.append([sub_lbl, sub])

        val = task_g["Input2ID"].values[0]
        pred_lbl = ""
        if "wdt" in val:
            pred = f'{WDT}{val.strip("wdt:")}'
            pred_g = rdflib.term.URIRef(pred)
            pred_lbl = graph.entity_to_label(pred_g)
        elif "ddis" in val:
            pred = f'{DDIS}{val.replace("ddis:", "")}'
            pred_g = rdflib.term.URIRef(pred)
            pred_lbl = val.replace("ddis:", "")
        l.append([pred_lbl, pred])

    return pd.DataFrame(l, columns=["label", "entity"]).drop_duplicates()


# Generate embeddings
def generate_embeddings(df):
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    sentences = df["label"].tolist()
    embeddings = model.encode(sentences)
    return embeddings


if __name__ == "__main__":
    src = "speakeasy-python-client-library/usecases/data/filtered_crowd_data.tsv"
    df = pd.read_csv(src, sep="\t")

    graph_pickle_path = (
        "speakeasy-python-client-library/usecases/data/pickle_graph.pickel"
    )
    graph = Graph(graph_pickle_path)

    # Extract entities
    ent_emb_df = extract_entities(df, graph)
    ent_emb_df.to_csv("entities_crowd.csv", index=False)

    # Generate embeddings
    embeddings = generate_embeddings(ent_emb_df)
    np.save("entities_crowd_emb.npy", embeddings)

    print("Embeddings generated and saved.")
