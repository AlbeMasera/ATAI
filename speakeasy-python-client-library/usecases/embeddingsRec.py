import os
import re
import utils
import torch
from sentence_transformers import SentenceTransformer, util
import numpy
import pandas as pd
import rdflib
from nltk.util import everygrams
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize


THRESHOLD = 0.75
EVERYGRAM_LEN = 5

# Get the absolute path to the current directory
current_directory = os.path.dirname(os.path.abspath(__file__))

# Define the relative path to the "data" folder
data_folder = os.path.join(current_directory, "data")

# Use absolute paths for loading files from the "data" folder
PREDICATE_DESC = os.path.join(data_folder, "predicates_extended.csv")
PRED_EMBEDDINGS = os.path.join(data_folder, "embeddings2.npy")

CROWD_ENTITIES_DESC = os.path.join(data_folder, "entities_crowd.csv")

CROWD_ENTITIES_EMBEDDINGS = os.path.join(data_folder, "entities_crowd_emb.npy")

REPLACE_PREDICATES_FILE = os.path.join(data_folder, "replace_predicates_ner.csv")


class PossiblePredicate:
    def __init__(
        self, label: str, score: float, predicate: rdflib.term.URIRef, query: str
    ):
        self.label: str = label
        self.score: float = score
        self.predicate: rdflib.term.URIRef = predicate
        self.fixed_query: str = query

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"PredicateEmbedding(label={self.label}, score={self.score}, predicate={self.predicate}, query={self.fixed_query})"


class CrowdEntity:
    def __init__(
        self, label: str, score: float, predicate: rdflib.term.URIRef, query: str
    ):
        self.label: str = label
        self.score: float = score
        self.node: rdflib.term.URIRef = predicate
        self.fixed_query: str = query

    def __str__(self):
        return f"PredicateEmbedding(label={self.label}, score={self.score}, predicate={self.node}, query={self.fixed_query})"


class EmbeddingRecogniser:
    def __init__(
        self,
        pred_df_path: str = PREDICATE_DESC,
        pred_embeddings_path: str = PRED_EMBEDDINGS,
        crowd_df_path: str = CROWD_ENTITIES_DESC,
        crowd_embeddings_path: str = CROWD_ENTITIES_EMBEDDINGS,
        replace_predicates_path: str = REPLACE_PREDICATES_FILE,
    ):
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.stammer = PorterStemmer()

        np_arr = numpy.load(pred_embeddings_path)
        self.pred_embeddings = torch.from_numpy(np_arr).to("cpu")
        self.pred_df = pd.read_csv(pred_df_path)

        np_arr = numpy.load(crowd_embeddings_path)
        self.crowd_embeddings = torch.from_numpy(np_arr).to("cpu")
        self.crowd_df = pd.read_csv(crowd_df_path)

        self.replace_predicates_df = pd.read_csv(replace_predicates_path)

        assert len(self.pred_df) > 0, "PredicateEmbedding: No predicates found"
        assert len(self.pred_df) == len(
            self.pred_embeddings
        ), "Embeddings and predicates must have the same length"

        assert len(self.crowd_embeddings) > 0, "crowd_embeddings: No entities found"
        assert len(self.crowd_df) == len(
            self.crowd_embeddings
        ), "Embeddings and DF must have the same length"

        assert (
            len(self.replace_predicates_df) > 0
        ), "replace_predicates_df: No predicates found"

    @staticmethod
    def __max_len_everygrams(arr):
        if len(arr) > EVERYGRAM_LEN:
            return EVERYGRAM_LEN
        return len(arr)

    def __fix_query(self, query, org_label, org_string_found, embedding_found):
        if org_label in query:
            return query

        words = word_tokenize(org_string_found)
        words = [" ".join(tup) for tup in everygrams(words, max_len=len(words))]

        found_str_embedding = self.model.encode(
            words, convert_to_tensor=True, device="cuda"
        )
        hits = util.semantic_search(embedding_found, found_str_embedding, top_k=1)
        h = hits[0][0]
        print(h)

        return re.sub(
            f'{words[h["corpus_id"]]}?(.*?)[\s,.?!-]',
            org_label + " ",
            query,
            flags=re.DOTALL,
        )

    def __replace_pred(self, query: str, label: str, org_string: str) -> str:
        r_df = self.replace_predicates_df[self.replace_predicates_df["label"] == label]
        if r_df.empty:
            return query
        else:
            return query.replace(org_string, r_df["fixed"].values[0])

    def get_predicates(self, query, stemming=True) -> PossiblePredicate | None:
        original_query = query
        query = utils.remove_sent_endings(query)

        split = word_tokenize(query)
        words = [
            " ".join(tup)
            for tup in everygrams(split, max_len=self.__max_len_everygrams(split))
        ]

        split2 = []
        if stemming:
            print("[.] Embedding: will try stemming")
            split2 = [self.stammer.stem(w) for w in split]
            words2 = [
                " ".join(tup)
                for tup in everygrams(split2, max_len=self.__max_len_everygrams(split2))
            ]
            words.extend(words2)

        words.sort(key=len, reverse=True)

        print("[.] PredicateEmbedding: will embed:", words)
        query_embeddings = self.model.encode(
            words, convert_to_tensor=True, device="cpu"
        )
        for i, query_embed in enumerate(query_embeddings):
            hits = util.semantic_search(query_embed, self.pred_embeddings, top_k=1)
            hits = hits[0]  # Get the hits for the first query
            for hit in hits:
                index = hit["corpus_id"]
                # print("---Closest: ", index, hits[0]['score'])

                if THRESHOLD < hits[0]["score"]:
                    org_label = self.pred_df["org_label"][index]
                    string_found = self.pred_df["label"][index]
                    print(
                        f"[+] PredicateEmbedding: Found a match: {org_label} / {string_found}"
                    )

                    original_query = self.__fix_query(
                        original_query, org_label, words[i], self.pred_embeddings[index]
                    )

                    original_query = self.__replace_pred(
                        original_query, org_label, string_found
                    )
                    return PossiblePredicate(
                        org_label,
                        hit["score"],
                        rdflib.term.URIRef(self.pred_df["predicate"][index]),
                        original_query,
                    )

        print("[X] PredicateEmbedding: No match found")
        return

    def get_crowd_entity(self, query) -> CrowdEntity | None:
        split = utils.remove_sent_endings(query).split(" ")

        words = [
            " ".join(tup)
            for tup in everygrams(split, max_len=self.__max_len_everygrams(split))
        ]
        words.sort(key=len, reverse=True)

        print("[.] CROWD Embedding: will embed:", words)
        query_embeddings = self.model.encode(
            words, convert_to_tensor=True, device="cpu"
        )
        for i, query_embed in enumerate(query_embeddings):
            hits = util.semantic_search(query_embed, self.crowd_embeddings, top_k=1)
            hits = hits[0]  # Get the hits for the first query
            for hit in hits:
                index = hit["corpus_id"]

                if 0.9 < hits[0]["score"]:
                    label = self.crowd_df["label"][index]
                    print(f"[+] CROWD: Found a match: {label}")
                    # print(words[i:i + label.count(" ")])
                    query = query.replace(
                        " ".join(words[i : i + label.count(" ")]), label
                    )
                    return CrowdEntity(
                        label, hit["score"], self.crowd_df["entity"][index], query
                    )

        print("[X] CROWD: No match found")
        return
