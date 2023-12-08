import pandas as pd
import rdflib

df = pd.read_csv("speakeasy-python-client-library/usecases/data/filtered_crowd_data.tsv", sep="\t")

# Setup RDF namespaces
WD = rdflib.Namespace('http://www.wikidata.org/entity/')
WDT = rdflib.Namespace('http://www.wikidata.org/prop/direct/')
DDIS = rdflib.Namespace('http://ddis.ch/atai/')
RDFS = rdflib.namespace.RDFS
SCHEMA = rdflib.Namespace('http://schema.org/')

# Initialize a list for processed data
d = []

# Process each task
for task_id in df["HITId"].unique():
    task_df = df[df["HITId"] == task_id]
    task_g = task_df.groupby(by="HITId").head(1)
    batch_id = task_g["HITTypeId"].unique()[0]

    count_correct = task_df[task_df["AnswerLabel"] == "CORRECT"].count()["HITId"]
    count_false = task_df[task_df["AnswerLabel"] == "INCORRECT"].count()["HITId"]

    ent = f'{WD}{task_g["Input1ID"].unique()[0].strip("wd:")}'
    sub = rdflib.term.URIRef(ent)

    val = task_g["Input2ID"].unique()[0]
    pred_g = None
    if "wdt" in val:
        pred = f'{WDT}{val.strip("wdt:")}'
        pred_g = rdflib.term.URIRef(pred)
    elif "ddis" in val:
        pred = f'{DDIS}{val.replace("ddis:", "")}'
        pred_g = rdflib.term.URIRef(pred)

    objt = task_df["Input3ID"].unique()[0]
    o = None
    if "wd" in objt:
        ent_obj = f'{WD}{task_g["Input3ID"].unique()[0].strip("wd:")}'
        o = rdflib.term.URIRef(ent_obj)
    else:
        o = objt

    fixes = []
    for fix_str in task_df["FixValue"].dropna().unique():
        fix = None
        if "wd" in fix_str or fix_str.startswith("Q"):
            fix_ent_obj = f'{WD}{fix_str.strip("wd:")}'
            fix = rdflib.term.URIRef(fix_ent_obj)
        elif "wdt" in fix_str or fix_str.startswith("P"):
            pred_fixed = f'{WDT}{fix_str.strip("wdt:")}'
            fix = rdflib.term.URIRef(pred_fixed)
        else:
            fix = fix_str
        fixes.append(fix)

    position = task_df["FixPosition"].dropna().unique()[0] if len(task_df["FixPosition"].dropna().unique()) > 0 else None

    d.append(
        [task_id, batch_id, sub, pred_g, o, count_correct, count_false, position, fixes[0] if len(fixes) else None])

# Create a new DataFrame
df_bot = pd.DataFrame(d, columns=["HITId", "HITTypeId", "Input1ID", "Input2ID", "Input3ID", "CORRECT", "INCORRECT",
                                  "FixPosition", "FixValue"])

# Save the processed data to a new CSV file
output_path = "speakeasy-python-client-library/usecases/data/crowd_bot.csv"
df_bot.to_csv(output_path, sep="\t", index=False)
