import io
import json
import os

import pandas as pd
from pymongoClient import client
import qiime2
from qiime2.plugins import taxa, feature_table
import biom
if __name__ == '__main__':

    db = client.dbClient()

    experiment_id = os.getenv("EXP_ID")
    if db.check_doc_exists({"experiment_id":experiment_id},"experiment"):
        print("Sorry that experiment_id already exists, please use a new experiment ID")
    else:
        params = json.loads(os.getenv("PARAMS"))

        input = params["input"] # filepath or experiment name
        output_dir = params["output_dir"] # either a qza or a json experiment needed

        if os.path.exists(input):
            sequences = qiime2.Artifact.load(input)
        else:
            docs = db.get_one({"experiment_id":input},"experiment")

            if docs and docs['stage'] == "Feature_Classification":
                path = docs['output']['data']
                sequences = qiime2.Artifact.load(path+".qza")
                table_docs = db.get_one({"experiment_id":  docs['input']}, "experiment")
                if table_docs and table_docs['stage'] == "Data_QA":
                    path = table_docs['output']['data']
                    table = qiime2.Artifact.load(os.path.join(path, "filtered_samples_table.qza"))
            else:
                print("The input experiment does not exist please re-run that experiment or choose another")

        visual_output = os.path.join(output_dir, "visuals")
        if not os.path.exists(visual_output):
            os.makedirs(visual_output)


        """
        Collapsing the table to have the taxa names from the classifier
        """

        taxa_table = taxa.methods.collapse(table=table,
                                      taxonomy=sequences,
                                      level=6)

        # Getting the relative frequency
        id_freq = feature_table.methods.relative_frequency(table)
        otu_freq = feature_table.methods.relative_frequency(taxa_table.collapsed_table)

        # Saving the table information
        relative_freq_tab = feature_table.visualizers.summarize(id_freq.relative_frequency_table)
        relative_freq_tab.visualization.save(os.path.join(visual_output,"id_relative_freq_table"))

        # Saving the table information
        otu_freq_tab = feature_table.visualizers.summarize(otu_freq.relative_frequency_table)
        otu_freq_tab.visualization.save(os.path.join(visual_output, "otu_relative_freq_table"))

        taxa_table.collapsed_table.save(os.path.join(output_dir,"collapsed_table"))

        """
        Convert the table into biom table format (.txt file) for machine learning and LEFSE style tools
        """
        biom_table = otu_freq.relative_frequency_table.view(biom.Table)
        # print(biom_table.to_tsv())
        df = pd.read_csv(io.StringIO(biom_table.to_tsv()), sep='\t', header=1)
        samples = df.columns.values.tolist()[1:]

        print(df)

        meta_data = {}
        for id in samples:
            metadata_id = db.get_one_selective({"run_accession":id},{"sample_alias":1,"_id":0},"samples")["sample_alias"]
            condition = db.get_one_selective({"sample":metadata_id},{"dx":1,"_id":0},"metadata")
            if condition is not None:
                meta_data[id] = condition["dx"]
            else:
                meta_data[id] = "inconclusive"


        def new_headers(df, metadata):
            result = [('#Diagnosis', '#OTU id')]
            current = df.columns
            for i in current[1:]:
                result.append((metadata[i], i))
            return result

        df.columns = pd.MultiIndex.from_tuples(new_headers(df, meta_data))

        df = df.drop(' ', axis=1, level=0)

        df.to_json(path_or_buf=output_dir+"OTU_Table.json")

        experiment = {
            "experiment_id": experiment_id,
            "stage": "Feature_Classification",
            "parameters": params,
            "input": input,  # filepath or experiment name
            "output": {"visuals": visual_output, "data":os.path.join(output_dir,"collapsed_table")},
        }

        db.new_experiment(experiment)
        db.close()
