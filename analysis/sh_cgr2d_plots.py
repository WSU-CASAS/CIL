#!/usr/bin/env python
# coding: utf-8


import pathlib
import yaml
import pyusm

import pandas as pd
import numpy as np

from scipy.stats import norm
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from matplotlib.dates import MO
from matplotlib import rc
import seaborn as sn

# set which code chunk to run 
fixedwin = True
weeklywin = True
dailywin = False

#rc('font', **{'family':'Times New Roman'})
rc('font',**{'family':'sans-serif','sans-serif':['Calibri']})

daysints = {'Monday':0, 'Tuesday':1, 'Wednesday':2, 'Thursday':3, 'Friday':4, 'Saturday':5, 'Sunday':6}

def rw(X: np.ndarray, wsize=1, stride=1):
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
      

# class cgr_plot:
#     def __init__(self, coords, coord_dict):
#         #self.fig = fig
#         #self.ax = ax
#         self.verts = len(coord_dict)
#         self.points = len(coords)
#         self.coord_dict = coord_dict
#         #get vertex coordinates
#         sensors, vertices = tuple(zip(*coord_dict.items()))
#         x_vals, y_vals = tuple((zip(*vertices)))
#         x_vals = np.array(x_vals)
#         y_vals = np.array(y_vals)
#         self.x_vals = x_vals
#         self.y_vals = y_vals
#         vert_coords = np.column_stack((x_vals, y_vals))
#         xmin = x_vals.min() - 0.2
#         xmax = x_vals.max() + 0.2
#         ymin = y_vals.min() - 0.2
#         ymax = y_vals.max() + 0.2
#         self.xlims = (xmin, xmax)
#         self.ylims = (ymin, ymax)
#         #initiate figure instance
#         self.fig, self.ax = plt.subplots(figsize=(10,10))
#         self.ax.set(xlim=self.xlims, ylim=self.ylims)
        
#         self.coords = coords
        
#     def plot(self):
#         x, y = zip(*self.coords)
#         self.ax.scatter(self.x_vals, self.y_vals, c='b', s=1)
#         #self.ax.legend()
#         for i, xy in self.coord_dict.items():
#             if xy[0] < 0 and xy[1] > 0:
#                 self.ax.annotate(f'{i}', xy, xycoords='data',xytext=(-70,4), textcoords='offset points', size=10)
#             elif xy[0] < 0 and xy[1] < 0:
#                 if len(i) < 15:
#                     self.ax.annotate(f'{i}', xy, xycoords='data',xytext=(-70,-4), textcoords='offset points', size=10)
#                 else:
#                     self.ax.annotate(f'{i}', xy, xycoords='data',xytext=(-110,-4), textcoords='offset points', size=10)
#             elif xy[0] > 0 and xy[1] < 0:
#                 self.ax.annotate(f'{i}', xy, xycoords='data',xytext=(4,-10), textcoords='offset points', size=10)
#             else:
#                 self.ax.annotate(f'{i}', xy, xycoords='data', xytext=(4,4), textcoords='offset points', size=10)
#         self.ax.scatter(x, y, s=1, c='g')
#         # c = self.ax.hexbin(x, y, gridsize=120, cmap='cool', linewidths=1, mincnt=1)
#         # cb = self.fig.colorbar(c, label='count in bin')
#         return
        
#     def savefig(self, filename, **kwargs):
#         self.fig.savefig(filename, **kwargs)
#         return

# #     def init_frame(self):
# #         self.ax.cla()
# #         self.ax.set(xlim=self.xlims, ylim=self.ylims)
# #         self.ax.scatter(x=0, y=0.25, s=1, c='r', label='inital point')
# #         self.ax.scatter(self.x_vals, self.y_vals, c='b', label='vertices')
# #         self.ax.legend()
# #         for i, xy in enumerate(zip(self.x_vals, self.y_vals)):
# #             self.ax.annotate(f'{i}', xy, xycoords='data', xytext=(4,4), textcoords='offset points')
# #         return
    
# #     def animation(self, i):
# #         i_from = i * self.chunks
# #         # are we on the last frame?
# #         if i_from + self.chunks > len(self.coords) - 1:
# #             i_to = len(self.coords) - 1
# #         else:
# #             i_to = i_from + self.chunks
# #         rows = self.coords[i_from:i_to]
# #         x, y = zip(*rows)
# #         self.ax.scatter(x, y, s=1, c='g')
# #         return
    
# #     def animate(self, chunks=10):
# #         self.chunks = chunks
# #         self.frame_chunks = self.points // self.chunks
# #         self.ani = FuncAnimation(self.fig, self.animation, frames=self.frame_chunks, init_func=self.init_frame, interval=0.5, repeat=True, blit=True)
# #         plt.show()
        
# #     def movie(self):
# #         movie1 = self.ani.to_jshtml()
# #         return movie1
    
# #     def pause(self):
# #         self.ani.pause()
# #         return


# In[13]:


def list_of_included_dfs(ptid, inverse_coded):
    included = []
    for timeframe in INCLUDE_TIMEFRAMES[ptid]:
        included.append(inverse_coded.loc[timeframe[0]:timeframe[1]])
    #inverse_coded = inverse_coded.loc[inverse_coded.index.difference(inverse_coded.index[inverse_coded.index.slice_indexer(timeframe[0], timeframe[1])])]
    #ignored_seg = inverse_coded[~inverse_coded.loc[timeframe[0]:timeframe[1]]]
    #print(included)
    return included

def included_dfs(ptid, inverse_coded):
    included = []
    for timeframe in INCLUDE_TIMEFRAMES[ptid]:
        included.append(inverse_coded.loc[timeframe[0]:timeframe[1]])
    #inverse_coded = inverse_coded.loc[inverse_coded.index.difference(inverse_coded.index[inverse_coded.index.slice_indexer(timeframe[0], timeframe[1])])]
    #ignored_seg = inverse_coded[~inverse_coded.loc[timeframe[0]:timeframe[1]]]
    #print(included)
    included_df = pd.concat(included)
    return included_df

# this yaml file is copy of fr_data_params_strict
with open("../cil_data_params_corrected.yml", 'r') as paramfile:
    data_params = yaml.safe_load(paramfile)
IGNORE_TIMEFRAMES = data_params['IGNORE_TIMEFRAMES']
INCLUDE_TIMEFRAMES = data_params['INCLUDE_TIMEFRAMES']
BIWEEKLYWINDOW = data_params['BIWEEKLYWINDOW']
FILELOCS = data_params['FILELOCS']
HOUSEKEEPING = data_params['HOUSEKEEPING']

for ptid in FILELOCS.keys():
    #ptid = 'tm015'
    print("making CGR plots for ", ptid)
    if ptid == 'test':
         continue
    window = BIWEEKLYWINDOW[ptid][0]
    print(window)
    step = window // 4
    
    
    # In[16]:
    
    
    fname = f'{ptid}_utc2pst_df_ONsensorsonly_ignored.pkl'
    fdir = pathlib.Path(r"C:\Users\Wuestney\Documents\GitHub\casas_measures\data")
    fpath = fdir / fname
    sh_df = pd.read_pickle(fpath)
    #remove
    included_df = included_dfs(ptid, sh_df)
    # if HOUSEKEEPING[ptid][0]:
    #     included_df = included_df[included_df.index.dayofweek != daysints[HOUSEKEEPING[ptid][0]]]
    
    cgr = pyusm.USM.cgr2d(included_df['Sensor'].to_numpy())
    
    
    coords_df = pd.DataFrame(cgr.fw, index=included_df.index)
    coords_df
    
    
    # In[23]:
    
    
    included_coords = list_of_included_dfs(ptid, coords_df)
    
    
    # In[41]:
    
    
    cwd = pathlib.Path.cwd()
    outdir = cwd / f"plots/{ptid}/"
    outdir.mkdir(parents=True, exist_ok=True)
    outfile = outdir / f"{ptid}_empty_plots.txt"
    if fixedwin:
        with open(outfile, 'w') as log:
            log.write(f"Index values for empty cgrs for {ptid} \n")
            for df in included_coords:
                window_cgrs = []
                window_index = df.index[:: step]
                coords = df.to_numpy()
                for win in rw(coords, window, step):
                    if win is np.nan:
                        window_cgrs.append(None)
                    else:
                        window_cgrs.append(pyusm.cgr_plot(win, cgr.coord_dict))
        
                for i, cgrp in zip(window_index, window_cgrs):
                    print(i)
                    if cgrp is None:
                        log.write(f"{i} \n")
                    else:
                        cgrp.plot()
                        cgrp.savefig(f"plots/{ptid}/{ptid}_cgrpoints_{i.strftime('%Y-%m-%dT%H-%M-%S.%f')}.png", dpi=1200)

                        # Clear the current axes.
                        plt.cla() 
                        # Clear the current figure.
                        plt.clf() 
                        # Closes all the figure windows.
                        plt.close('all')   
                        plt.close(cgrp.fig)
