# -*- coding: utf-8 -*-
"""
Created on Sat Mar 19 11:13:56 2022

@author: Chenyu Lue
"""
import numpy as np
import pandas as pd
import matplotlib.patches as mpatches

import squarify

def treemap(
    axes,
    data,
    *,
    area=None,
    labels=None,
    fill=None,
    color=None,
    levels=None,
    norm_x=100, 
    norm_y=100,
    top=False,
    pad=0.0,
    subgroup_rectprops=None,
    subgroup_textprops=None,
    rectprops=None,
    textprops=None,      
):
    rect_colname = '_rect_'
    
    plot_data = get_plot_data(
        data=data,
        area=area,
        labels=labels, 
        levels=levels
    )
    
    subgroups = get_subgroups(
        plot_data, levels=levels
    )
    
    squarified = squarify_subgroups(
        subgroups,
        norm_x=norm_x,
        norm_y=norm_y,
        levels=levels,
        pad=pad
    )
    
    if rectprops is None:
        rectprops = {}
    if textprops is None:
        textprops = {}
        
    if subgroup_rectprops is None:
        subgroup_rectprops = {}
    else:
        for k in subgroup_rectprops.keys():
            dict_update(subgroup_rectprops[k], rectprops)
            
    if subgroup_textprops is None:
        subgroup_textprops = {}
    else:
        for k in subgroup_textprops.keys():
            dict_update(subgroup_textprops[k], textprops)
    
    for k, v in squarified.items():
        if k in subgroup_rectprops:
            draw_rectangles(axes, v.loc[:, rect_colname], top, norm_y,
                            subgroup_rectprops[k],
                            subgroup_textprops[k])
        else:
            draw_rectangles(axes, v.loc[:, rect_colname], top, norm_y,
                            rectprops, textprops)


def dict_update(dt1, dt2):
    for k, v in dt2.items():
        dt1.setdefault(k, v)  
          
    
def draw_rectangles(axes, sizes, top, height, rectprops, textprops):
    for rect in sizes:
        y0 = height - rect['y'] - rect['dy'] if top else rect['y']
        patch = mpatches.Rectangle(
            (rect['x'], y0), rect['dx'], rect['dy'],
            **rectprops  # Todo: split the kwargs
            )
        axes.add_patch(patch)
        

def squarify_subgroups(
    data,
    norm_x,
    norm_y,
    levels=None,
    pad=0.0,
):
    rect_colname = '_rect_'
    
    if levels is None:
        for k, v in data.items():
            data[k] = squarify_data(v, x=0, y=0, dx=norm_x, dy=norm_y)
        return data
    
    for i, level in enumerate(levels):
        subgroup = data[level]
        if not i: # The root subgroup
            data[level] = squarify_data(subgroup, x=0, y=0, dx=norm_x, dy=norm_y)
        else:   # The non-root subgroup
            pad_left, pad_right, pad_top, pad_bottom = get_surrounding_pad(pad)
            parent_idx = set(idx[:-1] for idx in subgroup.index)
            for parent in parent_idx:
                child_group = subgroup.loc[parent, :]
                parent_rect = data[levels[i-1]].loc[parent, rect_colname]
                x, y, dx, dy = parent_rect['x'], parent_rect['y'], parent_rect['dx'], parent_rect['dy']
                child_group = squarify_data(
                    child_group, 
                    x + (0 if pd.isna(child_group.index[0]) else pad_left), 
                    y + (0 if pd.isna(child_group.index[0]) else pad_bottom), 
                    dx - (0 if pd.isna(child_group.index[0]) else pad_left + pad_right), 
                    dy - (0 if pd.isna(child_group.index[0]) else pad_bottom + pad_top)
                    )
                subgroup.loc[parent, rect_colname] = child_group[rect_colname].values
                
    return data


def get_surrounding_pad(pad):
    if isinstance(pad, (int, float)):
        pad_left, pad_right, pad_top, pad_bottom = pad, pad, pad, pad
    elif isinstance(pad, tuple) and (len(pad) == 2):
        pad_left, pad_top = pad
        pad_right, pad_bottom = pad
    elif isinstance(pad, tuple) and (len(pad) == 4):
        pad_left, pad_right, pad_top, pad_bottom = pad
    else:
        raise ValueError('`pad` can only be a number, or a tuple of two or four numbers.')
    
    return pad_left, pad_right, pad_top, pad_bottom
                

def squarify_data(df, x, y, dx, dy):
    area_colname = '_area_'
    rect_colname = '_rect_'
    # squarify needs the data of sizes to be positive values sorted 
    # in descending order.
    sorted_df = df.sort_values(by=area_colname, ascending=False)
    sorted_df[rect_colname] = squarify.squarify(
        sizes=squarify.normalize_sizes(
            sorted_df[area_colname].values, dx, dy
        ), x=x, y=y, dx=dx, dy=dy
    )
    
    return df.loc[:, df.columns != rect_colname].join(sorted_df.loc[:, rect_colname])
    

def get_subgroups(
    data,
    levels=None
):
    if levels is None:
        return {'_group_': data}
    
    current_level = []
    subgroups = {}
    for level in levels:
        current_level.append(level)
        subgroups[level] = data.groupby(
            by=current_level,
            sort=False,
            dropna=False
            ).sum()
        
    return subgroups


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