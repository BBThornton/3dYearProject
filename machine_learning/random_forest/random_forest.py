import os
from pymongoClient import client
import pandas as pd

from pymongoClient import client

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, label_binarize
from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import precision_score, recall_score, roc_auc_score, roc_curve, auc
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score

"""
https://towardsdatascience.com/an-implementation-and-explanation-of-the-random-forest-in-python-77bf308a9b76 - 
https://www.codementor.io/@agarrahul01/multiclass-classification-using-random-forest-on-scikit-learn-library-hkk4lwawu
https://laurenliz22.github.io/roc_curve_multiclass_predictions_random_forest_classifier

"""

CURRENT_STAGE = "Random_Forest"

if __name__ == '__main__':
    db = client.dbClient()
    outputs = db.default_output_names(CURRENT_STAGE)

    output_dir_data = os.getenv("OUTPUT_DIR")
    output_dir_visuals = os.path.join(output_dir_data, "Visuals")

    out_auc_plot = os.path.join(output_dir_visuals, outputs["visuals"][0])

    if not os.path.exists(output_dir_visuals):
        os.makedirs(output_dir_visuals)

    experiment_id = os.getenv("EXP_ID")
    parent_name = os.getenv("PARENT")

    if db.check_doc_exists({"_id": experiment_id}, "experiment"):
        print("Sorry that experiment_id already exists, please use a new experiment ID")
    else:
        parent = db.stage_parent_correct(CURRENT_STAGE, parent_name)

        if parent is not None:
            df = pd.read_csv(parent["output"]["data"][0], sep=',',index_col=0,header=0)
            print(df)
            feature_list = list(df.iloc[:, 1:].columns)
            data = df.iloc[:, 1:].values
            labels = [i[0:2] for i in df["dx"]]
            labelsint = []
            for i in labels:
                if i == "CD":
                    i = 0
                elif i == "UC":
                    i = 1
                else:
                    i = 2
                labelsint.append(i)
            print(data)

            X_train, X_test, y_train, y_test = train_test_split(data, labelsint, test_size=0.5, random_state=0)

            sc = StandardScaler()
            X_train = sc.fit_transform(X_train)
            X_test = sc.transform(X_test)

            regressor = RandomForestClassifier(random_state=0, max_features='sqrt')
            regressor.fit(X_train, y_train)

            #TODO REMOVE THIS LINE
            X_test = X_train
            y_test = y_train

            y_pred = regressor.predict(X_test)

            rf_probs = regressor.predict_proba(X_test)

            # Calculate roc auc
            roc_value = roc_auc_score(y_test, rf_probs, multi_class="ovr")

            # Training predictions (to demonstrate overfitting)
            train_rf_predictions = regressor.predict(X_train)
            train_rf_probs = regressor.predict_proba(X_train)

            # Testing predictions (to determine performance)
            rf_predictions = regressor.predict(X_test)
            rf_probs = regressor.predict_proba(X_test)

            y_test_bin = label_binarize(y_test, classes=[0, 1, 2])
            n_classes = y_test_bin.shape[1]

            fpr = dict()
            tpr = dict()
            roc_auc = dict()

            colours = ['green', 'red', 'purple']

            for i in range(n_classes):
                fpr[i], tpr[i], _ = roc_curve(y_test_bin[:, i], rf_probs[:, i])
                plt.plot(fpr[i], tpr[i], color=colours[i], lw=2)
                print('AUC for Class {}: {}'.format(i + 1, auc(fpr[i], tpr[i])))

            plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
            plt.xlim([0.0, 1.0])
            plt.ylim([0.0, 1.05])
            plt.xlabel('False Positive Rate')
            plt.ylabel('True Positive Rate')
            plt.title('AUC of '+experiment_id)
            plt.legend(["CD", "UC", "Healthy", "RANDOM GUESS"])
            plt.savefig(out_auc_plot)

            # Get numerical feature importances
            importances = list(regressor.feature_importances_)
            # List of tuples with variable and importance
            feature_importances = [(feature, round(importance, 2)) for feature, importance in
                                   zip(feature_list, importances)]
            # Sort the feature importances by most important first
            feature_importances = sorted(feature_importances, key=lambda x: x[1], reverse=True)
            # Print out the feature and importances
            [print('Variable: {:20} Importance: {}'.format(*pair)) for pair in feature_importances];

            this_experiment = {
                "_id": experiment_id,
                "parent": parent_name,
                "stage": CURRENT_STAGE,
                "output": {
                    "visuals": out_auc_plot,
                    "data": None
                }
            }

            # db.new_experiment(this_experiment)

        db.close()
