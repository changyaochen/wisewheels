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
    stations = df_stations['name'].sort_values()
    
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
    
    ## get the result
    result = models.prediction(age = user_age, 
                               date = date, 
                               gender = user_gender,
                               hour = hour,
                               start_station = start_station,
                               TAVG = temperature
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
    return render_template("story.html")
  



#@app.route('/output_old')
#def cesareans_output():
#  #pull 'birth_month' from input field and store it
#  patient = request.args.get('birth_month')
#    #just select the Cesareans  from the birth dtabase for the month that the user inputs
#  query = "SELECT index, attendant, birth_month FROM birth_data_table WHERE delivery_method='Cesarean' AND birth_month='%s'" % patient
#  print(query)
#  query_results=pd.read_sql_query(query,con)
#  print(query_results)
#  births = []
#  for i in range(0,query_results.shape[0]):
#      births.append(dict(index=query_results.iloc[i]['index'], attendant=query_results.iloc[i]['attendant'], birth_month=query_results.iloc[i]['birth_month']))
#      the_result = ''
#  return render_template("output.html", births = births, the_result = the_result)

#def index():
#    return render_template("index.html",
#       title = 'Home', user = { 'nickname': 'Miguel' },
#       )

#@app.route('/db')
#def birth_page():
#    sql_query = """                                                             
#                SELECT * FROM birth_data_table WHERE delivery_method='Cesarean'\
#;                                                                               
#                """
#    query_results = pd.read_sql_query(sql_query,con)
#    births = ""
#    print(query_results[:10])
#    for i in range(0,10):
#        births += query_results.iloc[i]['birth_month']
#        births += "<br>"
#    return births
#
#@app.route('/db_fancy')
#def cesareans_page_fancy():
#    sql_query = """
#               SELECT index, attendant, birth_month FROM birth_data_table WHERE delivery_method='Cesarean';
#                """
#    query_results=pd.read_sql_query(sql_query,con)
#    births = []
#    for i in range(0,query_results.shape[0]):
#        births.append(dict(index=query_results.iloc[i]['index'], attendant=query_results.iloc[i]['attendant'], birth_month=query_results.iloc[i]['birth_month']))
#    return render_template('cesareans.html',births=births)