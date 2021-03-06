import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import os
from .signal_processing import butter_bp_data
from .visualization import (
    showCharts
    )
from .detection_icfc import (
    integrate_Hz, 
    identify_scale
    )


def applyOffsetRemove(df):
    """
    Based on Lyons 2005.
    To run a walking bout detection, this function is first used to center the raw signal data.
    This happens by subtracting the average of the signal.
    """
    df.iloc[:,1] = np.subtract(df[1], np.average(df[1]))
    df.iloc[:,2] = np.subtract(df[2], np.average(df[2]))
    df.iloc[:,3] = np.subtract(df[3], np.average(df[3]))
    return df


def applyFilter(df):
    """
    Based on Lyons 2005.
    We eliminate high frequencies. 
    The lower_than variable should not be too low, else it will affect the bout filter.
    """
    fs = 100 # Hz
    lower_than = 17 # Hz
    order = 2
    df = butter_bp_data(df, lower_than, fs, order, 'low')
    return df


def runWalkingBoutDetection(
    data,
    ssd_threshold = 0.1,
    windowSize = 10,
    minimum = 50,
    plot_this = False,
    ):
    """
    Main function for running the walking bout detection.
    It identifies activity in the signal by classifying as activity all the parts of the signal that surpass a given threshold.

    * ssd_threshold: The threshold to be used to identify the activity
    * data: the data we are using to detect activity in
    * windowSize: The windowSize to calculate the combined standard deviation.
    * minimum: The bouts are only considered bouts in case they are a bigger size than this number.
    * plot_this: In case we want to visualize the detection of activity.
    """
    df1 = comb_std_rolling(data, windowSize)
    ranges_ww = calcSegments(windowSize, df1 ,ssd_threshold, minimum)
    if plot_this:
        showCharts(0, ranges_ww, df1, ssd_threshold)
    print("walking bouts detection completed...")
    return ranges_ww


def calcSegments(
    window,
    data_std,
    ssd_threshold,
    minimum = 250,
    ):

    """
    This function provides the ranges that satisfy the
    threshold conditions.
    """
    Ln = len(data_std)
    walking_window = np.zeros(Ln)
    ranges = list()
    start = 0
    end = 0
    contiguous = False
    # Mark the ranges that satisfy a certain condition
    for i in range(0,Ln):
        if (data_std[i] >= ssd_threshold):
            walking_window[i] = 1


    for i in range(0,Ln):
        if (i == Ln - 1) and contiguous:
            end = i - 1
            ranges.append((start,end))
        if walking_window[i] == 1:
            if not contiguous:
                contiguous = True
                start = i
        elif (walking_window[i] == 0 ) and contiguous:
            contiguous = False
            end = i - 1
            ranges.append((start,end))

    # Here we are filtering all the ranges that have
    # less than 50 centiseconds

    for i in range(0,len(ranges)):
        start = ranges[i][0]
        end = ranges[i][1]+1
        len_wb = end - start
        if (len_wb < minimum):
            walking_window[start:end] = [0]*len_wb

    ranges = list()
    start = 0
    end = 0
    contiguous = False
    for i in range(0,Ln):
        if (i == Ln - 1) and contiguous:
            end = i
            ranges.append((start,end))
        if walking_window[i] == 1:
            if not contiguous:
                contiguous = True
                start = i
        elif walking_window[i] == 0 and contiguous:
            contiguous = False
            end = i-1
            ranges.append((start,end))
    return ranges


def comb_std_rolling (data, window):
    """
    This function will perform a rolling window for combined std
    of several axis.
    """

    data_combined1 = data[1].rolling(window).std()
    data_combined2 = data[2].rolling(window).std()
    data_combined3 = data[3].rolling(window).std()
    arr = np.array([
        data_combined1.tolist(),
        data_combined2.tolist(),
        data_combined3.tolist()
        ])
    data_combined = arr.sum(axis = 0)
    data_combined = data_combined[window-1:len(data_combined)]
    return data_combined


# DEPRECATED
def get_trials(data, trials_TS):
    a = 0 #index trial
    b = 0 #index tsInit / tsEnd
    keyAnt = -1
    data_wb_trials = list()
    for key,value in enumerate(data[0]):
        if value > trials_TS.loc[a,b]:
            a = a + 1 if b == 1 else a
            if (b == 1):
                data_wb_trials.append(data[keyAnt:key+1].reset_index(drop=True))
            b = 0 if b == 1 else 1
            keyAnt = key
            if a >= len(trials_TS):
                break
    return data_wb_trials
