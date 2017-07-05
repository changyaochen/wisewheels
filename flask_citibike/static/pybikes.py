#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  2 13:45:18 2017
This is my attempt to scrap live feeds from all bikeshare programs
it is largely based on:
https://www.citybik.es

@author: changyaochen
"""

import json, requests, os, time, re
import pandas as pd
_debug = True

dname = os.path.dirname(os.path.abspath(__file__))
os.chdir(dname)

all_networks_url = 'https://api.citybik.es/v2/networks'
# get all the networks (cities)
all_networks = requests.get(all_networks_url).json()['networks']
print('total number of cities:', len(all_networks))

if not os.path.exists('all_networks'):
  os.mkdir('all_networks')
os.chdir('./all_networks')

# start scraping each of the networks
round_count = 0
network_id_blk_list = [
    'nextbike-offenbach-am-main'
    ]

while round_count < 100:
  for network in all_networks:
    print(network['id'])
    if network['id'] in network_id_blk_list:
      continue
    # let's make the preambles
    network_city = network['location']['city']
    network_city = network_city.replace('/','')
    network_city = network_city.replace(' ','')
    network_country = network['location']['country']
    # save network status to individual dataframe
    csv_name = network_city.split(',')[0] + '_' + network_country + '.csv'
    if os.path.exists(csv_name):
      df_network = pd.read_csv(csv_name, encoding = 'utf-8')
    else:
      df_network = pd.DataFrame()
    
    # make the indiviual api url for each network
    network_url = 'https://api.citybik.es/v2/networks/' + network['id']
    response = requests.get(network_url).json()['network'] # response is a dict  
    if 'stations' not in response:  # in case the response is not correct
      continue
    all_stations = response['stations']
    # process the station status in the network / city
    for station in all_stations:
      if not station['empty_slots']:
        station['empty_slots'] = 0
      if not station['free_bikes']:
        station['free_bikes'] = 0
      station['total_slots'] = station['empty_slots'] + station['free_bikes']
      # write to the dafaframe
      df_network = df_network.append(station, ignore_index = True)
    
    # done with this network / city, save the data
    df_network.to_csv(csv_name, index = False, encoding = 'utf-8')  
        
  round_count += 1  
  print('waiting...')
  time.sleep(2*60)
  
os.chdir('..')