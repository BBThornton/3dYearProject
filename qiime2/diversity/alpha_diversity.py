import json
import os
from pymongoClient import client
import qiime2
import pandas as pd
from qiime2.plugins import diversity, metadata, feature_table, empress, emperor

CURRENT_STAGE = "Alpha_Diversity"

if __name__ == '__main__':
    db = client.dbClient()
    outputs = db.default_output_names(CURRENT_STAGE)

    output_dir_data = os.getenv("OUTPUT_DIR")
    output_dir_visuals = os.path.join(output_dir_data, "Visuals")

    out_diversity_artifact = os.path.join(output_dir_data, outputs["data"][0])
    out_alpha_boxplot = os.path.join(output_dir_visuals, outputs["visuals"][0])
    out_beta_diversity_boxplots_dx = os.path.join(output_dir_visuals, outputs["visuals"][1])
    out_empress_plot = os.path.join(output_dir_visuals, outputs["visuals"][2])

    experiment_id = os.getenv("EXP_ID")
    parent_name = os.getenv("PARENT")
    params = json.loads(os.getenv("PARAMS"))

    if db.check_doc_exists({"_id": experiment_id}, "experiment"):
        print("Sorry that experiment_id already exists, please use a new experiment ID")
    else:
        parent = db.stage_parent_correct(CURRENT_STAGE, parent_name)
        if parent is not None:
            # Metadata for the samples used in diversity metrics to determine importance
            metadata_file = db.get_specified_parent_stage("Metadata_Creator", [parent], [])["output"]["data"]
            sample_metadata = qiime2.Metadata.load(metadata_file)

            # Tree for all the phylogenic diversity metrics
            phylogenetic_tree_file = db.get_specified_parent_stage("Rooted_Tree", [parent], [])["output"]["data"]
            phylogenetic_tree = qiime2.Artifact.load(phylogenetic_tree_file)

            # Classification file used in order to convert the UIDs to the taxonomic labels
            classification_file = db.get_specified_parent_stage("Feature_Classification", [parent], [])["output"][
                "data"]
            classification = qiime2.Artifact.load(classification_file)

            # The UID sequences to perform diversity analysis on
            sequences = qiime2.Artifact.load(parent["output"]["data"][1])

            # Filter the sequences to remove samples with no diagnosis
            filtered_sequences = feature_table.methods.filter_samples(sequences, metadata=sample_metadata,
                                                                      where='"dx" IS NOT "NaN"')
            # Filter the sequences to remove samples with no diagnosis
            df = sample_metadata.to_dataframe()
            filtered = df.dropna(subset=['dx'])
            print(filtered)
            filtered_metadata = qiime2.metadata.Metadata(filtered)

            # Set up the file location for the outputs (ensuring it exists)
            if not os.path.exists(output_dir_visuals):
                os.makedirs(output_dir_visuals)

            diversity_metrics = diversity.pipelines.core_metrics_phylogenetic(table=filtered_sequences.filtered_table,
                                                                              phylogeny=phylogenetic_tree,
                                                                              sampling_depth=1742,
                                                                              metadata=filtered_metadata)


            # filtered_sequences_relative = feature_table.methods.filter_samples(diversity_metrics.rarefied_table,
            #                                                                    metadata=sample_metadata,
            #                                                                    where='"dx" IS NOT "NaN"')

            relative_sequence = feature_table.methods.relative_frequency(diversity_metrics.rarefied_table)
            feature_table.visualizers.summarize(relative_sequence.relative_frequency_table).visualization.save(output_dir_data+"/test_test")


            # Uncomment to see all outputs of this metric calculation
            # print(diversity_metrics)

            # Alpha diversity visualisations
            alpha_diversity = diversity.pipelines.alpha(filtered_sequences.filtered_table, metric="shannon")

            alpha_diversity.alpha_diversity.save(out_diversity_artifact)

            correlation = diversity.visualizers.alpha_group_significance(alpha_diversity.alpha_diversity,
                                                                         sample_metadata)
            correlation.visualization.save(out_alpha_boxplot)

            # Beta diversity with relation to the diagnosis metadata
            dx_beta_diversity = diversity.visualizers.beta_group_significance(
                diversity_metrics.weighted_unifrac_distance_matrix, sample_metadata.get_column('dx'), 'permanova',
                pairwise=True)

            dx_beta_diversity.visualization.save(out_beta_diversity_boxplots_dx)

            # Pcoa biplot used for the empress plot
            pcoa_biplot_2 = diversity.methods.pcoa_biplot(diversity_metrics.weighted_unifrac_pcoa_results,
                                                          relative_sequence.relative_frequency_table)
            pcoa_biplot_2.biplot.save(output_dir_data + "/BIPLOT")

            # diversity_metrics.weighted_unifrac_pcoa_results.save(output_dir_data + "/old_weighted_unifrac")

            #OLD VS NEW
            # relative_sequence.relative_frequency_table.save(output_dir_data+"/OLD_FEATURE")
            ft = qiime2.Artifact.load("./data/morgan/alpha_diversity/OLD_FEATURE.qza")




            # Empress visual provides both the PCOA plots and the phylogenetic tree. Also shows important features
            # for PCOA positioning
            empress_plot = empress.visualizers.community_plot(tree=phylogenetic_tree,
                                                              pcoa=pcoa_biplot_2.biplot,
                                                              feature_table=ft,
                                                              sample_metadata=sample_metadata,
                                                              feature_metadata=classification.view(qiime2.Metadata),
                                                              number_of_features=10,
                                                              filter_extra_samples=True, filter_missing_features=True,
                                                              ignore_missing_samples=True)
            empress_plot.visualization.save(out_empress_plot)

            this_experiment = {
                "_id": experiment_id,
                "parent": parent_name,
                "stage": CURRENT_STAGE,
                "output": {
                    "visuals": [out_alpha_boxplot,out_beta_diversity_boxplots_dx,out_empress_plot],
                    "data": [out_diversity_artifact]
                }
            }

            # db.new_experiment(this_experiment)

    db.close()
