import os
import ast
import pickle
import sys
import pandas as pd
import numpy as np
from subprocess import run, PIPE
from typing import List, Dict

sys.path.append('.')
from .config import java_dir, get_data_file, get_model_file

JAVAC_PATH = '/usr/bin/javac'
JAVA_PATH = '/usr/bin/java'
JAVA_FILE = 'MojoRunner'
h2o_feature_file = os.path.join(java_dir, 'h2o_feature_names.txt')


def _compile_mojo():
    """Simply compile the java file."""
    cmd = [JAVAC_PATH,
           '-cp',
           os.path.join(java_dir, 'localjars', 'h2o-genmodel.jar'),
           os.path.join(java_dir, JAVA_FILE + '.java')]
    run(cmd, shell=False, check=True)


def _run_mojo(model_name: str,
              csv_file_name: str,
              score: bool = True) -> Dict:
    """Run the mojo on the data.model_name

    If score is False, we will pass None . The purpose
    is to only get the feature name list.
    """

    _indicator = '===>'
    csv_file = get_data_file(csv_file_name) if score else ''
    cmd = [JAVA_PATH,
           '-cp',
           ':'.join([java_dir,
                    os.path.join(java_dir, 'localjars', 'h2o-genmodel.jar')]),
           JAVA_FILE,
           get_model_file(model_name),
           csv_file,
           h2o_feature_file
           ]
    if score:
        output = run(cmd,
                     shell=False,
                     check=True,
                     stdout=PIPE).stdout.decode('utf-8')
        # we want the last line
        items = output.split('\n')
        items = [x for x in items if len(x) > 0]  # remove empty items

        if not items[-1].startswith(_indicator):
            raise Exception('{} sign not found. '.format(_indicator) +
                            'There is error in making predictions.')
        # convert the list in string to a python list
        results = items[-1][len(_indicator):].strip()
        return {'prediction': ast.literal_eval(results)}

    else:
        try:
            run(cmd, shell=False, check=False)
            print('The java.io.FileNotFoundException is expected')
        except Exception as e:  # it is expected to fail
            pass
        return {'prediction': [-999.0]}


def get_mojo_info(model_name: str):
    """Get the information about the mojo"""

    meta = 'MOJO from H2O.ai'

    _compile_mojo()

    # make a dummy run to get the feature names
    _ = _run_mojo(model_name, 'not_used', False)
    with open(h2o_feature_file, 'r') as f:
        feature_list = f.read().splitlines()

    return None, feature_list, meta


def load_pkl_model(model_file: str):
    """Load the pickled model object.

    Args:
        model_file (str): bare name of the pickled model objects

    Returns:
        tuple of (
            actual model object,
            ordered list of feature names,
            meta information)
    """
    with open(get_model_file(model_file), 'rb') as f:
        obj = pickle.load(f)

    # sanity check
    keys = obj.keys()
    if 'model' not in keys:
        raise Exception('A `model` object is needed')
    if 'ordered_feature_list' not in keys:
        raise Exception('A `ordered_feature_list` is needed')

    if 'meta' in keys:
        meta = obj['meta']
    else:
        meta = None

    return (obj['model'], obj['ordered_feature_list'], meta)


def check_payload(data: Dict, ordered_feature_list: List) -> List[List]:
    """Validate the data POSTed from http request.

    Args:
        data (dict): The dictionary converted from the json payload['data'].
        ordered_feature_list (list): List of expected features in the correct
            order.

    Returns:
        List of feature list of values, ordered by the correct order.
    """

    keys = data.keys()
    values = []

    for f in ordered_feature_list:
        if f in data:
            values.append(data[f])
        else:
            raise Exception(
                'The feature {f} is needed but not provided.'.format(f=f))

    return values


def get_precition_sklearn(
        model,
        inputs: List[List],
        ordered_feature_list: List) -> Dict:
    """Loads and model, and applies the data to get prediction.

    Applies the inputs to the sklearn model and get predictions.
    """
    if not hasattr(model, 'predict_proba'):
        raise Exception('There is no `predict_proba` method for the model.')

    df_pred = pd.DataFrame(
        data={x: y for (x, y) in zip(ordered_feature_list, inputs)})
    pred = model.predict_proba(df_pred[df_pred.columns])

    return {'prediction': pred[:, -1].tolist()}


def get_model_and_check_input(model_name: str, data: Dict):
    """Wrapper to load model, and verify input data."""

    model, ordered_feature_list, meta = load_pkl_model(model_name)
    # inputs is List[List]
    inputs = check_payload(data, ordered_feature_list)

    return model, ordered_feature_list, meta, inputs


def sklearn_backend_process(model_name: str, data: Dict):
    """Procedural steps with sklearn backend."""

    model, ordered_feature_list, meta, inputs = \
        get_model_and_check_input(model_name, data)

    pred = get_precition_sklearn(model, inputs, ordered_feature_list)

    return pred


def h2o_backend_process(model_name: str, data: Dict, compile=False):
    """Procedural steps with sklearn backend.

    There are 3 major steps involved:
    1. Convert the incoming data to a csv file in the ../data/ folder;
    2. Compile the MOJO file as a java binary
    3. Run java for socring
    """

    # 1. covert data to csv
    csv_file_name = 'score.csv'
    tmp_df = pd.DataFrame.from_dict({k: v for k, v in data.items()})
    tmp_df.to_csv(get_data_file(csv_file_name), index=False)

    # 2. compile the mojo
    if compile:
        _compile_mojo()

    # 3. the actual scoring step
    pred = _run_mojo(model_name=model_name,
                     csv_file_name=csv_file_name,
                     score=True)

    return pred


if __name__ == '__main__':
    h2o_backend_process('2OGBM_38331063_fold_3.zip', {})
