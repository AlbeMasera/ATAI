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
from typing import Optional


# Get the absolute path to the current directory
current_directory = os.path.dirname(os.path.abspath(__file__))

# Define the relative path to the "data" folder
data_folder = os.path.join(current_directory, "data")

# Use absolute paths for loading files from the "data" folder
PREDICATE_DESC = os.path.join(data_folder, "predicates_extended.csv")
PRED_EMBEDDINGS = os.path.join(data_folder, "embeddings2.npy")
REPLACE_PREDICATES_FILE = os.path.join(data_folder, "replace_predicates_ner.csv")


class PossiblePredicate:
    def __init__(
        self, label: str, score: float, predicate: rdflib.term.URIRef, query: str
    ):
        self.label: str = label
        self.score: float = score
        self.predicate: rdflib.term.URIRef = predicate
        self.fixed_query: str = query


class EmbeddingRecognizer:
    def __init__(
        self,
        pred_df_path: str = PREDICATE_DESC,
        pred_embeddings_path: str = PRED_EMBEDDINGS,
        replace_predicates_path: str = REPLACE_PREDICATES_FILE,
    ):
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.stammer = PorterStemmer()

        np_arr = numpy.load(pred_embeddings_path)
        self.pred_embeddings = torch.from_numpy(np_arr).to("cpu")
        self.pred_df = pd.read_csv(pred_df_path)

        self.replace_predicates_df = pd.read_csv(replace_predicates_path)

    @staticmethod
    def __max_len_everygrams(arr: list) -> int:
        return min(5, len(arr))

    def __fix_query(
        self,
        query: str,
        org_label: str,
        org_string_found: str,
        embedding_found: torch.Tensor,
    ) -> str:
        if org_label in query:
            return query

        # Tokenize and generate everygrams from the original string
        words = [
            " ".join(tup)
            for tup in everygrams(
                word_tokenize(org_string_found),
                max_len=len(word_tokenize(org_string_found)),
            )
        ]

        # Encode everygram embeddings
        found_str_embedding = self.model.encode(
            words, convert_to_tensor=True, device="cpu"
        )
        hits = util.semantic_search(embedding_found, found_str_embedding, top_k=1)
        h = hits[0][0]

        # Replace the found pattern in the query with org_label
        pattern = re.escape(words[h["corpus_id"]])
        query = re.sub(
            rf"{pattern}(.*?)[\s,.?!-]", org_label + " ", query, flags=re.DOTALL
        )

        return query

    def __replace_pred(self, query: str, label: str, org_string: str) -> str:
        r_df = self.replace_predicates_df[self.replace_predicates_df["label"] == label]
        if not r_df.empty:
            query = query.replace(org_string, r_df["fixed"].values[0])
        return query

    def __generate_everygrams(self, query: str, stemming: bool) -> list:
        split = word_tokenize(query)
        words = [
            " ".join(tup)
            for tup in everygrams(split, max_len=self.__max_len_everygrams(split))
        ]

        if stemming:
            stemmed_words = [self.stammer.stem(w) for w in split]
            words.extend(
                [
                    " ".join(tup)
                    for tup in everygrams(
                        stemmed_words, max_len=self.__max_len_everygrams(stemmed_words)
                    )
                ]
            )

        words.sort(key=len, reverse=True)
        return words

    def get_predicates(
        self, query: str, stemming: bool = True
    ) -> Optional[PossiblePredicate]:
        original_query = query
        query = utils.remove_sent_endings(query)

        words = self.__generate_everygrams(query, stemming)
        query_embeddings = self.model.encode(
            words, convert_to_tensor=True, device="cpu"
        )

        for i, query_embed in enumerate(query_embeddings):
            hits = util.semantic_search(query_embed, self.pred_embeddings, top_k=1)
            hits = hits[0]

            if hits[0]["score"] >= 0.75:
                index = hits[0]["corpus_id"]
                org_label = self.pred_df["org_label"][index]
                string_found = self.pred_df["label"][index]

                original_query = self.__fix_query(
                    original_query, org_label, words[i], self.pred_embeddings[index]
                )
                original_query = self.__replace_pred(
                    original_query, org_label, string_found
                )

                return PossiblePredicate(
                    org_label,
                    hits[0]["score"],
                    rdflib.term.URIRef(self.pred_df["predicate"][index]),
                    original_query,
                )

        return None
