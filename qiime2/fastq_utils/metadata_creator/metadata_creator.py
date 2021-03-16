import json
import os
from os import path

from pymongoClient import client

CURRENT_STAGE = "Metadata_Creator"
def get_sample_locations(criteria):
    db = client.dbClient()
    docs = db.query(criteria, 'samples')
    db.close()
    return docs


if __name__ == '__main__':
    db = client.dbClient()
    outputs = db.default_output_names(CURRENT_STAGE)

    output_dir_data = os.getenv("OUTPUT_DIR")
    out_metadata = os.path.join(output_dir_data, outputs["data"][0])
    if not path.exists(output_dir_data):
        os.makedirs(output_dir_data)
    experiment_id = os.getenv("EXP_ID")
    parent_name = os.getenv("PARENT")
    params = json.loads(os.getenv("PARAMS"))

    if db.check_doc_exists({"_id": experiment_id}, "experiment"):
        print("Sorry that experiment_id already exists, please use a new experiment ID")
    else:
        parent = db.stage_parent_correct(CURRENT_STAGE, parent_name)
        if parent is not None:
            # Get the sample Id for the given manifest
            samples = []
            sample_manifest = parent["output"]["data"]

            # Get the sampleIds from the manifest
            print(sample_manifest)
            with open(sample_manifest,"r") as f:
                print(f)
                for line in f:
                    split = line.split("\t")
                    samples.append(split[0])

            # Prepare the output file headings
            output_file = open(out_metadata, "w")
            output_file.write("sample-id \t")



            # If selection of specific header
            if "selection" in params:
                db_selection = params["selection"]
                headings = list(db_selection.keys())
                db_selection["_id"] = 0
                db_selection["sample"] = 0
                for item in headings:
                    output_file.write(item + "\t")
            else:
                db_selection = {"_id":0,"sample":0}
                sample_alias = db.get_one_selective({"run_accession":samples[1]}, {"_id": 0}, "samples")["sample_alias"]
                headings = db.get_one_selective({"sample": sample_alias}, {"_id": 0}, "metadata").keys()
                [output_file.write(heading + "\t") for heading in list(headings)[1:]]

            output_file.write("\n")

            # For every sample Id get the metdata and write to file
            for id in samples[1:]:
                sample_alias = db.get_one_selective({"run_accession":id},{"sample_alias" : 1},"samples")["sample_alias"]
                metadata = db.get_one_selective({"sample":sample_alias},db_selection,"metadata")
                output_file.write(id+"\t")
                # This shouldnt happen but for some datasets metadata may be removed from repository so account for that
                if metadata is None:
                    [output_file.write("NaN\t") for item in list(headings)[1:]]
                    output_file.write("\n")

                else:
                    for value in metadata.values():
                        # If no value for the header in the metadata replace with NaN
                        if value is not None:
                            output_file.write(value+"\t")
                        else:
                            output_file.write("NaN\t")
                    output_file.write("\n")


            this_experiment = {
                "_id": experiment_id,
                "parent":parent_name,
                "stage": CURRENT_STAGE,
                "output": {
                    "visuals":None,
                    "data":out_metadata
                }
            }

            db.new_experiment(this_experiment)

    db.close()