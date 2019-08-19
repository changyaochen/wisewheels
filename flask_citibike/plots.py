#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  8 20:59:11 2017

@author: changyaochen
"""
import pandas as pd
import os
import bokeh.plotting as bkp
import bokeh.models as bkm
from bokeh.resources import CDN
from bokeh.embed import file_html
from bokeh.models import (
    GMapPlot, GMapOptions, ColumnDataSource, Circle, DataRange1d, PanTool, 
    WheelZoomTool, BoxSelectTool, Range1d
)
# from config import google_map_api_key
google_map_api_key = "AIzaSyAQRCMxY0k1nWkjv3CmQgzMFDZq7E-FI3E"

def plot_income_pop(output = 'income'):
  """
  for informative purpose, showing either the income or population
  by census block
  """
  dname = os.path.dirname(os.path.abspath(__file__))
  project_folder = '/'.join(dname.split('/')[:-1])+'/NYC_bikeshare'
  df = pd.read_csv(project_folder + 
                          '/data/NYC_income_population_lite.csv')
  
  # ======== preparing the plot =======
  map_options = GMapOptions(lat=40.75, lng=-73.95, map_type="roadmap", zoom=12)
  plot = GMapPlot(
      x_range=DataRange1d(), 
      y_range=DataRange1d(), 
      map_options=map_options, 
      api_key = google_map_api_key
  )
  plot.title.text = 'Income and population by station'
  
  #plot.api_key = google_map_api_key
  
  source1 = bkp.ColumnDataSource(data = dict
      (lat = df['centroid_lat'], 
       long = df['centroid_long'],
       income_plot = df['median_income'] / 10000,
       income = df['median_income'],
       pop_plot = df['Population'] / 500,
       pop = df['Population'] 
      ))
  if output == 'income':  
    circle1 = Circle(x = 'long', y = 'lat', fill_color='red',
                     fill_alpha = 0.7, line_alpha = 0, size = 'income_plot')
    plot.add_glyph(source1, circle1)
    plot.add_tools(PanTool(), WheelZoomTool(), BoxSelectTool())
    hover = bkm.HoverTool(tooltips=[('income', '@income{$0,0}')])
    plot.title.text = 'Median input. Data source: US Census'
    plot.add_tools(hover)
    bokeh_map = file_html(plot, CDN, "bokeh")
    print('return the plot!')
    
    #return plot
    return bokeh_map
  
  elif output == 'pop':
    circle1 = Circle(x = 'long', y = 'lat', fill_color='blue',
                     fill_alpha = 0.7, line_alpha = 0, size = 'pop_plot')
    plot.add_glyph(source1, circle1)
    plot.add_tools(PanTool(), WheelZoomTool(), BoxSelectTool())
    hover = bkm.HoverTool(tooltips=[('population', '@pop')])
    plot.title.text = 'Population. Data source: US Census'
    plot.add_tools(hover)
    bokeh_html = file_html(plot, CDN, "bokeh")
  
    #return plot
    return bokeh_html
  
  else: 
    raise
    return 
  
def plot_destination(start_station, end_neighborhoods, N = 3):
  """
  plot the top N most probable end neighborhoods
  """
  dname = os.path.dirname(os.path.abspath(__file__))
  project_folder = '/'.join(dname.split('/')[:-1])+'/NYC_bikeshare'
  df = pd.read_csv(project_folder + 
                          '/data/NYC_neighborhoods.csv')
  df_for_plot = pd.DataFrame(end_neighborhoods)
  df_for_plot = pd.merge(df_for_plot, df, 
                         left_on = 'name', right_on = 'neighborhood',
                         how = 'left')
  lat_centroid = df_for_plot['latitude'].mean()
  long_centroid = df_for_plot['longitude'].mean()
  
  df_station = pd.read_csv(project_folder + 
                          '/data/NYC_bike_stations_v1.csv')
  df_start_station = df_station[df_station['name'] == start_station]
  
  
  ## source for probability
  source1 = bkp.ColumnDataSource(data = dict
      (lat = df_for_plot['latitude'], 
       long = df_for_plot['longitude'],
       prob_plot = 15*df_for_plot['prob']**0.5,
       prob = df_for_plot['prob'],
       name = df_for_plot['name']
      ))
  ## source for start station
  source2 = bkp.ColumnDataSource(data = dict
      (lat = df_start_station['latitude'], 
       long = df_start_station['longitude'],
       name = df_start_station['name']
      ))
  
  ## source for all the stations
  source3 = bkp.ColumnDataSource(data = dict
    (lat = df_station['latitude'], 
     long = df_station['longitude'],
     name = df_station['name'],
     neighbor = df_station['neighborhood'],
    ))
  
  # ======== preparing the plot =======
  map_options = GMapOptions(
                            #lat = lat_centroid,
                            #lng = long_centroid,
                            lat=df_start_station['latitude'].values[0], 
                            lng=df_start_station['longitude'].values[0], 
                            map_type="roadmap", zoom=13)
  plot = GMapPlot(
      x_range=Range1d(), 
      y_range=Range1d(), 
      map_options=map_options,
      api_key = google_map_api_key
  )
  #plot.title.text = 'End neighborhoods'  
  #plot.api_key = google_map_api_key
  
  circle1 = Circle(x = 'long', y = 'lat', fill_color='#2ECC71',
                     fill_alpha = 0.7, line_alpha = 0, size = 'prob_plot')
  g_prob = plot.add_glyph(source1, circle1)
  hover1 = bkm.HoverTool(renderers=[g_prob],
          tooltips=[('Neighborhood', '@name'),
                                  ('Probability', '@prob')])
  
  circle2 = Circle(x = 'long', y = 'lat', fill_color='blue',
                     fill_alpha = 0.7, line_alpha = 0, size = 6)
  g_start_station = plot.add_glyph(source2, circle2)
  hover2 = bkm.HoverTool(renderers=[g_start_station],
          tooltips=[('Start station', '@name')])
  
    
  circle3 = Circle(x = 'long', y = 'lat', fill_color='red',
                     fill_alpha = 0.2, line_alpha = 0, size = 5)
  g_stations = plot.add_glyph(source3, circle3)
  hover3 = bkm.HoverTool(renderers=[g_stations],
          tooltips=[('Station', '@name')])
  
  
  plot.add_tools(hover1)
  plot.add_tools(hover2)
  plot.add_tools(hover3)
  
  plot.add_tools(PanTool(), WheelZoomTool())
  bokeh_html = file_html(plot, CDN, "tmp")
  #print('df_for_plot:\n', df_for_plot)
  print('return the destination plot...')
  
  return bokeh_html
  #return plot

def station_map(fill_alpha = 0.9, show_neighor = False):
  """
  to return a google map enhanced bokeh html page
  showing all the bike stations
  """
  dname = os.path.dirname(os.path.abspath(__file__))
  project_folder = '/'.join(dname.split('/')[:-1])+'/NYC_bikeshare'
  df_station = pd.read_csv(project_folder + 
                          '/data/NYC_bike_stations_v1.csv')
  ## preparing the source
  source = bkp.ColumnDataSource(data = dict
    (lat = df_station['latitude'], 
     long = df_station['longitude'],
     name = df_station['name'],
     neighbor = df_station['neighborhood'],
    ))
  
  ## ======== preparing the plot =======
  map_options = GMapOptions(lat=40.75, lng=-73.95, 
                            map_type="roadmap", zoom=12)
  plot = GMapPlot(
      x_range=Range1d(), 
      y_range=Range1d(), 
      map_options=map_options,
      api_key = google_map_api_key,
      tools = [PanTool(), WheelZoomTool()],
  )
  # plot.title.text = 'Citibike stations'
  circle = Circle(x = 'long', y = 'lat', fill_color='red',
                 fill_alpha = fill_alpha, line_alpha = 0)
  plot.add_glyph(source, circle)
#  plot.add_tools(PanTool(), WheelZoomTool())
  hover = bkm.HoverTool(tooltips=[('Station name','@name'), 
                                  ('Neighborhood', '@neighbor')])
  plot.add_tools(hover)
  plot.toolbar.active_drag = 'auto'
  plot.toolbar.active_scroll = WheelZoomTool()
  bokeh_html = file_html(plot, CDN, "tmp")
  print('return the station plot...')
  
  return bokeh_html
    
