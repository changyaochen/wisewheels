#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Created on Wed Jun  7 12:04:2k8 2017.

@author: changyaochen
"""
import io
import os
import time
import codecs
import logging
import pandas as pd

from typing import List
from datetime import datetime
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.core.properties import value
from bokeh.models import ColumnDataSource, HoverTool
from flask import render_template, request
from .egg_drop_problem import EggDrop
from .multi_armed_bandit import (
    TestBed, GreedyAgent, EpsilonGreedyAgent, UCBAgent, Simulation)
from .sir_model import SIR

# from bokeh.plotting import figure
# from bokeh.embed import components

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


@app.route('/egg_drop', methods=['get', 'post'])
def egg_drop_input():
    return render_template("egg_drop.html")


@app.route('/egg_drop_output', methods=['get', 'post'])
def egg_drop_output():
    n = request.form['floors'] or 100
    e = request.form['eggs'] or 3
    E = EggDrop(n=int(n), e=int(e))
    result = E.run()
    return render_template("egg_drop_output.html",
                           floors=n,
                           eggs=e,
                           result=result)


@app.route('/bandit', methods=['get', 'post'])
def bandit_input():
    return render_template("bandit.html")


@app.route('/bandit_output', methods=['get', 'post'])
def bandit_output():
    """Run one simulation."""
    try:
        epsilon = float(request.form['epsilon'])
        epsilon = min(max(0, epsilon), 1 - 1e-5)
    except ValueError:
        epsilon = 0.1
    try:
        ucb_c = float(request.form['ucb_c'])
        ucb_c = min(max(0, ucb_c), 1000)
    except ValueError:
        ucb_c = 2
    try:
        num_steps = min(1000, int(request.form['num_steps']))
    except ValueError:
        num_steps = 200
    try:
        num_sim = min(50, int(request.form['num_sim']))
    except ValueError:
        num_sim = 20

    start_time = time.time()
    random_seed = int(1000 * start_time)
    simulation_greedy = Simulation(
        env_type=TestBed,
        agent_type=GreedyAgent,
        num_agents=num_sim,
        init_value=None,
        step=num_steps,
        env_kwargs={'num_arms': 10, 'random_seed': random_seed},
    )

    simulation_greedy.run_all_agents()
    steps_greedy, avg_rewards_greedy = simulation_greedy.aggregate_rewards(
        make_plot=False)

    simulation_eps_greedy = Simulation(
        env_type=TestBed,
        agent_type=EpsilonGreedyAgent,
        num_agents=num_sim,
        init_value=None,
        step=num_steps,
        env_kwargs={'num_arms': 10, 'random_seed': random_seed},
        agent_kwargs={'epsilon': epsilon},
    )
    simulation_eps_greedy.run_all_agents()
    steps_eps_greedy, avg_rewards_eps_greedy = \
        simulation_eps_greedy.aggregate_rewards(make_plot=False)

    simulation_ucb = Simulation(
        env_type=TestBed,
        agent_type=UCBAgent,
        num_agents=num_sim,
        init_value=None,
        step=num_steps,
        env_kwargs={'num_arms': 10, 'random_seed': random_seed},
        agent_kwargs={'c': ucb_c},
    )

    simulation_ucb.run_all_agents()
    steps_ucb, avg_rewards_ucb = simulation_ucb.aggregate_rewards(
        make_plot=False)

    duration_in_second = '{:5.3f}'.format(time.time() - start_time)

    fig = plot_bandit_results(
        steps_greedy=steps_greedy,
        avg_rewards_greedy=avg_rewards_greedy,
        steps_eps_greedy=steps_eps_greedy,
        avg_rewards_eps_greedy=avg_rewards_eps_greedy,
        epsilon=epsilon,
        steps_ucb=steps_ucb,
        avg_rewards_ucb=avg_rewards_ucb,
        ucb_c=ucb_c)
    # Set title
    fig.title.text = f'Results from {num_sim} simulations'
    script, div = components(fig)

    return render_template(
        "bandit_output.html",
        duration_in_second=duration_in_second,
        script=script,
        div=div)


def plot_bandit_results(
        steps_greedy: List,
        avg_rewards_greedy: List,
        steps_eps_greedy: List,
        avg_rewards_eps_greedy: List,
        epsilon: float,
        steps_ucb: List,
        avg_rewards_ucb: List,
        ucb_c: float):
    """Plot bandit results from different policies."""
    fig = figure(plot_width=600, plot_height=400)

    _ = fig.line(
        x=steps_greedy,
        y=avg_rewards_greedy,
        line_alpha=0.3,
        line_color='blue',
        legend='Greedy',
    )
    _ = fig.line(
        x=steps_eps_greedy,
        y=avg_rewards_eps_greedy,
        line_alpha=0.3,
        line_color='red',
        legend=f'epsilon-Greedy, epsilon = {epsilon}',
    )
    _ = fig.line(
        x=steps_ucb,
        y=avg_rewards_ucb,
        line_alpha=0.3,
        line_color='#35B778',
        legend=f'UCB, c = {ucb_c}',
    )
    # Set the x axis label
    fig.xaxis.axis_label = 'Step'
    # Set the y axis label
    fig.yaxis.axis_label = 'Averaged reward'
    fig.legend.location = 'bottom_right'
    fig.sizing_mode = "scale_both"

    return fig


@app.route('/sir', methods=['get', 'post'])
def sir_input():
    """Input for the SIR model."""
    return render_template("sir.html")


@app.route('/sir_output', methods=['get', 'post'])
def sir_output():
    """Run one SIR simulation."""
    # parse the parameters
    try:
        r0 = float(request.form['r0'])
    except ValueError:
        r0 = 2.

    try:
        gamma = 1. / float(request.form['c'])
    except ValueError:
        gamma = 1. / 14

    try:
        eta = float(request.form['eta'])
        eta = min(1., max(0., eta))
    except ValueError:
        eta = 0.03

    try:
        i_init = float(request.form['i'])
        i_init = min(1., max(0., i_init))
    except ValueError:
        i_init = 0.1

    beta = r0 * gamma
    model = SIR(param={
        'beta': beta,
        'gamma': gamma,
        'eta': eta})
    model.run(
        X_init=[1. - i_init, i_init, 0, 0],
        num_steps=120)

    # make plot
    fig = plot_sir_results(model.X)
    # Set title
    fig.title.text = f'Results of SIR model simulations'
    script, div = components(fig)

    return render_template(
        "sir_output.html",
        script=script,
        div=div)


def plot_sir_results(X):
    """Plot SIR results."""
    # unpack the results
    S, I, R, D = X
    time_steps = list(range((len(S))))

    source = ColumnDataSource(data={
        'Day': time_steps,
        'Susceptible': S,
        'Infectious': I,
        'Recovered': R,
        'Dead': D})

    fig = figure(plot_width=600, plot_height=400)

    _ = fig.line(
        x='Day',
        y='Susceptible',
        line_width=3,
        line_alpha=0.3,
        line_color='blue',
        name='Susceptible',
        legend=value('Susceptible'),
        source=source,
    )

    _ = fig.line(
        x='Day',
        y='Infectious',
        line_width=3,
        line_alpha=0.3,
        line_color='darkorange',
        name='Infectious',
        legend=value('Infectious'),
        source=source,
    )

    _ = fig.line(
        x='Day',
        y='Recovered',
        line_width=3,
        line_alpha=0.3,
        line_color='green',
        name='Recovered',
        legend=value('Recovered'),
        source=source,
    )

    _ = fig.line(
        x='Day',
        y='Dead',
        line_width=3,
        line_alpha=0.3,
        line_color='red',
        name='Dead',
        legend=value('Dead'),
        source=source,
    )

    # set the hover tip
    fig.add_tools(HoverTool(
        tooltips=[
            ('Day', '@Day'),
            ('Susceptible', '@Susceptible{%0.2f}'),
            ('Infectious', '@Infectious{%0.2f}'),
            ('Recovered', '@Recovered{%0.2f}'),
            ('Dead', '@Dead{%0.2f}'),
        ],
        mode='vline',
        names=['Infectious'])
    )

    # Set the x axis label
    fig.xaxis.axis_label = 'Day'
    # Set the y axis label
    fig.yaxis.axis_label = 'Proportion of population'
    fig.legend.location = 'top_right'
    fig.sizing_mode = "scale_both"

    return fig
