import io
import os

import pandas as pd
from pymongoClient import client
import qiime2
from qiime2.plugins import taxa, feature_table
import biom


CURRENT_STAGE = "Freq_To_Biom"


def new_headers(df, metadata):
    result = [('#Diagnosis', '#OTU id')]
    current = df.columns
    for i in current[1:]:
        result.append((metadata[i], i))
    return result

if __name__ == '__main__':
    db = client.dbClient()
    outputs = db.default_output_names(CURRENT_STAGE)

    output_dir_data = os.getenv("OUTPUT_DIR")

    out_table_tsv = os.path.join(output_dir_data, outputs["data"][0])

    if not os.path.exists(output_dir_data):
        os.makedirs(output_dir_data)

    experiment_id = os.getenv("EXP_ID")
    parent_name = os.getenv("PARENT")

    if db.check_doc_exists({"_id": experiment_id}, "experiment"):
        print("Sorry that experiment_id already exists, please use a new experiment ID")
    else:
        parent = db.stage_parent_correct(CURRENT_STAGE, parent_name)
        if parent is not None:
            taxa_table = qiime2.Artifact.load(parent["output"]["data"][0])

            print(taxa_table)

            otu_freq = feature_table.methods.relative_frequency(taxa_table)

            biom_table = otu_freq.relative_frequency_table.view(biom.Table)
            df = pd.read_csv(io.StringIO(biom_table.to_tsv()), sep='\t', header=1)
            samples = df.columns.values.tolist()[1:]

            meta_data = {}
            for id in samples:
                metadata_id = db.get_one_selective({"run_accession": id}, {"sample_alias": 1, "_id": 0}, "samples")[
                    "sample_alias"]
                condition = db.get_one_selective({"sample": metadata_id}, {"dx": 1, "_id": 0}, "metadata")
                if condition is not None:
                    meta_data[id] = condition["dx"]
                else:
                    meta_data[id] = "inconclusive"

            df.columns = pd.MultiIndex.from_tuples(new_headers(df, meta_data))

            df = df.drop(' ', axis=1, level=0)

            df = df.drop('inconclusive', axis=1, level=0)

            df.to_csv(out_table_tsv, sep='\t', index=False)


            this_experiment = {
                "_id": experiment_id,
                "parent": parent_name,
                "stage": CURRENT_STAGE,
                "output": {
                    "visuals": None,
                    "data": [out_table_tsv]
                }
            }

            db.new_experiment(this_experiment)

    db.close()
