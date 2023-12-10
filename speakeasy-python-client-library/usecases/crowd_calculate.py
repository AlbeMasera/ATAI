
import pandas as pd

df = pd.read_csv('speakeasy-python-client-library/usecases/data/filtered_crowd_data.tsv', sep='\t')

# 1. Aggregating crowd answers
def get_correct_incorrect_counts(df):
    result = {}
    for hit_id in df["HITId"].unique():
        row = df[df["HITId"] == hit_id]
        correct_count = row[row["AnswerLabel"] == "CORRECT"].shape[0]
        incorrect_count = row[row["AnswerLabel"] == "INCORRECT"].shape[0]
        batch_id = row["HITTypeId"].iloc[0]
        result[hit_id] = {"HITTypeId": batch_id, "Correct": correct_count, "Incorrect": incorrect_count}
    return pd.DataFrame.from_dict(result, orient='index')

df_correct_incorrect = get_correct_incorrect_counts(df)

print("\nCorrect and Incorrect Counts by Batch: ")
grouped_data = df_correct_incorrect.groupby('HITTypeId').sum()
print(grouped_data)

# 2. Computing Fleiss Kappa
def calculate_fleiss_kappa(batch_df):
    happyCNT = batch_df["Correct"].sum()
    unhappyCNT = batch_df["Incorrect"].sum()
    totalCNT = happyCNT + unhappyCNT
    hit_cnt = len(batch_df)

    Pe = (happyCNT / totalCNT) ** 2 + (unhappyCNT / totalCNT) ** 2
    Po = 0

    for _, row in batch_df.iterrows():
        c = row["Correct"]
        ic = row["Incorrect"]
        worker_cnt = c + ic

        if worker_cnt - 1 == 0:
            continue

        Po += (c ** 2 + ic ** 2 - worker_cnt) / (worker_cnt * (worker_cnt - 1))

    Po /= hit_cnt
    kappa = (Po - Pe) / (1 - Pe)
    return kappa


# Compute Fleiss Kappa for each batch
kappa_scores = df_correct_incorrect.groupby("HITTypeId").apply(calculate_fleiss_kappa)
print(f"\nFleiss' Kappa Scores by Batch: {kappa_scores}")
