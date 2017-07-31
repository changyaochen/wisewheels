#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  8 20:59:11 2017

@author: changyaochen
"""

import os, sys

## bin packing problem
class Shelf(object):
    """ 
    Single shelf object for items that keeps a running sum. 
    """
    def __init__(self, W):
        self.items = []
        self.sum = 0
        self.width = W

    def append(self, item):
        self.items.append(item)
        self.sum += item
        self.space = self.width - self.sum

    def __str__(self):
        """ 
        Printable representation 
        """
        return 'Shelf(sum=%d, items=%s)' % (self.sum, str(self.items))


def pack(widths, W, verbose = True):
    """
    Main packing function with first fit descending. 
    
    Input: 
    widths: list of numbers that represents the widths of all the objects
    W: width of single shelf
    
    Return:
    Total number of shelves needed to allocate all the objects.
    """
    widths = sorted(widths, reverse=True)  # sort the objects with decreasing width
    shelves = []  # initialze the shelves

    for item in widths:
        ## Try to fit item into one shelf
        for shelf in shelves:
            if shelf.sum + item <= shelf.width:
                if verbose: print('Adding', item, 'to', shelf)
                shelf.append(item)
                break
        else:
            ## item didn't fit into shelf, start a new shelf
            if verbose: print('Making new shelf for', item)
            shelf = Shelf(W)
            shelf.append(item)
            shelves.append(shelf)
        
    return len(shelves)
  
## brute-force solution
def permuteUnique(nums):
    """
    To generate only unique permutations
    """
    res = [[]]
    for n in nums:
        res = [l[:i]+[n]+l[i:]
               for l in res
               for i in range((l+[n]).index(n)+1)]
    return res

def pack_brute(widths, W, verbose = 0):
    """
    Main packing function for the brute-force solution
    
    Input: 
    widths: list of numbers that represents the widths of all the objects
    W: width of single shelf
    
    Return:
    Total number of shelves needed to allocate all the objects.
    """
    all_widths = permuteUnique(widths)  # create all the permutations
    min_shelves = len(widths)  
    
    for i, width in enumerate(all_widths):
        if verbose > 0: 
            print('Testing {} of total {} possibilities'
                  .format(i, len(all_widths)))
        shelves = []  # initialze the shelves
        for item in width:
            if len(shelves) > min_shelves:  # no need to continue
                break
            ## Try to fit item into one shelf
            for shelf in shelves:
                if shelf.sum + item <= shelf.width:
                    if verbose > 1: print('Adding', item, 'to', shelf)
                    shelf.append(item)
                    break
            else:
                ## item didn't fit into shelf, start a new shelf
                if verbose > 1: print('Making new shelf for', item)
                shelf = Shelf(W)
                shelf.append(item)
                shelves.append(shelf)
        ## update the min_shelves
        min_shelves = min(len(shelves), min_shelves)
    return min_shelves

  