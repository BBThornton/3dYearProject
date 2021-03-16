import json
import os
import subprocess
import sys
import sklearn
from pymongoClient import client
import qiime2
from qiime2.plugins import feature_classifier, metadata

CURRENT_STAGE = "Feature_Classification"

if __name__ == '__main__':
    db = client.dbClient()
    outputs = db.default_output_names(CURRENT_STAGE)

    output_dir_data = os.getenv("OUTPUT_DIR")
    output_dir_visuals = os.path.join(output_dir_data, "Visuals")

    out_classified_taxa_artifact = os.path.join(output_dir_data, outputs["data"][0])
    out_classified_taxa_table = os.path.join(output_dir_visuals, outputs["visuals"][0])

    experiment_id = os.getenv("EXP_ID")
    parent_name = os.getenv("PARENT")
    params = json.loads(os.getenv("PARAMS"))

    if db.check_doc_exists({"_id": experiment_id}, "experiment"):
        print("Sorry that experiment_id already exists, please use a new experiment ID")
    else:
        parent = db.stage_parent_correct(CURRENT_STAGE, parent_name)
        if parent is not None:


            sequences = qiime2.Artifact.load(parent["output"]["data"][1])

            gg_classifier = qiime2.Artifact.load("/qiime_classifier/classifiers/"+params["classifier"]+".qza")

            classify_params = params["classify_sklearn"]
            classify_params["reads"] = sequences
            classify_params["classifier"] = gg_classifier
            taxonomy = feature_classifier.methods.classify_sklearn(**classify_params)

            if not os.path.exists(output_dir_visuals):
                os.makedirs(output_dir_visuals)

            # Visual Creation
            taxonomy_classification = metadata.visualizers.tabulate(taxonomy.classification.view(qiime2.Metadata))
            taxonomy_classification.visualization.save(out_classified_taxa_table)

            # Artifact Creation
            taxonomy.classification.save(out_classified_taxa_artifact)

            this_experiment = {
                "_id": experiment_id,
                "parent": parent_name,
                "stage": CURRENT_STAGE,
                "output": {
                    "visuals": out_classified_taxa_table,
                    "data": out_classified_taxa_artifact
                }
            }

            db.new_experiment(this_experiment)

    db.close()
