import os
from pymongoClient import client
import qiime2

CURRENT_STAGE = "Data_Import"

if __name__ == '__main__':

    db = client.dbClient()
    output_name = db.default_output_names(CURRENT_STAGE)["data"][0]

    experiment_id = os.getenv("EXP_ID")
    parent_name = os.getenv("PARENT")

    output_dir = os.path.join(os.getenv("OUTPUT_DIR"),output_name)

    if db.check_doc_exists({"_id":experiment_id},"experiment") :
        print("Sorry that experiment_id already exists, please use a new experiment ID")
    else:
        parent = db.stage_parent_correct(CURRENT_STAGE, parent_name)
        if parent is not None:
            manifest = parent["output"]["data"]

            single_end_sequences = qiime2.Artifact.import_data('SampleData[SequencesWithQuality]', manifest,
                                                               view_type='SingleEndFastqManifestPhred33V2')

            single_end_sequences.save(output_dir)

            this_experiment = {
                "_id": experiment_id,
                "parent": parent_name,
                "stage": CURRENT_STAGE,
                "output": {
                    "visuals": None,
                    "data": output_dir
                }
            }

            db.new_experiment(this_experiment)

    db.close()

