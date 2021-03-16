import json
import os
from pymongoClient import client
import qiime2
from qiime2.plugins import alignment, phylogeny

CURRENT_STAGE = "Rooted_Tree"

if __name__ == '__main__':

    db = client.dbClient()
    outputs = db.default_output_names(CURRENT_STAGE)

    output_dir_data = os.getenv("OUTPUT_DIR")

    out_rooted_tree = os.path.join(output_dir_data, outputs["data"][0])

    experiment_id = os.getenv("EXP_ID")
    parent_name = os.getenv("PARENT")
    params = json.loads(os.getenv("PARAMS"))

    if db.check_doc_exists({"_id": experiment_id}, "experiment"):
        print("Sorry that experiment_id already exists, please use a new experiment ID")
    else:
        parent = db.stage_parent_correct(CURRENT_STAGE, parent_name)
        if parent is not None:
            representative_sequences = qiime2.Artifact.load(parent["output"]["data"][1])

            if not os.path.exists(output_dir_data):
                os.makedirs(output_dir_data)

            mafft_alignment = alignment.methods.mafft(representative_sequences)
            masked_mafft_alignment = alignment.methods.mask(mafft_alignment.alignment)
            unrooted_tree = phylogeny.methods.fasttree(masked_mafft_alignment.masked_alignment)
            rooted_tree = phylogeny.methods.midpoint_root(unrooted_tree.tree)

            rooted_tree.rooted_tree.save(out_rooted_tree)



            this_experiment = {
                "_id": experiment_id,
                "parent": parent_name,
                "stage": CURRENT_STAGE,
                "output": {
                    "data": out_rooted_tree
                }
            }

            db.new_experiment(this_experiment)

    db.close()
