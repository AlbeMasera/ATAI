import os
import pandas as pd
from nltk.stem import PorterStemmer
from nltk.stem.snowball import SnowballStemmer
import editdistance
from nltk.corpus import wordnet as wn
from nltk.tokenize import word_tokenize


def read_original_predicates(input_file):
    return pd.read_csv(input_file, sep=",")


def stem_with_porter(label, ps):
    words = word_tokenize(label)
    stemmed = " ".join([ps.stem(word) for word in words])
    return stemmed


def create_synonyms(stemmed_word, snowball_stemmer):
    synonyms = set()
    synsets = wn.synsets(stemmed_word)
    for synset in synsets:
        lemmas = synset.lemmas()
        for lemma in lemmas:
            derived_forms = lemma.derivationally_related_forms()
            for form in derived_forms:
                name = form.name()
                stemmed = snowball_stemmer.stem(name)
                if editdistance.distance(stemmed, stemmed_word) < 3:
                    synonyms.add(stemmed)
    return synonyms


def process_predicates(input_file, output_file):
    df = read_original_predicates(input_file)
    df["org_label"] = df["label"]

    # Stemming using Porter Stemmer
    ps = PorterStemmer()
    stemmed_rows = []
    for _, row in df.iterrows():
        stemmed_label = stem_with_porter(row["label"], ps)
        cp = row.copy(deep=True)
        cp["label"] = stemmed_label
        stemmed_rows.append(cp)

    stemmed_df = pd.DataFrame(stemmed_rows, columns=df.columns)

    # Snowball Stemmer and Synonym Generation
    snowball_stemmer = SnowballStemmer(language="english")

    # Generate variations and synonyms
    processed_rows = []
    for _, row in df.iterrows():
        stemmed_words = [ps.stem(word) for word in word_tokenize(row["label"])]
        cp = row.copy(deep=True)
        cp["label"] = " ".join(stemmed_words)
        processed_rows.append(cp)

        for w in stemmed_words + word_tokenize(row["label"]):
            synonyms = create_synonyms(w, snowball_stemmer)
            for y in synonyms:
                n = row["label"].replace(w, y)
                print(f"{row['label']} -> {n}")

                cp = row.copy(deep=True)
                cp["label"] = n
                processed_rows.append(cp)

    # Create DataFrames for stemmed, original, and word variations
    stemmed_df = pd.DataFrame(stemmed_rows, columns=df.columns).drop_duplicates()
    original_df = df.drop_duplicates()
    words_df = pd.DataFrame(processed_rows, columns=df.columns).drop_duplicates()

    # Concatenate and sort the DataFrames, drop duplicates and save the result to predicates_extended.csv
    all_df = pd.concat([stemmed_df, original_df, words_df])
    all_df = all_df.sort_values(by="label").drop_duplicates()
    all_df.to_csv(output_file, ",", index=False)


if __name__ == "__main__":
    input_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "predicates_original.csv"
    )
    output_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "predicates_extended.csv"
    )
    process_predicates(input_file, output_file)
