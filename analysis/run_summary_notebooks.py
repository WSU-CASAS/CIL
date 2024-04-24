# -*- coding: utf-8 -*-
"""
Created on Fri May  5 11:11:31 2023

@author: Wuestney
"""

import papermill as pm
import yaml

with open("../cil_data_params_strict.yml", 'r') as paramfile:
    data_params = yaml.safe_load(paramfile)
FILELOCS = data_params['FILELOCS']

for ptid in FILELOCS.keys():
    print("making summary notebook for ", ptid)
    if ptid == 'test':
        pass
    else:
    
        #pm.execute_notebook('summarize_ignored_sensors.ipynb', f'{ptid}_ignored_sensors_counts.ipynb', parameters = {'ptid':ptid, 'window':5000, 'step':1250})
        pm.execute_notebook('case_triangulation_analysis_sensorcounts_windurations.ipynb', f'{ptid}_triangulation_analysis_sensorcounts_windurations.ipynb', parameters = {'ptid':ptid})
    #pm.execute_notebook('frailty_data.ipynb', f'fr{i}_roomtranignored_W10000_S2500_newcutoffs.ipynb', parameters={'ptid':f'fr{i}', 'stem':'roomtran_ignored_newcutoffs', 'window':10000, 'step':2500})
    #pm.execute_notebook('frailty_data.ipynb', f'fr{i}_inactseqignored_W10000_S2500_newcutoffs.ipynb', parameters={'ptid':f'fr{i}', 'stem':'inactseq_ignored_newcutofs', 'window':10000, 'step':2500})
    #pm.execute_notebook('frailty_data.ipynb', 
                        # f"fr{i}_roomtranall_W10000_S500.ipynb", 
                        # parameters={'ptid':f'fr{i}', 'stem':'roomtran_all', 'window':10000, 'step':500})
    # pm.execute_notebook('frailty_data.ipynb', 
    #                     f"fr{i}_roomtranignored_W10000_S500.ipynb", 
    #                     parameters={'ptid':f'fr{i}', 'stem':'roomtran_ignored', 'window':10000, 'step':500})
    # pm.execute_notebook('frailty_data.ipynb', 
    #                     f"fr{i}_sensorsonlyignored_W10000_S500.ipynb", 
    #                     parameters={'ptid':f'fr{i}', 'stem':'sensorsonly_ignored', 'window':10000, 'step':500, 'multim':False})
    # pm.execute_notebook('frailty_data.ipynb', 
    #                     f"fr{i}_sensorsonlyall_W10000_S500.ipynb", 
    #                     parameters={'ptid':f'fr{i}', 'stem':'sensorsonly_all', 'window':10000, 'step':500, 'multim':False})
    #pm.execute_notebook('frailty_data.ipynb', 
                        # f"fr{i}_roomtranall_W5000_S100.ipynb", 
                        # parameters={'ptid':f'fr{i}', 'stem':'roomtran_all', 'window':5000, 'step':100})
    # pm.execute_notebook('frailty_data.ipynb', 
    #                     f"fr{i}_roomtranignored_W5000_S100.ipynb", 
    #                     parameters={'ptid':f'fr{i}', 'stem':'roomtran_ignored', 'window':5000, 'step':100})
    # pm.execute_notebook('frailty_data.ipynb', 
    #                     f"fr{i}_sensorsonlyignored_W5000_S100.ipynb", 
    #                     parameters={'ptid':f'fr{i}', 'stem':'sensorsonly_ignored', 'window':5000, 'step':100, 'multim':False})
    # pm.execute_notebook('frailty_data.ipynb', 
    #                     f"fr{i}_sensorsonlyall_W5000_S100.ipynb", 
    #                     parameters={'ptid':f'fr{i}', 'stem':'sensorsonly_all', 'window':5000, 'step':100, 'multim':False})