import json
import os

from pymongoClient import dbClient
import pandas as pd
import numpy as np


def import_data(file, header=1, nan_val=' ', separator=','):
    """

    :param file:
    :param header: val of 1 headers are first line in file, val of -1 headers are in the first column of the file
    :param nan_val:
    :param separator:
    :return:
    """
    if header == 1:
        df = pd.read_csv(file, sep=separator, header=header)
    elif header == -1:
        df = pd.read_csv(file, sep=separator, header=None)
        df = df.T
        headers = df.iloc[0, :]
        df.columns = headers
        df = df.iloc[1:, :]

    # Replace nan values
    df = df.replace(nan_val, np.NaN)

    # Export to json for db entry
    json_data = df.to_json(orient="records")

    return json.loads(json_data)


if __name__ == '__main__':
    metadata_file = os.getenv('META_FILE')
    data = import_data(metadata_file, -1, separator="\t")
    db_client = dbClient()
    for item in data:
        db_client.insert_one(item,"metadata")
    db_client.close()