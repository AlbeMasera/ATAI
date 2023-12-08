import pandas as pd
import numpy as np

src = "speakeasy-python-client-library/usecases/data/crowd_data.tsv"
df = pd.read_csv(src, sep="\t")

# Function to check if a worker always gives the same response
def has_constant_response(group, column):
    return len(group[column].unique()) == 1

# Function to check if a worker always responds in the same duration
def has_constant_time(group):
    return group['WorkTimeInSeconds'].nunique() <= 2  # Allowing a variance of ±1 second

# Function to check for outlier answers
def is_outlier_worker(group, global_mode):
    if len(group) < 3:  # Skip checking for outliers if too few responses
        return False
    worker_mode = group['AnswerLabel'].mode().iloc[0]
    return worker_mode != global_mode

# Group by WorkerId
grouped = df.groupby('WorkerId')

# Find global mode for AnswerLabel
global_mode = df['AnswerLabel'].mode().iloc[0]

# Identify workers to filter out
workers_to_filter = set()
for name, group in grouped:
    if has_constant_response(group, 'AnswerLabel') or has_constant_response(group, 'FixPosition') or has_constant_response(group, 'FixValue'):
        workers_to_filter.add(name)
    elif has_constant_time(group):
        workers_to_filter.add(name)
    elif group['WorkTimeInSeconds'].lt(5).all():
        workers_to_filter.add(name)
    elif (group['LifetimeApprovalRate'].str.rstrip('%').astype(float) < 70).all():
        if is_outlier_worker(group, global_mode):
            workers_to_filter.add(name)
    elif group['FixPosition'].eq("I don't understand").all() or group['FixValue'].eq("I don't understand").all():
        workers_to_filter.add(name)

# Filter out the identified workers
df_filtered_out = df[df['WorkerId'].isin(workers_to_filter)]
df_cleaned = df[~df['WorkerId'].isin(workers_to_filter)]

# Save the cleaned and removed dataframes
df_cleaned.to_csv('speakeasy-python-client-library/usecases/data/filtered_crowd_data.tsv', sep='\t', index=False)
df_filtered_out.to_csv('speakeasy-python-client-library/usecases/data/removed_crowd_data.tsv', sep='\t', index=False)
