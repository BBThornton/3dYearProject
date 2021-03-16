import json
import os
import subprocess
import sys
import sklearn
from pymongoClient import client
import qiime2
from qiime2.plugins import metadata, composition, feature_table

CURRENT_STAGE = "Differential_Abundance"

if __name__ == '__main__':
    db = client.dbClient()
    outputs = db.default_output_names(CURRENT_STAGE)

    output_dir_data = os.getenv("OUTPUT_DIR")
    # output_dir_visuals = os.path.join(output_dir_data, "Visuals")
    #
    # out_classified_taxa_artifact = os.path.join(output_dir_data, outputs["data"][0])
    # out_classified_taxa_table = os.path.join(output_dir_visuals, outputs["visuals"][0])

    experiment_id = os.getenv("EXP_ID")
    parent_name = os.getenv("PARENT")
    params = json.loads(os.getenv("PARAMS"))

    if db.check_doc_exists({"_id": experiment_id}, "experiment"):
        print("Sorry that experiment_id already exists, please use a new experiment ID")
    else:
        parent = db.stage_parent_correct(CURRENT_STAGE, parent_name)
        if parent is not None:
            metadata_file = db.get_specified_parent_stage("Metadata_Creator", [parent], [])["output"]["data"]
            sample_metadata = qiime2.Metadata.load(metadata_file)

            table = qiime2.Artifact.load(parent["output"]["data"][0])
            filtered_sequences = feature_table.methods.filter_samples(table, metadata=sample_metadata,
                                                                      where='"dx" IS NOT "NaN"')

            comp_table = composition.methods.add_pseudocount(filtered_sequences.filtered_table).composition_table
            # filtered_table = feature_table.methods.filter_samples(table,metadata=sample_metadata)

            vis = composition.visualizers.ancom(comp_table, sample_metadata.get_column('dx'))

            print("HI")
            if not os.path.exists(output_dir_data):
                os.makedirs(output_dir_data)

            vis.visualization.save(output_dir_data + '/temp')



            #
            # this_experiment = {
            #     "_id": experiment_id,
            #     "parent": parent_name,
            #     "stage": CURRENT_STAGE,
            #     "output": {
            #         "visuals": out_classified_taxa_table,
            #         "data": out_classified_taxa_artifact
            #     }
            # }
            #
            # db.new_experiment(this_experiment)

    db.close()
