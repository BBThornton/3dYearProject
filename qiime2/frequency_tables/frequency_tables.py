import json
import os
from pymongoClient import client
import qiime2
import pandas as pd
from qiime2.plugins import taxa, feature_table
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import Divider, Size
import seaborn as sns
import pathlib
import shutil
import tempfile

CURRENT_STAGE = "Frequency_Tables"



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
            if file.suffix == '.csv':
                data.append(pd.read_csv(file))
                # shutil.copy(file, dest)
    return data


if __name__ == '__main__':
    db = client.dbClient()
    outputs = db.default_output_names(CURRENT_STAGE)

    output_dir_data = os.getenv("OUTPUT_DIR")
    output_dir_visuals = os.path.join(output_dir_data, "Visuals")

    out_frequency_collapsed_table = os.path.join(output_dir_data, outputs["data"][0])
    out_frequency_uid_collapsed_table = os.path.join(output_dir_data, outputs["data"][1])
    out_relative_collapsed_table_artifact = os.path.join(output_dir_data, outputs["data"][2])
    out_relative_collapsed_table_artifact_uid = os.path.join(output_dir_data, outputs["data"][3])

    out_id_freq_table = os.path.join(output_dir_visuals, outputs["visuals"][0])
    out_otu_freq_table = os.path.join(output_dir_visuals, outputs["visuals"][1])
    out_id_rel_freq_table = os.path.join(output_dir_visuals, outputs["visuals"][2])
    out_otu_rel_freq_table = os.path.join(output_dir_visuals, outputs["visuals"][3])
    out_stacked_frequency = os.path.join(output_dir_visuals, outputs["visuals"][4])
    out_individual_boxplot = os.path.join(output_dir_visuals, outputs["visuals"][5])

    experiment_id = os.getenv("EXP_ID")
    parent_name = os.getenv("PARENT")
    params = json.loads(os.getenv("PARAMS"))

    if db.check_doc_exists({"_id": experiment_id}, "experiment"):
        print("Sorry that experiment_id already exists, please use a new experiment ID")
    else:
        parent = db.stage_parent_correct(CURRENT_STAGE, parent_name)
        # print(parent["parent"])
        if parent is not None:
            if not os.path.exists(output_dir_visuals):
                os.makedirs(output_dir_visuals)

            sequences = qiime2.Artifact.load(parent["output"]["data"])

            reference_table_experiment = db.stage_parent_correct("Quality_Analysis", parent["parent"])

            if reference_table_experiment is not None:

                reference_table = qiime2.Artifact.load(reference_table_experiment["output"]["data"][0])

                taxa_table = taxa.methods.collapse(table=reference_table,
                                                   taxonomy=sequences,
                                                   level=params["level"])

                taxa_table.collapsed_table.save(out_frequency_collapsed_table)
                reference_table.save(out_frequency_uid_collapsed_table)

                feature_table.visualizers.summarize(reference_table).visualization.save(out_id_freq_table)
                feature_table.visualizers.summarize(taxa_table.collapsed_table).visualization.save(out_otu_freq_table)


                # Getting the relative frequency
                id_freq = feature_table.methods.relative_frequency(reference_table)
                otu_freq = feature_table.methods.relative_frequency(taxa_table.collapsed_table)

                # Saving the table information
                relative_freq_tab = feature_table.visualizers.summarize(id_freq.relative_frequency_table)
                relative_freq_tab.visualization.save(out_id_rel_freq_table)

                # Saving the table information
                otu_freq_tab = feature_table.visualizers.summarize(otu_freq.relative_frequency_table)
                otu_freq_tab.visualization.save(out_otu_rel_freq_table)

                otu_freq.relative_frequency_table.save(out_relative_collapsed_table_artifact)
                id_freq.relative_frequency_table.save(out_relative_collapsed_table_artifact_uid)

                # Metadata for the samples used in diversity metrics to determine importance
                metadata_file = db.get_specified_parent_stage("Metadata_Creator", [parent], [])["output"]["data"]
                sample_metadata = qiime2.Metadata.load(metadata_file)

                stacked_boxplot = taxa.visualizers.barplot(reference_table, sequences, sample_metadata)
                stacked_boxplot.visualization.save(out_stacked_frequency)

                metadata_columns = sample_metadata.to_dataframe().columns

                # Extract the data from the stacked boxplot
                data = extract_csvs(stacked_boxplot.visualization, './data/temp/csv')
                level_4 = data[4]

                # Filters the level 4 data to CD and UC
                IBD_level_4 = level_4.loc[level_4['dx'].isin(["CD", "UC"])]
                IBD_level_4 = IBD_level_4.drop(columns=metadata_columns)
                IBD_level_4 = IBD_level_4.set_index('index')

                # Normalise the data around 0
                standardised = (IBD_level_4 - IBD_level_4.mean()) / IBD_level_4.std()

                # sets the sizing so as much of the label can be shown as possible
                fig = plt.figure(figsize=(11.7, 8.27))
                h = [Size.Fixed(6.), Size.Scaled(.5), Size.Fixed(.2)]
                v = [Size.Fixed(0.7), Size.Scaled(.5), Size.Fixed(.5)]
                divider = Divider(fig, (0, 0, 1, 1), h, v, aspect=False)
                ax = fig.add_axes(divider.get_position(),
                                  axes_locator=divider.new_locator(nx=1, ny=1))

                # Plots the relative frequency
                sns.boxplot(y="variable", x="value", data=pd.melt(standardised), showfliers=False, width=.6, ax=ax)
                ax.xaxis.grid(True)
                ax.set(ylabel="Bacteria", xlabel="Relative Abundance",
                       title="Relative Abundance for IBD for taxa at level 4")
                sns.despine(trim=True, left=True)
                plt.savefig(out_individual_boxplot)

                this_experiment = {
                    "_id": experiment_id,
                    "parent": parent_name,
                    "stage": CURRENT_STAGE,
                    "output": {
                        "visuals": [out_id_freq_table,out_otu_freq_table,out_id_rel_freq_table, out_otu_rel_freq_table, out_stacked_frequency,
                                    out_individual_boxplot],
                        "data": [out_frequency_collapsed_table, out_frequency_uid_collapsed_table,
                                 out_relative_collapsed_table_artifact, out_relative_collapsed_table_artifact_uid]
                    }
                }

                db.new_experiment(this_experiment)

    db.close()
