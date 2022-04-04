# -*- coding: utf-8 -*-
"""
Created on Sat Mar 19 11:13:56 2022

@author: Chenyu Lue
"""
import itertools

import numpy as np
import pandas as pd
import matplotlib.patches as mpatches
from matplotlib import cm
import matplotlib.colors as mcolors

import squarify

from . import autofit

def treemap(
    axes,
    data,
    *,
    area=None,
    labels=None,
    fill=None,
    cmap=None,
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
    plot_data = get_plot_data(
        data=data,
        area=area,
        labels=labels,
        fill=fill, 
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
    if subgroup_textprops is None:
        subgroup_textprops = {}
    
    axes.set_xlim([0, norm_x])
    axes.set_ylim([0, norm_y])
    
    for k, subgroup in squarified.items():
        if k in subgroup_rectprops:
            draw_subgroup(axes, subgroup, top, norm_y, cmap, 
                          subgroup_rectprops[k], subgroup_textprops[k], False)
        elif (k == levels[-1]) or (k not in levels):
            draw_subgroup(axes, subgroup, top, norm_y, cmap, 
                          rectprops, textprops, True)


# def dict_update(dt1, dt2):
#     for k, v in dt2.items():
#         dt1.setdefault(k, v)  
          
    
def draw_subgroup(
    axes, 
    subgroup, 
    top, 
    norm_y, 
    cmap,
    rectprops, 
    textprops, 
    is_leaf
    ):
    if is_leaf and ('_fill_' in subgroup.columns):
        colors = get_colormap(cmap, subgroup['_fill_'])
        fill_is_numeric = np.issubdtype(subgroup.loc[:, '_fill_'].dtype, np.number)
        if fill_is_numeric: 
            max_value = subgroup['_fill_'].max()
            min_value = subgroup['_fill_'].min()
            norm = mcolors.Normalize(vmin=min_value, vmax=max_value)
        
    for idx in subgroup.index:
        if is_leaf and ('_fill_' in subgroup.columns) and fill_is_numeric:
            rectprops['color'] = colors(norm(subgroup.loc[idx, '_fill_']))
        elif is_leaf and ('_fill_' in subgroup.columns):
            #print(idx)
            rectprops['color'] = colors[subgroup.loc[idx, '_fill_']]
        
        rect = subgroup.loc[idx, '_rect_']
        y0 = norm_y - rect['y'] - rect['dy'] if top else rect['y']
        #print(f'y0={y0}, height={height}')
        patch = mpatches.Rectangle(
            (rect['x'], y0), rect['dx'], rect['dy'],
            **rectprops  # Todo: split the kwargs
            )
        axes.add_patch(patch)
        
        if textprops and ('_label_' in subgroup.columns):
            extra = ['grow', 'wrap', 'xmax', 'ymax', 'place']
            grow = textprops.get('grow', False)
            wrap = textprops.get('wrap', False)
            xmax = textprops.get('xmax', 1)
            ymax = textprops.get('ymax', 1)
            place = textprops.get('place', 'center')
            xa0, ya0, width, height = rect['x'], y0, rect['dx'], rect['dy']
            (x, y, ha, va) = get_position(xa0, ya0, width, height, place)
            text_kwargs = {k:v for k, v in textprops.items() if k not in extra}
            #print(text_kwargs)
            if is_leaf:
                txtobj = axes.text(x, y, subgroup.loc[idx, '_label_'], 
                          ha=ha, va=va, **text_kwargs)
            else:
                subgroup_label = [lbl for lbl in idx if lbl is not None][-1]
                txtobj = axes.text(x, y, subgroup_label, 
                                   ha=ha, va=va, **text_kwargs)
            padx = xmax == 1
            pady = ymax == 1
            autofit.text_with_autofit(txtobj, xmax*width, ymax*height, 
                                      pad=(padx, pady), wrap=wrap, grow=grow)
                       

def get_position(x, y, dx, dy, pos):
    x_pos = {'center': x + dx/2, 'left': x, 'right': x + dx}
    y_pos = {'center': y + dy/2, 'bottom': y, 'top': y + dy}
    name_dict = {'b':'bottom', 'c':'center', 't':'top', 'l':'left', 'r':'right'}
    try:
        if (pos == 'c') or (pos == 'center') or (pos == 'centre'):
            return (x_pos.get(pos, x_pos['center']), y_pos.get(pos, y_pos['center']),
                    'center', 'center')
        elif len(pos) == 2:
            ytxt, xtxt = pos[0], pos[1]
            return (x_pos[name_dict[xtxt]], y_pos[name_dict[ytxt]],
                    name_dict[xtxt], name_dict[ytxt])
        else:
            ytxt, xtxt = pos.split()
            ytxt = 'center' if ytxt == 'centre' else ytxt
            xtxt = 'center' if xtxt == 'centre' else xtxt
            return (x_pos[xtxt], y_pos[ytxt],
                    xtxt, ytxt)
    except KeyError:
        raise ValueError('Invalid position. Available positions are:\n- "center" (British spelling accepted), '
                        '"center left", "center right", \n- "bottom left", "bottom center", "bottom right", '
                        '\n- "top left", "top center", "top right".')
        

def get_colormap(cmap, fill_col):
    if np.issubdtype(fill_col.dtype, np.number):
        colors = cmap if isinstance(cmap, mcolors.Colormap) else cm.get_cmap(cmap)
    else:
        if cmap is not None:
            colors = cmap if isinstance(cmap, list) else [cmap]
        else:
            colors = cm.get_cmap(cmap, fill_col.nunique()).colors
        colors = dict(zip(fill_col.unique(), itertools.cycle(colors)))
        
    return colors
        
        

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
    
    agg_fun = {'_area_': 'sum'}
    if '_label_' in data.columns:
        agg_fun['_label_'] = 'first'
    if '_fill_' in data.columns:
        agg_fun['_fill_'] = 'first'
        
    current_level = []
    subgroups = {}
    for level in levels:
        current_level.append(level)
        subgroups[level] = data.groupby(
            by=current_level,
            sort=False,
            dropna=False
            ).agg(agg_fun)
        
    return subgroups


def get_plot_data(
    data,
    area=None,
    labels=None,
    fill=None,
    levels=None
):
    if levels is None:
        levels = []
        
    area_colname = '_area_'
    label_colname = '_label_'
    fill_colname = '_fill_'
        
    if isinstance(data, pd.DataFrame):
        if area is None:
            raise TypeError('`area` must be specified when `data` is a DataFrame. '
                            'It can be a `str`, a `number` or a list of `numbers`.')
            
        if isinstance(area, str):       
            try:
                selected_data = data.loc[:, levels + [area]]
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
            raise KeyError('column specified by `labels` not included in `data`.')
        except AttributeError:
            raise ValueError('`data` does not support `labels` specified by a string. '
                             'Specify the `labels` by a list of string.')
    elif labels is not None:
        label_arr = np.atleast_1d(labels)
        try:
            selected_data[label_colname] = label_arr
        except ValueError:
            raise ValueError('The length of `labels` does not match the length of `data`.')
        
    if isinstance(fill, str):
        try:
            selected_data[fill_colname] = data.loc[:, fill]
        except KeyError:
            raise KeyError('column specified by `fill` not included in `data`.')
        except AttributeError:
            raise ValueError('`data` does not support `fill` specified by a string. '
                             'Specify the `fill` by a list.')
    elif fill is not None:
        fill_arr = np.atleast_1d(fill)
        try:
            selected_data[fill_colname] = fill_arr
        except ValueError:
            raise ValueError('The length of `fill` does not match the length of `data`.')
        
    return selected_data