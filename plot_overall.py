#!/usr/bin/env python
# coding: utf-8

# ### A Dashboard of Caltech's Diversity

# In[1]:


import numpy as np
import pandas as pd

import bokeh.io
import bokeh.models
import bokeh.palettes
import bokeh.plotting

import holoviews as hv

import bebi103

bokeh.io.output_notebook()
hv.extension('bokeh')

get_ipython().run_line_magic('run', 'bebi103_hv.py')


# In[2]:


df = pd.read_csv("stats.csv", skiprows=1)
df.drop(columns=['Note'], inplace=True)

df = df.melt(id_vars=['Year', 'Level', 'Total'], value_name='count')
df.dropna(axis=0, inplace=True)
df['count'] = df['count'].astype(int)


# In[3]:


def set_group(x):
    if x == 'Total':
        return 'Total'
    elif x in ['Male', 'Female']:
        return 'Gender'
    elif x in ['White', 'Asian', 'URM',
               'International', 'Two or More Races', 'Unknown']:
        return 'Race'
    else:
        raise ValueError('Unknown group `{}`'.format(x))
df['Group'] = df['variable'].apply(set_group) 


# In[4]:


# Combine G and UG
df_all = df.groupby(['Year', 'variable', 'Group'])['count'].sum().reset_index()
df_all['Level'] = 'All'

df = pd.concat([df, df_all], sort=False)


# In[5]:


df['USonly'] = 0
df_us = df.copy()
df_us['USonly'] = 1
df_us = df_us[(df_us['Group'] != 'Gender') & (df_us['variable'] != 'International')]
df = pd.concat([df, df_us], sort=False)


# In[6]:


# Add fractions

df['Total'] = df.groupby(['Group', 'Year', 'Level', 'USonly'])['count'].transform('sum')
df['frac'] = df['count'] / df['Total']


# ### MIT IR colors:
#     Black - #9c0824
#     Hispanic - #bc1118
#     Native Americal - #d63128
#     Native Hawaiian - #de4b3b
#     Asian - #f37263
#     Two or more - #f79085
#     White - #2277b2
#     International - #a3a3a3
#     Unknown - #c3c3c3
# 
# 
#     US Citizen - #4e79a7
#     US Permanent Resident - #a0cbe8
#     International - #59a14f
# 
#     Male - #ff7f0e 
#     Female - #1f77b4

# In[7]:


cmap = {
    'Male': '#ff7f0e',
    'Female': '#1f77b4',
    'White': '#2277b2',
    'Asian': '#f37263',
    'URM': '#bc1118',
    'International': '#a3a3a3',
    'Two or More Races': '#f79085',
    'Unknown': '#c3c3c3'
}


# ### Count of groups vs year

# In[8]:


from bokeh.models.renderers import GlyphRenderer
from bokeh.models import Range1d, LinearAxis

def apply_formatter(plot, element):

    p = plot.state
    
    # create secondary range and axis
    p.extra_y_ranges = {"twiny": Range1d(start=0, end=35)}
    p.add_layout(LinearAxis(y_range_name="twiny"), 'right')

    # set glyph y_range_name to the one we've just created
    glyph = p.select(dict(type=GlyphRenderer))[0]
    glyph.y_range_name = 'twiny'
    return 

#  US-only to selector
df['USonly'] = df['USonly'].astype(str)



# correspond with bar stacking
stack_order = [
    'Male',
    'Female',
    
    'White',
    'International',
    'Unknown',
    
    'Two or More Races',
    'Asian',
    'URM',
]

df_count = df[df['USonly'] == '0'].copy()

p_points = hv.Points(df_count,
    kdims=['Year', 'count'],
    vdims=['variable', 'Level', 'Group']
).redim.values(
    variable=stack_order
).groupby(
    ['Level', 'Group']
).opts(
    show_legend=False,
    color='variable',
    cmap=cmap,
    tools=['hover'],

)

def get_color(keys):
    return [cmap[k] for k in keys]

p_curve = hv.Curve(df_count,
    kdims=['Year', 'variable'],
    vdims=['count', 'Level', 'Group']
).redim.values(
    variable=stack_order
).groupby(
    ['variable', 'Level', 'Group']
).opts(
    color=hv.dim('variable', get_color),
).overlay(
    'variable'
)


# In[9]:


p_all = p_curve * p_points

p_all = p_all.opts(
    xticks=list(range(1900, 2100, 1)),
    ylim=(0, None),
    ylabel='Total',
    labelled=[],
    width=800,
    height=800,
    tools=['hover'],
    legend_offset=(0, 0),
    legend_position='bottom',
    title='',
    fontsize={'legend_title': 0},
    fontscale=1.5,
)

p_all


# ### Percentage of groups vs year

# In[10]:


def flip_y(r):
    if r['variable'] in ['Male', 'International', 'White', 'Unknown']:
        r['frac'] *= -1
    return r

df_bar = df.apply(flip_y, axis=1)

# in order away from axes (for bar plot)
stack_order = [
    'Male',
    'Female',

    'Two or More Races',
    'Asian',
    'URM',

    'White',
    'International',
    'Unknown',
]

p_bars = hv.Bars(
    df_bar,
    kdims=['Year', 'variable'],
    vdims=['frac', 'Level', 'USonly', 'Group']
).redim.values(variable=stack_order
).groupby(
    ['Level', 'USonly', 'Group']
).opts(
    cmap=cmap,
    labelled=[],
    tools=['hover'],
    stacked=True,
    width=800,
    height=400,
    yaxis=None,
    ylim=(None, None),
    title='',
    legend_offset=(0, 0),
    legend_position="bottom",
    show_legend=True,
)


# In[11]:


df_bar = df.apply(flip_y, axis=1)


def format_pct(x):
    return (x * 100).abs().round(1).astype(str) + '%'
df_bar['frac_label'] = format_pct(df_bar['frac'])

def calc_label_position(df):
    """Positions label in the center of the stacked bar
    builtin `y_offset` from holoviews is constant, so it doesn't work
    """
    df_bar['is_pos'] = df_bar['frac'] > 0
    def find_frac_pos(frac):
        return frac.cumsum() - frac/2

    df = (df
        .sort_values(['Year', 'Level', 'USonly', 'Group', 'variable', 'is_pos'])
        .set_index(['Year', 'Level', 'USonly', 'Group', 'variable', 'is_pos'])
        .reindex(stack_order, level='variable')
    )
    df['frac_label_pos'] = (df
        .groupby(level=['Year', 'Level', 'USonly', 'Group', 'is_pos'], sort=False, as_index=False, group_keys=False)['frac']
        .transform(find_frac_pos)
    )
    df = df.reset_index()
    
    df.drop(columns=['is_pos'], inplace=True)
    return df

df_bar = calc_label_position(df_bar)


p_lab = hv.Labels(df_bar,
    kdims=['Year', 'frac_label_pos'],
    vdims=['frac_label', 'variable', 'Level', 'USonly', 'Group']
).groupby(
    ['Level', 'USonly', 'Group']
)

p_bar_lab = (p_bars * p_lab).opts(
    width=800,
    height=800,
    legend_offset=(0, 0),
    legend_position="bottom",
    show_legend=True,
    title='',
    fontscale=1.5,
)

p_bar_lab


# ### Combined views

# In[12]:


p_dash = (p_all + p_bar_lab).opts(
    title=''
)
p_dash


# In[13]:


hv.save(p_dash, 'p_dash.html', fmt='html')


# ### Undergrad vs Grad

# In[14]:


from bokeh.models.renderers import GlyphRenderer
from bokeh.models import Range1d, LinearAxis

def apply_formatter(plot, element):

    p = plot.state
    
    # create secondary range and axis
    p.extra_y_ranges = {"twiny": Range1d(start=0, end=35)}
    p.add_layout(LinearAxis(y_range_name="twiny"), 'right')

    # set glyph y_range_name to the one we've just created
    glyph = p.select(dict(type=GlyphRenderer))[0]
    glyph.y_range_name = 'twiny'
    return 

#  US-only to selector
df['USonly'] = df['USonly'].astype(str)



# correspond with bar stacking
stack_order = [
    'Male',
    'Female',
    
    'White',
    'International',
    'Unknown',
    
    'Two or More Races',
    'Asian',
    'URM',
]

df_count = df[df['USonly'] == '0'].copy()

p_lvl_points = hv.Points(df_count[df_count['Level'] != 'All'],
    kdims=['Year', 'count'],
    vdims=['variable', 'Level', 'Group']
).redim.values(
    variable=stack_order
).groupby(
    ['Group']
).opts(
    show_legend=False,
    color='variable',
    #marker='Level',
    cmap=cmap,
    tools=['hover'],

)

def get_color(keys):
    return [cmap[k] for k in keys]

def get_dash(keys):
    style = []
    for k in keys:
        if k == "UG":
            style.append("solid")
        style.append("dashed")
    return style

p_lvl_curve = hv.Curve(df_count[df_count['Level'] != 'All'],
    kdims=['Year', 'variable'],
    vdims=['count', 'Group', 'Level'],
).redim.values(
    variable=stack_order
).groupby(
    ['variable', 'Group', 'Level']
).opts(
    color=hv.dim('variable', get_color),
    line_dash=hv.dim('Level', get_dash)
).overlay(
    ['variable', 'Level']
)


# In[15]:


p_lvl_points = hv.Points(df_count[df_count['Level'] != 'All'],
    kdims=['Year', 'count'],
    vdims=['variable', 'Level', 'Group']
).redim.values(
    variable=stack_order
).groupby(
    ['variable', 'Level']
).opts(
    show_legend=False,
    color='variable',
    #marker='Level',
    cmap=cmap,
    tools=['hover'],
).overlay(
    'Level'
)

p_lvl_points


# In[16]:


p_lvl_curve = hv.Curve(df_count[df_count['Level'] != 'All'],
    kdims=['Year', 'variable'],
    vdims=['count', 'Group', 'Level'],
).redim.values(
    variable=stack_order
).groupby(
    ['variable', 'Level']
).opts(
   # color=hv.dim('variable', get_color),
    line_dash=hv.dim('Level', get_dash)
).overlay(
    ['Level']
)

p_lvl_count = (p_lvl_points * p_lvl_curve).layout(
    ['variable']
)


# In[17]:


p_lvl_all = p_lvl_curve * p_lvl_points

p_lvl_all = p_lvl_all.opts(
    xticks=list(range(1900, 2100, 1)),
    ylim=(0, None),
    ylabel='Total',
    labelled=[],
    width=800,
    height=800,
    tools=['hover'],
    legend_offset=(0, 0),
    legend_position='bottom',
    title='',
    fontsize={'legend_title': 0},
    fontscale=1.5,
)

p_lvl_all


# In[18]:


p_level_bars = hv.Bars(
    df_bar[df_bar['Level'] != 'All'],
    kdims=['Level', 'variable'],
    vdims=['frac', 'Year', 'USonly', 'Group']
).redim.values(variable=stack_order
).groupby(
    ['Year', 'USonly', 'Group']
).opts(
    cmap=cmap,
    labelled=[],
    tools=['hover'],
    stacked=True,
    width=800,
    height=400,
    yaxis=None,
    ylim=(None, None),
    title='',
    legend_offset=(0, 0),
    legend_position="bottom",
    show_legend=True,
)

p_level_bars


# In[19]:


df_bar = df.apply(flip_y, axis=1)


def format_pct(x):
    return (x * 100).abs().round(1).astype(str) + '%'
df_bar['frac_label'] = format_pct(df_bar['frac'])

def calc_label_position(df):
    """Positions label in the center of the stacked bar
    builtin `y_offset` from holoviews is constant, so it doesn't work
    """
    df_bar['is_pos'] = df_bar['frac'] > 0
    def find_frac_pos(frac):
        return frac.cumsum() - frac/2

    df = (df
        .sort_values(['Year', 'Level', 'USonly', 'Group', 'variable', 'is_pos'])
        .set_index(['Year', 'Level', 'USonly', 'Group', 'variable', 'is_pos'])
        .reindex(stack_order, level='variable')
    )
    df['frac_label_pos'] = (df
        .groupby(level=['Year', 'Level', 'USonly', 'Group', 'is_pos'], sort=False, as_index=False, group_keys=False)['frac']
        .transform(find_frac_pos)
    )
    df = df.reset_index()
    
    df.drop(columns=['is_pos'], inplace=True)
    return df

df_bar = calc_label_position(df_bar)


p_level_lab = hv.Labels(
    df_bar[df_bar['Level'] != 'All'],
    kdims=['Level', 'frac_label_pos'],
    vdims=['frac_label', 'variable', 'Year', 'USonly', 'Group']
).groupby(
    ['Year', 'USonly', 'Group']
)

p_level_bar_lab = (p_level_bars * p_level_lab).opts(
    width=400,
    height=800,
    legend_offset=(0, 0),
    legend_position="right",
    show_legend=True,
    title='',
    fontscale=1.5,
)

p_level_bar_lab


# In[20]:


p_level_dash = (p_lvl_count + p_level_bar_lab).opts(
    title=''
)

hv.save(p_level_dash, 'p_level_dash.html', fmt='html')


# In[21]:


p_level_dash

