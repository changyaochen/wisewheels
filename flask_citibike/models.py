#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  8 20:59:11 2017

@author: changyaochen
"""

import os
import sys
import pickle
import pandas as pd
import numpy as np
#import matplotlib.pyplot as plt
#from sklearn.linear_model import SGDClassifier
#from sklearn.model_selection import train_test_split
#from sklearn.preprocessing import StandardScaler
#from sklearn.model_selection import GridSearchCV
#from sklearn.externals import joblib
from datetime import datetime


def prediction(age=25, start_station='Franklin St & W Broadway',
               TAVG=20, PRCP=0, SNOW=0, gender='Male',
               date='2016/06/01',
               hour=10):

    _debug = False

    dname = os.path.dirname(os.path.abspath(__file__))
    os.chdir(dname)

    data_folder = '/'.join(dname.split('/')[:-1]) + '/NYC_bikeshare/data'
    df_stations = pd.read_csv(data_folder + '/NYC_bike_stations_v7.csv')

    model_name = 'RF.pkl'

    if os.path.exists(model_name):
        print("I am reading ...")
        # clf, input_X, debug_input_X, debug_y = \
        #     joblib.load(os.path.join(dname, model_name))
        clf, input_X, debug_input_X, debug_y = \
            pickle.load(open(os.path.join(dname, model_name), 'rb'))
        print("Model is loaded!")
    else:
        print('There is no model that I can find.')

    num_features = len(input_X)
    print('number of features: ', num_features)

    # features in the input_X:
    #    'start station id', 'age', 'gender', 'hour', 'weekday', 'day of week',
    #    'TAVG', 'PRCP', 'SNOW',
    #    'shortest_dist','total_slots','nearest_3','nearest_5',
    #    'closest_pop',
    #    'closest_income',

    # deal with start station id
    start_station_id = df_stations[df_stations['name'] == start_station]['id'].values
    station_id = 'start station id_' + str(int(start_station_id))
    input_X[station_id] = 1

    # dealing with age
    input_X['age'] = age

    # process the gender
    if gender == 'Male':
        gender_number = 1
    elif gender == 'Female':
        gender_number = 2
    else:
        gender_number = 0
    print('The gender value is : {}'.format(gender_number))
    input_X['gender_' + str(int(gender_number))] = 1

    # process the hour
    input_X['hour'] = hour
    print('The hour is: {}'.format(hour))

    # process the day of the week
    date_right_format = datetime.strptime(date, "%m/%d/%Y")
    print('The date is: {}'.format(date_right_format))
    day_of_week = date_right_format.weekday()
    print('The day of the week is {}.'.format(day_of_week))
    input_X['day of week_' + str(int(day_of_week))] = 1

    # process the weekday
    if day_of_week >= 5:
        input_X['weekday_False'] = 1
    else:
        input_X['weekday_True'] = 1

    # process weather
    input_X['TAVG'] = TAVG
    input_X['PRCP'] = PRCP
    input_X['SNOW'] = SNOW
    print('The weather conditions are: ', TAVG, PRCP, SNOW)

    # process station info
    df_single = df_stations[df_stations['name'] == start_station]
    df_single = df_single.drop(['id', 'name', 'latitude', 'longitude', 'neighborhood',
             'dists_to_other_stations'], axis = 1)
    df_single = df_single.reset_index(drop = True)
    print('shape of df_single (should be 1 by sth): ',
                df_single.shape)

    input_X = input_X.astype('float') # this is important!
    for item in df_single.columns:
        input_X[item] = df_single.ix[0, item]
    # print(input_X)
    # print('start station name is: {}'.format(start_station))

#  input_X['shortest_dist'] = \
#  df_stations[df_stations['name'] == start_station]['shortest_dist'].values
#  input_X['total_slots'] = \
#  df_stations[df_stations['name'] == start_station]['total_slots'].values
#  input_X['nearest_3'] = \
#  df_stations[df_stations['name'] == start_station]['nearest_3'].values
#  input_X['nearest_5'] = \
#  df_stations[df_stations['name'] == start_station]['nearest_5'].values
#
#  ## process the pop and income
#  input_X['closest_pop'] = \
#  df_stations[df_stations['name'] == start_station]['closest_pop'].values
#  input_X['closest_income'] = \
#  df_stations[df_stations['name'] == start_station]['closest_income'].values

    # check for input_X
    print(station_id, input_X[station_id])
    for item in input_X.index:
        if not item.startswith('start station id_'):
            # print('{}: {}'.format(item, input_X[item]))
            pass

    if _debug:
        input_X = debug_input_X
        print('truth is:', debug_y)
    # make the prediction
    y_pred = clf.predict_proba([input_X])

    # build the probility
    temp_dict = {k: v for k, v in zip(clf.classes_, y_pred[0])}
    temp_s = pd.Series(temp_dict)
    temp_s = temp_s.sort_values(ascending = False)
    temp_df = temp_s.reset_index();

    return temp_df

def plot_conf_mat(clf, X_test, y_test, N = 5):
        """
        to get the confusion matrix for multiclass classifier
        """
        import seaborn as sn
        import matplotlib.pyplot as plt
        import pandas as pd
        import numpy as np
        from sklearn.metrics import confusion_matrix

        y_pred = clf.predict(X_test)
        cm = confusion_matrix(y_test, y_pred)
        labels = clf.classes_
        df_cm = pd.DataFrame(cm, index = [i for i in labels],
                                            columns = [i for i in labels])
        plt.figure(figsize = (10,7))
        sn.heatmap(df_cm, annot=False);

        # find the top-N mistakes
        cm_copy = cm.copy()
        np.fill_diagonal(cm_copy, -1)
        for i in range(N):
                max_idx = cm_copy.argmax()
                max_idx = np.unravel_index(max_idx, cm_copy.shape)
                # set that value to -1
                cm_copy[max_idx] = -1
                print('Top {} mistake: truth is {}, but predicting {}'.format(i+1,
                df_cm.index[max_idx[0]],
                df_cm.columns[max_idx[1]]))

def get_proba(clf, X_scaled, y_true = 'Not provided', N = 5):
        """
        to get top-N predictions for multiclass classifier
        given a scaled input
        """
        labels = clf.classes_
        y_pred = clf.predict_proba(X_scaled.reshape(1,-1))
        tmp = [(name, proba) for name, proba in zip(labels, y_pred[0])]
        tmp = sorted(tmp, key = lambda x: x[1], reverse = True)
        print('Truth is {}'.format(y_true))
        print('Predictions are:')
        for i in range(5):
                print(tmp[i])

if __name__ == '__main__':
    temp_s = prediction()
