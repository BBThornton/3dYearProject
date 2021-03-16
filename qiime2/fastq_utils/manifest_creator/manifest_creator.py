import json
import os
from os import path

from pymongoClient import client


def get_sample_locations(criteria):
    db = client.dbClient()
    docs = db.query(criteria, 'samples')
    db.close()
    return docs


def write_manifest(data, manifest_output_dir):
    with open(manifest_output_dir, 'w') as f:
        f.write('sample-id\tabsolute-filepath\n')
        for sample in data:
            # TODO get the study accession instead of the name from the database
            line = sample['run_accession'] + '\t' + \
                   "/qiime_data_import/"+sample['file_location'][2:] + "/" +sample['run_accession']+'.fastq.gz'
            f.write(line + '\n')


if __name__ == '__main__':
    experiment_id = os.getenv('EXP_ID')
    parent_name = os.getenv("PARENT")

    db = client.dbClient()
    experiment_id = os.getenv("EXP_ID")
    if db.check_doc_exists({"_id": experiment_id}, "experiment"):
        print("Sorry that experiment_id already exists, please use a new experiment ID")
    else:
        output_dir = os.getenv('OUTPUT_DIR')
        output_dir_data = os.path.join(output_dir,"manifest.txt")
        if not path.exists(output_dir):
            os.makedirs(output_dir)
        samples = os.getenv('SAMPLES')

        stage = "Manifest_Creator"

        this_experiment = {
            "_id": experiment_id,
            "parent":parent_name,
            "stage": stage,
            "output": {
                "visuals":None,
                "data":output_dir_data
            }
        }

        docs = get_sample_locations(json.loads(samples))
        write_manifest(docs, output_dir_data)
        db.new_experiment(this_experiment)

    db.close()