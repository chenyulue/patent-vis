# -*- coding: utf-8 -*-
"""
Created on Sat Mar 19 11:13:56 2022

@author: Chenyu Lue
"""

import numpy as np
import pandas as pd

def treemap(
    axes,
    data,
    *,
    area=None,
    labels=None,
    fill=None,
    levels=None,
    norm_x=100, 
    norm_y=100,
    top=False,    
):
    pass


def get_plot_data(
    data,
    area=None,
    labels=None,
    levels=None
):
    if levels is None:
        levels = []
        
    area_colname = '_area_'
    label_colname = '_label_'
        
    if isinstance(data, pd.DataFrame):
        if area is None:
            raise TypeError('`area` must be specified when `data` is a DataFrame. '
                            'It can be a `str`, a `number` or a list of `numbers`.')
            
        if isinstance(area, str):
            levels.append(area)
            
            try:
                selected_data = data.loc[:, levels]
            except KeyError:
                raise KeyError('columns specified by `area` or `levels` not included in `data`.')
            
            selected_data.rename(columns={area:area_colname}, inplace=True)
        
        elif isinstance(area, (int, float)):
            try:
                selected_data = data.loc[:, levels]
            except KeyError:
                raise KeyError('columns specified by `levels` not included in `data`.')
            selected_data[area_colname] = area
        
        else:
            try:
                selected_data = data.loc[:, levels]
            except KeyError:
                raise KeyError('columns specified by `levels` not included in `data`.')
            
            area_arr = np.array(area)
            
            if np.issubdtype(area_arr.dtype, np.number):
                try:
                    selected_data[area_colname] = area_arr
                except ValueError:
                    raise ValueError('The length of `area` does not match the length of `data`.')
            else:
                raise ValueError('`area` must be all numbers.')
    
    else:
        data_arr = np.atleast_1d(data)
        if np.issubdtype(data_arr.dtype, np.number):
            selected_data = pd.DataFrame({'_area_': data_arr})
        else:
            raise ValueError('`data` must be all numbers.')
        
    if isinstance(labels, str):
        try:
            selected_data[label_colname] = data.loc[:, labels]
        except KeyError:
            raise KeyError('columns specified by `labels` not included in `data`.')
        except AttributeError:
            raise ValueError('`data` does not support `labels` specified by a string. '
                             'Specify the `labels` by a list of string.')
    elif labels is not None:
        label_arr = np.atleast_1d(labels)
        try:
            selected_data[label_colname] = label_arr
        except ValueError:
            raise ValueError('The length of `labels` does not match the length of `data`.')
        
    return selected_data