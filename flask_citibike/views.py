#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  7 12:04:28 2017
@author: changyaochen
"""
import os
import codecs
import logging
import pandas as pd
from flask import render_template, request, jsonify, abort
from datetime import datetime
from collections import OrderedDict

# from bokeh.plotting import figure
# from bokeh.embed import components

from .utils import (load_pkl_model, get_mojo_info,
                    sklearn_backend_process,
                    h2o_backend_process)
from .config import log_file
from flask_citibike import app, models, bin_packing, plots

logging.basicConfig(filename=log_file)
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(logging.DEBUG)


@app.route('/')
@app.route('/index')
@app.route('/input', methods=['get', 'post'])
def prediction_input():
    # to populate the station list
    dname = os.path.dirname(os.path.abspath(__file__))
    data_folder = '/'.join(dname.split('/')[:-1]) + '/NYC_bikeshare/data'
    df_stations = pd.read_csv(data_folder + '/NYC_bike_stations_v5.csv')
    # boro = df_stations['neighborhood'].unique().tolist()
    stations = list(set(df_stations['name']))
    stations = sorted(stations)
    blk_list = ['8 Ave & W 31 St']  # somehow this doesn't work
    for item in blk_list:
        stations.remove(item)

    # plot the map
    bokeh_html = plots.station_map()
    return render_template(
        "input.html",
        stations=stations,
        bokeh_html=bokeh_html)


@app.route('/output', methods=['get', 'post'])
def prediction_output():

    # processing age
    default_age = False
    user_age = request.form['user_age']
    # check for the invalid input
    try:
        user_age = float(user_age)
        if user_age < 12 or user_age > 70:
            default_age = True
    except ValueError:
        default_age = True
    if default_age:
        user_age = 25

    # processing date
    default_date = False
    date = request.form['date']
    try:
        datetime.strptime(date, "%m/%d/%Y")
    except ValueError:
        default_date = True

    if default_date:
        date = '06/01/2016'

    # processing gender
    user_gender = request.form.get('user_gender')

    # processing time
    hour = request.form.get('hour')

    # get station name
    start_station = request.form.get('start_station')

    # get temperature
    temperature = request.form.get('temperature')
    # check for the invalid input
    default_temperature = False
    try:
        temperature = float(temperature)
        if temperature < -20 or temperature > 50:
            default_temperature = True
    except ValueError:
        default_temperature = True
    if default_temperature:
        temperature = 15

    # get rain the snow
    if request.form.get('rain'):
        # print('it is raining')
        PRCP = 1.97
    else:
        PRCP = 0

    if request.form.get('snow'):
        # print(it's snowing)
        SNOW = 7.67
    else:
        SNOW = 0

    # get the result
    result = models.prediction(age=user_age,
                               date=date,
                               gender=user_gender,
                               hour=hour,
                               start_station=start_station,
                               TAVG=temperature,
                               PRCP=PRCP,
                               SNOW=SNOW)

    N = 3
    end_neighborhoods = []
    for i in range(N):
        end_neighborhoods.append(
            {'name': result.iloc[i, 0],
             'prob': round(100 * result.iloc[i, 1], 1)})
    # print('Predictions (list type): \n', end_neighborhoods)
    bokeh_html = plots.plot_destination(
        start_station=start_station,
        end_neighborhoods=end_neighborhoods,
        N=N)
    print('get the html in view.py.')

    # script, div = components(bokeh_plot)
    # print('get the script and div for bokeh')
    # end_neighborhoods = [{'name':'Soho', 'prob': 0.9}]
    return render_template('output.html',
                           age=user_age,
                           default_age=default_age,
                           gender=user_gender,
                           end_neighborhoods=end_neighborhoods,
                           N=N,
                           date=date,
                           default_date=default_date,
                           temperature=temperature,
                           default_temperature=default_temperature,
                           hour=hour,
                           bokeh_html=bokeh_html,
                           start_station=start_station,
                           PRCP=PRCP,
                           SNOW=SNOW)


@app.route('/population', methods=['get', 'post'])
def pop():
    bokeh_html = plots.plot_income_pop(output='pop')
    return render_template("bokeh_pop_income.html",
                           bokeh_html=bokeh_html,
                           # script = script,
                           # div = div,
                           )


@app.route('/income', methods=['get', 'post'])
def income():
    bokeh_html = plots.plot_income_pop(output='income')
    return render_template("bokeh_pop_income.html",
                           bokeh_html=bokeh_html
                           )


@app.route('/about', methods=['get', 'post'])
def about():
    return render_template("about.html")


@app.route('/story', methods=['get', 'post'])
def story():
    dname = os.path.dirname(os.path.abspath(__file__))
    return render_template(
        "story.html",
        score_html=codecs.open(
            dname + "/templates/scores_data_story_v3.html", 'r').read(),
        neighborhood_html=codecs.open(
            dname + "/templates/station_in_neighbor.html", 'r').read(),
        cm_html=codecs.open(
            dname + "/templates/confusion_matrix_rf.html", 'r').read()
    )


@app.route('/bin_packing', methods=['get', 'post'])
def bin_packing_input():
    return render_template("bin_packing.html")


@app.route('/bin_packing_output', methods=['get', 'post'])
def bin_packing_output():
    # nums = request.form['nums']
    default_nums = [1, 2, 2, 3, 6, 7, 9]
    default_bin = 10
    default_bin_flag, default_nums_flag = False, False

    nums = request.form['nums']
    # check for the invalid input
    try:
        nums = [int(x) for x in nums.split(',')]
    except ValueError:
        default_nums_flag = True
    if default_nums_flag:
        nums = default_nums

    width = request.form['bin']
    try:
        W = int(width)
    except ValueError:
        default_bin_flag = True
    if default_bin_flag:
        W = default_bin

    W = max(W, max(nums))

    res1, shelves1 = bin_packing.pack(nums, W=W, verbose=False)

    res2, shelves2 = None, None
    exhaustive = False
    if request.form.get('exhaustive') and len(nums) <= 10:
        # do the exhaustive serach
        exhaustive = True
        res2, shelves2 = bin_packing.pack_brute(nums, W, verbose=2)
    
    return render_template("bin_packing_output.html",
                           nums=nums,
                           W=W,
                           res1=res1,
                           res2=res2,
                           shelves1=shelves1,
                           shelves2=shelves2,
                           exhaustive=exhaustive)


# ===== api test ====
SKLEARN_MODEL_NAME = '38267011-model_fold_3.pkl'
XGB_MODEL_NAME = '38324320-model_fold_3.pkl'
MOJO_MODEL_NAME = 'H2OGBM_38331063_fold_3.zip'

supported_backends = ('sklearn', 'xgb' 'h2o')
model_mapping = {'sklearn': SKLEARN_MODEL_NAME,
                 'xgb': XGB_MODEL_NAME,
                 # 'h2o': MOJO_MODEL_NAME,
                 }

app.config["JSON_SORT_KEYS"] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True


@app.route('/api', methods=['POST', 'GET'])
def api():
    """This is the endpoint of api calls."""

    if request.method == 'POST':
        try:  # we want json
            payload = request.get_json(force=True)  # convert it to dict
            data = payload['data']  # we need this key for data
            try:  # backend model choices
                backend = payload['backend']
            except KeyError:
                backend = 'sklearn'  # default option
            model_name = model_mapping[backend]

        except Exception as e:
            print(e)
            abort(400)

        # handle different backends, sklearn and xgb should be the same
        if backend == 'sklearn':
            pred = sklearn_backend_process(model_name, data)
        elif backend == 'xgb':
            pred = sklearn_backend_process(model_name, data)
        elif backend == 'h2o':
            pred = h2o_backend_process(model_name, data)
        else:
            raise Exception('{} backend it not supported.'.format(backend))

        return jsonify(pred)

    else:  # GET, print some info about the model
        all_model_info = OrderedDict()
        for b in model_mapping:
            model_info = OrderedDict()
            model_info['model name'] = model_mapping[b]
            if b in ('sklearn', 'xgb'):
                _, feature_list, meta = load_pkl_model(model_mapping[b])
            elif b in ('h2o',):
                _, feature_list, meta = get_mojo_info(model_mapping[b])
            else:
                raise Exception('{} backend it not supported.'.format(b))
            model_info['meta'] = meta
            model_info['feature names'] = feature_list

            all_model_info[b] = model_info

        return jsonify(all_model_info)
