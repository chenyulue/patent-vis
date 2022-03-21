# -*- coding: utf-8 -*-
"""
Created on Sat Mar 19 11:13:56 2022

@author: Chenyu Lue
"""

import itertools
import functools

from matplotlib.container import Container
import matplotlib.axes
from matplotlib import cm
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches

import pandas.api.types as ptypes

import squarify

from mpl.extension.extension import extension

import mpl.extension.autofit



class TreemapContainer(Container):
    '''
    Container for the artist of treemap plots (e.g. created by `.Axes.bar`)

    The container contains a tuple of the *patches* themselves as well as some
    additoinal attributes.

    Attributes
    ----------
    patches: list of list of :class:`~matplotlib.patches.Rectangle`
        The artists of the rectangles corresponding to different levels
    
    datavalues: None or array-like
        The underlying data values corresponding to the bars

    levels: int
        The treemap levels
    '''
    def __init__(self, patches, labels, *, datavalues=None, colornorm=None,**kwargs):
        self.patches = patches
        self.labels = labels
        self.datavalues = datavalues
        self.colornorm = colornorm
        super().__init__(patches, **kwargs)


def _get_bool_index(data, levels, elems):
    return functools.reduce(
        lambda x, y: x & y, 
        [data[col]==val for col, val in zip(levels, elems)])


def _calc_position(x, y, dx, dy, pos):
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



@extension(matplotlib.axes.Axes)
class AxesExt:
    def treemap(self, data, area, norm_x, norm_y, levels, *, 
                parent_border=None, parent_label=None,
                fill=None, color=None, cmap=None, 
                label=False, top=False, show_rect=False,
                rectprops=None, labelprops=None, 
                ):
        if isinstance(area, str):
            selected_data = data[levels + [area]]
        elif isinstance(area, int) or isinstance(area, float):
            selected_data = data.loc[:, levels]
            selected_data['area'] = area
        # Grouped_levels is of the form of a tuple showing the level path,
        # such as ('class', 'sub-class', 'sub-sub-class', ...). 
        # The last element represents the current level, and others are its parent
        # and ancestors.
        grouped_levels = [levels[:i] for i in range(1,len(levels)+1)]
        groups = {}
        for group in grouped_levels:
            groups[tuple(group)] = selected_data.groupby(
                by=group, sort=False, dropna=False
            ).sum().iloc[:, -1]

        rects = {}
        for level, group in groups.items():
            parent = level[:-1]
            # squarify needs the data of sizes to be positive values sorted 
            # in descending order.
            sorted_group = group.sort_values(ascending=False)
            if not parent:      # A root node
                subrects = squarify.squarify(
                    sizes=squarify.normalize_sizes(
                        sorted_group.values, norm_x, norm_y
                    ), x=0, y=0, dx=norm_x, dy=norm_y
                )
                # Every rectangle has a key corresponding to its label path of a tuple.
                rects[level] = dict(zip(
                    [tuple([label]) for label in sorted_group.index], 
                    subrects
                    ))
            else:
                rects[level] = {}
                for parent_key, parent_rect in rects[tuple(parent)].items():
                    # Sub-groups are plotted in the range of their parent.
                    width = parent_rect['dx']
                    height = parent_rect['dy']
                    x = parent_rect['x']
                    y = parent_rect['y']
                    # Split the parent rectangle with its children nodes.
                    sorted_parent_group = group.sort_index()    # For better performance
                    sorted_group = sorted_parent_group[parent_key].sort_values(ascending=False)
                    subrects = squarify.squarify(
                        sizes=squarify.normalize_sizes(
                            sorted_group.values, width, height
                        ), x=x, y=y, dx=width, dy=height
                    )
                    idx = [parent_key + (idx,) for idx in sorted_group.index]
                    rects[level].update(dict(zip(idx, subrects)))

        # Record the drawed patches and labels
        drawed_patches = {}
        drawed_labels = {}
        norm = None
        
        # By default all the rectangles are seprated by white lines.
        if rectprops is None:
            rectprops = {}
        if ('ec' not in rectprops) and ('edgecolor' not in rectprops):
            rectprops['ec'] = 'w'
        if ('lw' not in rectprops) and ('linewidth' not in rectprops):
            rectprops['lw'] = 1
            
        if labelprops is None:
            labelprops = {}
            
        
        # Only when fill is specified does color or cmap takes effect.
        if (fill is not None):
            numeric_fill_column = ptypes.is_numeric_dtype(data[fill].dtype)
            # Numeric column uses the sequential colormap, which is specified 
            # by the parameter of cmap
            if numeric_fill_column:
                sequential_colors = cmap if isinstance(cmap, mcolors.Colormap) else cm.get_cmap(cmap)
            # Categorical column uses the qualitative colormap, which can be 
            # specified by cmap name and by the parameter of color
            else:
                if color is not None:
                    colors = color if isinstance(color, list) else [color]
                else:
                    colors = cm.get_cmap(cmap, data[fill].nunique()).colors
                categorical_colors = dict(zip(data[fill].unique(), itertools.cycle(colors)))
        
        self.set_xlim([0, norm_x])
        self.set_ylim([0, norm_y])
        
        if parent_border is not None:
            parent_border_dict = {tuple(l): v for l, v in zip(grouped_levels[:-1], parent_border)}
            
        if parent_label is not None:
            parent_label_dict = {tuple(l): v for l, v in zip(grouped_levels[:-1], parent_label)}
            
        
        for i, displayed_levels in enumerate(reversed(grouped_levels)):
            # By default only the leaf levels are plotted.
            level_to_plot = tuple(displayed_levels)
            
            if i > 0:
                rectprops['fill'] = False
                borderprops = parent_border_dict.get(level_to_plot, {}) if parent_border is not None else {}
                rectprops.update(borderprops)
                
                textprops = parent_label_dict.get(level_to_plot, {}) if parent_label is not None else {}
                labelprops.update(textprops)
                
            wrap = labelprops.setdefault('wrap', False)
            grow = labelprops.setdefault('grow', False)
            max_labelsize = labelprops.setdefault('max_labelsize', None)
            min_labelsize = labelprops.setdefault('min_labelsize', 1)
            adjust = labelprops.setdefault('adjust', 1)
                
            for rect_label, subrects in rects[level_to_plot].items():
                if (fill is not None):
                    if (not numeric_fill_column):
                        fill_label = set(rect_label).intersection(set(data[fill].unique()))
                        if fill_label:
                            rect_color = categorical_colors[fill_label.pop()]
                        else:
                            idx_bool = _get_bool_index(data, displayed_levels, rect_label)
                            rect_color = categorical_colors[data.loc[idx_bool, fill].values[0]]
                    else:
                        max_value = data[fill].max()
                        min_value = data[fill].min()
                        norm = mcolors.Normalize(vmin=min_value, vmax=max_value)
                        idx_bool = _get_bool_index(data, displayed_levels, rect_label)
                        elem = data.loc[idx_bool, fill].values[0]
                        rect_color = sequential_colors(norm(elem))
                    rectprops.update({'fc':rect_color})
                # If top is true, then flip the rectangle upside down.
                y_original = norm_y - subrects['y'] - subrects['dy'] if top else subrects['y']
                rectangle = mpatches.Rectangle(
                    (subrects['x'], y_original), subrects['dx'], subrects['dy'], 
                    **rectprops)
                self.add_patch(rectangle)
    
                drawed_patches[rect_label] = rectangle
    
                # Add labels
                if label:
                    labelprops.setdefault('place', 'center')
                    (x, y, ha, va) = _calc_position(subrects['x'], 
                                                    y_original, 
                                                    subrects['dx'], 
                                                    subrects['dy'], 
                                                    labelprops['place'])
                    labelprops['ha'] = ha
                    labelprops['va'] = va
                    extra_keys = ['place', 'grow', 'wrap', 'adjust', 
                                  'max_labelsize', 'min_labelsize']
                    annotate_kwargs = {k:v for k, v in labelprops.items() if k not in extra_keys}
                    selected_label = [lbl for lbl in rect_label if lbl is not None][-1]
                    if not grow:
                        annotation = self.annotate(
                            selected_label, xy=(x,y),
                            **annotate_kwargs
                            )
                        drawed_labels[rect_label] = annotation
                        annotation.set_zorder(10-i)
                    else:
                        annotation = self.annotate_with_autofit(
                            selected_label, xy=(x,y),
                            width=subrects['dx'], height=subrects['dy'],
                            show_rect=show_rect, wrap=wrap, 
                            min_size=min_labelsize, adjust=adjust,
                            **annotate_kwargs
                            )
                        if i == 0 and max_labelsize is not None:
                            fontsize = annotation.get_fontsize()
                            fontsize_limit = fontsize if fontsize < max_labelsize else max_labelsize
                            annotation.set_fontsize(fontsize_limit)
                        drawed_labels[rect_label] = annotation
                        annotation.set_zorder(10-i)

        return TreemapContainer(drawed_patches, drawed_labels, colornorm=norm)
    

if __name__ == '__main__':
    import pandas as pd
    import matplotlib.pyplot as plt
    import numpy as np
    
    Blues = cm.get_cmap('PuBu_r')
    blues = mcolors.ListedColormap(Blues(np.linspace(0, 1, 256))[:114])
    
    data = pd.read_csv('./data/G20.csv')
    fig, ax = plt.subplots()
    treemap = ax.treemap(data, area=1, 
                         levels=['hemisphere','region','econ_classification','country'], label=True,
                         norm_x=100, norm_y=100, 
                         #cmap=blues, fill='hdi',
                         labelprops={'grow': True, 
                                     'wrap': True,
                                     'max_labelsize': 15,
                                     'adjust': 1.03,
                                     'place':'center', 
                                     'c':'w', 
                                     'fontstyle':'italic', 
                                     'fontfamily':'Serif'
                                     },
                         parent_border=[{'lw':3, 'ec':'r'}, 
                                        {'lw':2, 'ec':'w'},
                                        {'lw':1, 'ec':'b'}],
                         parent_label=[{'c':'r', 'alpha':0.5, 
                                        'place':'center',
                                        'wrap':False}, 
                                       {'c':'w', 'alpha':0.5, 
                                        'place':'bottom center',
                                        'fontstyle':'italic',
                                        #'max_labelsize':20,
                                        'wrap':False},
                                       {'place':'top center',
                                        'c': 'b', 'alpha':0.5,
                                        'wrap':False}],
                         rectprops={'clip_on':False, 'fc':'grey'}
                         )
    #plt.colorbar(cm.ScalarMappable(treemap.colornorm, cmap=blues), ax=ax)
    ax.axis('off')
    plt.show()

