import json
import os
from pymongoClient import client
import qiime2
from qiime2.plugins import quality_filter, deblur, feature_table, metadata

CURRENT_STAGE = "Quality_Analysis"

if __name__ == '__main__':

    db = client.dbClient()
    outputs = db.default_output_names(CURRENT_STAGE)

    output_dir_data = os.getenv("OUTPUT_DIR")
    output_dir_visuals = os.path.join(output_dir_data, "Visuals")

    out_filter_samples_artifact = os.path.join(output_dir_data, outputs["data"][0])
    out_filter_representative_seqs = os.path.join(output_dir_data, outputs["data"][1])
    out_q_score_stats = os.path.join(output_dir_visuals, outputs["visuals"][0])
    out_table_summary = os.path.join(output_dir_visuals, outputs["visuals"][1])
    out_deblur_stats = os.path.join(output_dir_visuals, outputs["visuals"][2])

    experiment_id = os.getenv("EXP_ID")
    parent_name = os.getenv("PARENT")
    params = json.loads(os.getenv("PARAMS"))

    if db.check_doc_exists({"_id": experiment_id}, "experiment"):
        print("Sorry that experiment_id already exists, please use a new experiment ID")
    else:
        parent = db.stage_parent_correct(CURRENT_STAGE, parent_name)
        if parent is not None:
            # Run q score
            sequences = qiime2.Artifact.load(parent["output"]["data"])
            q_score_params = params["q_score"]
            q_score_params["demux"] = sequences
            demux_filter_stats = quality_filter.methods.q_score(**q_score_params)

            # Run deblur
            deblur_params = params["deblur_denoise"]
            deblur_params["demultiplexed_seqs"] = demux_filter_stats.filtered_sequences
            deblur_sequences = deblur.methods.denoise_16S(**deblur_params)

            if not os.path.exists(output_dir_visuals):
                os.makedirs(output_dir_visuals)

            # Visual Creation
            q_score_filter_stats = metadata.visualizers.tabulate(demux_filter_stats.filter_stats.view(qiime2.Metadata))
            feature_table_summary = feature_table.visualizers.summarize(deblur_sequences.table)
            per_sample_deblur_stats = deblur.visualizers.visualize_stats(deblur_sequences.stats)

            # Visual Saving
            q_score_filter_stats.visualization.save(out_q_score_stats)
            feature_table_summary.visualization.save(out_table_summary)
            per_sample_deblur_stats.visualization.save(out_deblur_stats)

            # Artifact saving
            deblur_sequences.table.save(out_filter_samples_artifact)
            deblur_sequences.representative_sequences.save(out_filter_representative_seqs)

            # feature_table_df = deblur_sequences.table.view(pd.DataFrame)

            this_experiment = {
                "_id": experiment_id,
                "parent": parent_name,
                "stage": CURRENT_STAGE,
                "output": {
                    "visuals": [out_q_score_stats, out_table_summary, out_deblur_stats],
                    "data": [out_filter_samples_artifact, out_filter_representative_seqs]
                }
            }

            db.new_experiment(this_experiment)

    db.close()
