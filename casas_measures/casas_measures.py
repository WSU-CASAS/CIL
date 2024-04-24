"""
Statistical Measures for CASAS data

author: Katherine Wuestney
"""

import datetime
import numpy as np

def timedelta_median(lst):
    lst.sort()
    lstLen = len(lst)
    index = (lstLen) // 2
    if (lstLen % 2)==0:
        return sum([lst[index], lst[index-1]], datetime.timedelta(0))/2
    else:
        return lst[index]

def rolling_window(X: np.ndarray, wsize=1, stride=1):
    # function to match the same functionality as the pandas rolling object for 2d numpy arrays
    
    # move window forward by number of rows in stride
    # wsize is size of window in number of rows

    for i in range(0, X.shape[0], stride):
        end = i
        begin = end - wsize
        if begin < 0:
            subarray = np.nan
        else:
            if X.ndim == 1:
                subarray = X[begin:end]
            elif X.ndim == 2:
                subarray = X[begin:end,:]

        #print('begin', begin, 'end', end, 'window\n', subarray)
      
        #print(begin)
        #print(i)
        yield subarray
      
if __name__ == '__main__':
    X = np.arange(100000000).reshape(5000000, 20)
    print('X', X)
    # test window size even factor of row count
    #rolling_window(X, wsize=5, stride=3)
    
    # test window size not even factor of row count
    #rolling_window(X, wsize=7, stride=3)
    
    for i in rolling_window(X, wsize=10000, stride=1000):
        c = i