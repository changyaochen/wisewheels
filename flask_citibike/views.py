#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  7 12:04:28 2017

@author: changyaochen
"""

import os, re
from flask import render_template, request
from flask_citibike import app
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import pandas as pd
import psycopg2
from bokeh.plotting import figure
from bokeh.embed import components 
import codecs


from flask_citibike import models
from flask_citibike import plots
from datetime import datetime

user = 'changyaochen' #add your username here (same as previous postgreSQL)            
host = 'localhost'
dbname = 'birth_db'
db = create_engine('postgres://%s%s/%s'%(user,host,dbname))
con = None
# con = psycopg2.connect(database = dbname, user = user)


@app.route('/')
@app.route('/index')  
@app.route('/input', methods = ['get', 'post'])
def prediction_input():
    ## to populate the station list
    dname = os.path.dirname(os.path.abspath(__file__))
    data_folder = '/'.join(dname.split('/')[:-1]) + '/NYC_bikeshare/data'
    df_stations = pd.read_csv(data_folder + '/NYC_bike_stations_v5.csv')
    boro = df_stations['neighborhood'].unique().tolist()
    stations = list(set(df_stations['name']))    
    stations = sorted(stations)
    blk_list = ['8 Ave & W 31 St']  # somehow this doesn't work
    for item in blk_list:
      stations.remove(item)
    
    ## plot the map
    bokeh_html = plots.station_map()
    return render_template("input.html", 
                           stations = stations,
                           bokeh_html = bokeh_html)


@app.route('/output', methods = ['get', 'post'])
def prediction_output(): 
  
    ## processing age
    default_age = False     
    user_age = request.form['user_age']
    ## check for the invalid input  
    try:
      user_age = float(user_age)
      if user_age < 12 or user_age > 70:
        default_age = True
    except ValueError:
      default_age = True         
    if default_age:
      user_age = 25
    
    ## processing date
    default_date = False
    date = request.form['date']
    try:
        datetime.strptime(date, "%m/%d/%Y")
    except ValueError:
        default_date = True
    
    if default_date:
      date = '06/01/2016'
    
    ## processing gender
    user_gender = request.form.get('user_gender')
    
    ## processing time
    hour = request.form.get('hour')
    
    ## get station name
    start_station = request.form.get('start_station')
    
    ## get temperature
    temperature = request.form.get('temperature')
    ## check for the invalid input  
    default_temperature = False
    try:
      temperature = float(temperature)
      if temperature < -20 or temperature > 50:
        default_temperature = True
    except ValueError:
      default_temperature = True         
    if default_temperature:
      temperature = 15
      
    ## get rain the snow
    if request.form.get('rain'):
      #print('it is raining')
      PRCP = 1.97
    else:
      PRCP = 0
    
    if request.form.get('snow'):
      #print(it's snowing)
      SNOW = 7.67
    else:
      SNOW = 0
    
    
    ## get the result
    result = models.prediction(age = user_age, 
                               date = date, 
                               gender = user_gender,
                               hour = hour,
                               start_station = start_station,
                               TAVG = temperature,
                               PRCP = PRCP,
                               SNOW = SNOW
                               )
    N = 3
    end_neighborhoods = []
    for i in range(N):
      end_neighborhoods.append(
          {'name': result.iloc[i, 0],
           'prob': round(100*result.iloc[i, 1], 1)})
    #print('Predictions (list type): \n', end_neighborhoods)
    bokeh_html = plots.plot_destination(
                      start_station = start_station,
                      end_neighborhoods = end_neighborhoods,
                      N = N) 
    print('get the html in view.py.')
      
    #script, div = components(bokeh_plot)
    #print('get the script and div for bokeh')
    #end_neighborhoods = [{'name':'Soho', 'prob': 0.9}]
    return render_template('output.html', 
                           age = user_age, 
                           default_age = default_age,
                           gender = user_gender,
                           end_neighborhoods = end_neighborhoods,
                           N = N,
                           date = date,
                           default_date = default_date,
                           temperature = temperature,
                           default_temperature = default_temperature,
                           hour = hour,
                           bokeh_html = bokeh_html,
                           start_station = start_station, 
                           PRCP = PRCP,
                           SNOW = SNOW
                           )

@app.route('/population', methods = ['get', 'post'])
def pop():
    bokeh_html = plots.plot_income_pop(output='pop') 
    return render_template("bokeh_pop_income.html", 
                           bokeh_html=bokeh_html
                           #script = script,
                           #div = div
                           )
@app.route('/income', methods = ['get', 'post'])
def income():
    bokeh_html = plots.plot_income_pop(output='income') 
    return render_template("bokeh_pop_income.html", 
                           bokeh_html=bokeh_html
                           #script = script,
                           #div = div
                           )
@app.route('/about', methods = ['get', 'post'])
def about():
    return render_template("about.html")

@app.route('/story', methods = ['get', 'post'])
def story():
    dname = os.path.dirname(os.path.abspath(__file__))
    return render_template("story.html", 
                           score_html = codecs.open(dname +
                          "/templates/scores_data_story_v3.html", 'r').read(),
                           neighborhood_html = codecs.open(dname +
                          "/templates/station_in_neighbor.html", 'r').read(),
                           cm_html = codecs.open(dname +
                          "/templates/confusion_matrix_rf.html", 'r').read()
                          )
  
