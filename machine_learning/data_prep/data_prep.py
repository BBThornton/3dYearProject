import ast
import json
import os
from pymongoClient import client
import qiime2

import pandas as pd
import pathlib
import tempfile

CURRENT_STAGE = "Machine_Learning_Data_Prep"



def extract_csvs(viz, dest):
    """
    Function will extract the raw data from a visualisation, prevents the need for recomputing data to display in another no Qiime form
    :param viz:
    :param dest:
    :return:
    """
    data = []
    # create a temp dir to work in, that way we don't have
    # to manually clean up, later
    with tempfile.TemporaryDirectory() as temp:
        # export the `data` directory from the visualization
        viz.export_data(temp)
        temp_pathlib = pathlib.Path(temp)
        # iterate through all of the files that we just extracted above
        for file in temp_pathlib.iterdir():
            # if the file is a csv file, copy it to the final dest
            if file.suffix == '.tsv':
                data.append(pd.read_csv(file,sep="\t",header=0,index_col=0))
                # shutil.copy(file, dest)
    return data


if __name__ == '__main__':
    db = client.dbClient()
    outputs = db.default_output_names(CURRENT_STAGE)

    output_dir_data = os.getenv("OUTPUT_DIR")

    out_data_table = os.path.join(output_dir_data, outputs["data"][0])

    experiment_id = os.getenv("EXP_ID")
    parents = ast.literal_eval((os.getenv("PARENT_NAMES")))
    params = json.loads(os.getenv("PARAMS"))

    if db.check_doc_exists({"_id": experiment_id}, "experiment"):
        print("Sorry that experiment_id already exists, please use a new experiment ID")
    else:
        df = pd.DataFrame()
        if not os.path.exists(output_dir_data):
            os.makedirs(output_dir_data)
        for item in parents:
            parent = db.get_one({"_id": item[0]}, "experiment")
            if parent is not None:
                stage_outputs = db.get_one({"_id":parent["stage"]},"services")["output"]["data"]

                data = parent["output"]["data"][stage_outputs.index(item[1])]
                if parents.index(item) == 0:
                    metadata_file = db.get_specified_parent_stage("Metadata_Creator", [parent], [])["output"]["data"]

                    df = pd.read_csv(metadata_file,sep="\t",header=0,index_col=0)
                    df= df.dropna(subset=[params["classifier_column"]])
                    df = df[params["classifier_column"]]


                if data[-4:] == ".qza":
                    artifact = qiime2.Artifact.load(data)
                    temp = extract_csvs(artifact,"ttt")
                    print(temp)
                    df = pd.merge(left=df,left_index=True, right=temp[0], right_index=True,how='inner')
                elif data[-4:] == ".tsv":
                    if parent["stage"] == "Freq_To_Biom":
                        print("HI THERE")
                        temp = pd.read_csv(data,sep="\t",header=None)
                        temp = temp.drop(index=0)
                        temp = temp.T
                        temp = temp.set_index(temp.columns[0])
                        temp.columns = temp.iloc[0]
                        temp = temp.iloc[1:]
                        df = pd.merge(left=df,left_index=True, right=temp, right_index=True,how='inner')

        df.to_csv(out_data_table)






        this_experiment = {
            "_id": experiment_id,
            "parent": None,
            "stage": CURRENT_STAGE,
            "output": {
                "data": [out_data_table]
            }
        }

        # db.new_experiment(this_experiment)

    db.close()
