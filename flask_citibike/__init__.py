#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  7 11:58:44 2017

@author: changyaochen
"""

from flask import Flask
app = Flask(__name__)
from flask_citibike import views