#### TODO:
####    1. get data from MySql db
####    2. store data locally in SqLite3
####        - sqlalchemy
####    3. version control
####        - requirements.txt ?
####    4. add logging
####
## =======================
## Import needed libraries
## =======================

import os

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# pandas vers==1.4.0
import pandas as pd

import dash
from dash import Dash, dcc, html, Input, Output

import dash_bootstrap_components as dbc

import sqlite3
from sqlalchemy import create_engine # database connection


## ===============
## Helpers section
## ===============

def get_4d_data(df, bins, amplitudes):
    ## --------------------------------
    ## build new dataframe for 4d chart 
    ## takes hivekeepers dataframe, a list of the fft_bins and a list of the fft_amplitude values
    ## returns a dataframe where each index has each fft_bin and fft_amplitude value (total 64 per index)
    ## --------------------------------

    # get timestamp and internal temp data
    internal_temps = df['bme680_internal_temperature']

    # build initial df with timestamp and apiary columns
    data_4d_1 = [df["timestamp"], df["apiary_id"]]
    headers_4d_1 = ["timestamp", "apiary_id"]
    df_4d_1 =  pd.concat(data_4d_1, axis=1, keys=headers_4d_1)

    # add internal temperate column and data - repeat for each bin per timestamp index
    df_4d_2 = df_4d_1.loc[df_4d_1.index.repeat(len(bins))].assign(internal_temp=internal_temps).reset_index(drop=True).copy(deep=True)

    # build lists for converting to dataframe
    amp_list = []
    bin_list = []
    for i in amplitudes:
        n = 0
        for j in i:
            amp_list.append(j)
            bin_list.append(bins[n])
            n += 1

    # convert each list to dataframe
    df_fft_amplitude = pd.DataFrame(amp_list, columns=['fft_amplitude'])
    df_fft_band = pd.DataFrame(bin_list, columns=['fft_band'])

    # final 4d dataframe data
    data_4d = [df_4d_2["timestamp"],
                df_4d_2["apiary_id"],
                df_4d_2["internal_temp"],
                df_fft_amplitude['fft_amplitude'],
                df_fft_band['fft_band']]

    # final 4d dataframe headers
    headers_4d = ["timestamp",
                    'apiary_id',
                    "internal_temperature",
                    "fft_amplitude",
                    "fft_band"]

    # build 4d dataframe
    df_4d_final = pd.concat(data_4d,
                        axis=1,
                        keys=headers_4d)

    return df_4d_final

def get_fft_bins(bin_group):
    ## takes int value representing a selected grouping
    ## returns list of selected fft_bin names
    if bin_group == 1:
        bin_set = fft_bins[0:16]
    elif bin_group == 2:
        bin_set = fft_bins[16:32]
    elif bin_group == 3:
        bin_set = fft_bins[32:48]
    elif bin_group == 4:
        bin_set = fft_bins[48:64]
    elif bin_group == 5:
        bin_set = fft_bins
    
    return bin_set

## ===========================
## Get data from database/file 
## ===========================

data_file = "data.csv"

# read file into dataframe
try :
    hivekkeepers_data = pd.read_csv(data_file)
except FileNotFoundError as error_msg:
    print(f'{data_file} File not found!{error_msg=}, {type(error_msg)=}')
except Exception as error_msg:
    print(f"Unexpected {error_msg=}, {type(error_msg)=}")

## ========================
## Wrangle Hivekeepers Data
## ========================

# drop unnecessary columns
hivekkeepers_data.drop(hivekkeepers_data.columns[[1,3,4,5,6,7,9,10,11,12,13,14,15,16,18,19,20,22,23,24,25,90,91]], axis=1, inplace=True)

# add internal/external temperature delta column - confirm which they want? 
# option1: int - ext                <- non-absolute delta of int and delta
# option2: abs(int - ext)           <- the absolute delta of and ext
# option3: int - abs(int - ext)     <- int - (the absolute difference of int and ext)

#hivekkeepers_data['temp_delta'] = hivekkeepers_data['bme680_internal_temperature'] - hivekkeepers_data['bme680_external_temperature']
hivekkeepers_data['temp_delta'] = abs(hivekkeepers_data['bme680_internal_temperature'] - hivekkeepers_data['bme680_external_temperature'])
#hivekkeepers_data['temp_delta'] = hivekkeepers_data['bme680_internal_temperature'] - abs(hivekkeepers_data['bme680_internal_temperature'] - hivekkeepers_data['bme680_external_temperature'])

# convert timestamp From Unix/Epoch time to Readable date format:
# eg. from 1635249781 to 2021-10-26 12:03:01
hivekkeepers_data['timestamp'] = pd.to_datetime(hivekkeepers_data['timestamp'], unit='s')

# Build apiary id lists
unique_list = []
for id in hivekkeepers_data['apiary_id']:
    # check if exists in unique_list or not
    if id not in unique_list:
        unique_list.append(id)

# get fft bin names and amplitude values
fft_bins = [col for col in hivekkeepers_data if col.startswith('fft_bin')]
fft_amplitudes = hivekkeepers_data[fft_bins].values

## build new dataframe for 4d chart 
hivekeepers_data_4d = get_4d_data(hivekkeepers_data, fft_bins, fft_amplitudes)

## ====================================
## Dash Section server & layout section
## ====================================

## Create dash app and set url basen pathame
app = dash.Dash(__name__, url_base_pathname='/app/')

# server var for gunicorn - not used
server = app.server

# initialise figures
fig1 = go.Figure()
fig2 = go.Figure()
fig3 = go.Figure()
fig4 = go.Figure()

# set 2d chart x-axis range slider
rangeslider_2d_x = dict(buttons=list([dict(count=1,
                                        label="1h",
                                        step="hour",
                                        stepmode="backward"),
                                     dict(count=1,
                                        label="1d",
                                        step="day",
                                        stepmode="backward"),
                                     dict(count=7,
                                        label="1w",
                                        step="day",
                                        stepmode="backward"),
                                     dict(count=1,
                                        label="1m",
                                        step="month",
                                        stepmode="backward"),
                                     dict(count=6,
                                        label="6m",
                                        step="month",
                                        stepmode="backward"),
                                     dict(count=1,
                                        label="YTD",
                                        step="year",
                                        stepmode="todate"),
                                     dict(count=1,
                                        label="1y",
                                        step="year",
                                        stepmode="backward"),
                                     dict(step="all")])) 

app.layout = html.Div(
                children=[
                    # web header, title bar
                    html.Div(
                        children='HiveKeepers Dash App',
                        style = {'font-size': '48px',
                                 'color': '#413F38',
                                 'backgroundColor': '#F0D466',
                                 'font-family': 'Bahnschrift'},),
                    
                    # drop down apiary selector for all graphs
                    html.Div([dcc.Dropdown(
                                id='apiary-selector',
                                options=[{'label': f"Apiary: {i}", 'value': i} for i in unique_list],
                                placeholder="Select an apiaryID",
                                clearable=False,
                                style = {'width': '200px'}),],), 
                
                    # graph 1 div
                    html.Div([dcc.Graph(id='graph1', figure=fig1)]),
    
                    # graph 2 div
                    html.Div([dcc.Graph(id='graph2', figure=fig2)]),
                    
                    # drop down bin selector for graph 3
                    html.Div([dcc.Dropdown(
                                id='bin-selector1',
                                options=[{'label':'fft bins: 0-16',  'value':1},
                                         {'label':'fft bins: 16-32', 'value':2},
                                         {'label':'fft bins: 32-48', 'value':3},
                                         {'label':'fft bins: 48-64', 'value':4},
                                         {'label':'fft bins: all',   'value':5}],
                                value=5,
                                placeholder="Select an FFT bin group",
                                clearable=False,
                                style = {'width': '200px'})],), 
                    
                    # graph 3 div
                    html.Div([dcc.Graph(id='graph3', figure=fig3)]),
                    
                    # drop down bin selector for graph 4
                    html.Div([dcc.Dropdown(
                                id='bin-selector2',
                                options=[{'label':'fft bins: 0-16',  'value':1},
                                         {'label':'fft bins: 16-32', 'value':2},
                                         {'label':'fft bins: 32-48', 'value':3},
                                         {'label':'fft bins: 48-64', 'value':4},
                                         {'label':'fft bins: all',   'value':5}],
                                value=5,
                                placeholder="Select an FFT bin group",
                                clearable=False,
                                style = {'width': '200px'})],),
                    
                    # graph 4 div
                    html.Div([dcc.Graph(id='graph4', figure=fig4)])])

## ================
## Callback Section
## ================

## ===========================
## 2D charts - Line Plot
## chart1 = X-Axis Time,
##          Y-Axis1 Internal Temp,
##          Y-Axis2 External Temp
## 
## chart2 = X-Axis Time,
##          Y-Axis1 Internal Temp,
##          Y-Axis2 Internal to External Detla Temp
## ===========================
@app.callback(
    [Output('graph1', 'figure'),
     Output('graph2', 'figure')],
    [Input("apiary-selector", "value")]
)
def render_graphs(apiaryID):
    
    # PreventUpdate prevents ALL outputs updating
    if apiaryID is None:
        raise dash.exceptions.PreventUpdate

    # get apiary data
    filtered_hivekeepers_data = hivekkeepers_data.loc[hivekkeepers_data["apiary_id"] == int(apiaryID)].copy(deep=True)

    ## ============
    ## build chart1
    ## ============

    # Create figure with secondary y-axis
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])

    # add internal temp trace
    fig1.add_trace(
        go.Scatter(x=list(filtered_hivekeepers_data.timestamp), y=list(filtered_hivekeepers_data.bme680_internal_temperature), name="internal_temperature"), secondary_y=False)

    # add external temp trace
    fig1.add_trace(
        go.Scatter(x=list(filtered_hivekeepers_data.timestamp), y=list(filtered_hivekeepers_data.bme680_external_temperature), name="external_temperature"), secondary_y=True)

    # add axis titles
    fig1.update_layout(
        xaxis_title='date',
        yaxis_title='temp (C)',
        yaxis2_title='temp (C)'
    )
    
    # Set title
    fig1.update_layout(title_text="internal vs external hive temperatures")

    # Add range slider
    fig1.update_layout(
        xaxis=dict(
            rangeselector=rangeslider_2d_x,
            rangeslider=dict(
                visible=True
            ),
            type="date"
        )
    )
    
    ## ============
    ## build chart2
    ## ============
 
    # Create figure with secondary y-axis
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])

    # add internal temp trace
    fig2.add_trace(
        go.Scatter(x=filtered_hivekeepers_data['timestamp'], y=filtered_hivekeepers_data['bme680_internal_temperature'], name="internal_temperature"), secondary_y=False)

    # add delta temp trace
    fig2.add_trace(
        go.Scatter(x=filtered_hivekeepers_data['timestamp'], y=filtered_hivekeepers_data['temp_delta'], name="temp_delta"), secondary_y=True,
    )

    # add axis titles
    fig2.update_layout(
        xaxis_title='date',
        yaxis_title='temp (C)',
        yaxis2_title='temp delta (C)'
    )

    # Set title
    fig2.update_layout(
        title_text="internal vs external hive temperature delta"
    )

    # Add range slider
    fig2.update_layout(
        xaxis=dict(
            rangeselector=rangeslider_2d_x,
            rangeslider=dict(
                visible=True
            ),
            type="date"
        )
    )

    return fig1, fig2

## ===========================
## 3D FFT chart - Surface Plot
## X-Axis Time,
## Y-Axis FFT Bins,
## Z-Axis Amplitude,
## ===========================
@app.callback(
    Output('graph3', 'figure'),
    [Input("bin-selector1", "value"),
     Input("apiary-selector", "value")]
 )
def render_fft_graph(bin_group, apiaryID):

    # PreventUpdate prevents ALL outputs updating
    if bin_group is None or apiaryID is None:
        raise dash.exceptions.PreventUpdate

    # get apiary specific data
    filtered_hivekeepers_data = hivekkeepers_data.loc[hivekkeepers_data["apiary_id"] == int(apiaryID)].copy(deep=True)

    # get bins from drop down selection
    bins = get_fft_bins(bin_group)

    # build chart
    fig3 = go.Figure(data=[go.Surface(x=filtered_hivekeepers_data['timestamp'],
                                      z=filtered_hivekeepers_data[bins].values,
                                      y=bins,
                                      colorbar=dict(title='amplitude'))])

    # set chart title and size
    fig3.update_layout(title='3D FFT chart - Surface Plot (X-Axis Time, Y-Axis FFT Bins, Z-Axis Amplitude)',
                    autosize=True,
                    height=900)

    # set chart axis labels
    fig3.update_layout(scene = dict(
                    xaxis_title = 'timestamp',
                    yaxis_title = 'fft_bands',
                    zaxis_title = 'amplitude'))

    return fig3

## ===========================
## 3D FFT chart - Surface Plot
## X-Axis Time,
## Y-Axis FFT Bins,
## Z-Axis Amplitude,
## C-Axis Internal Temp
## ===========================
@app.callback(
   Output('graph4', 'figure'),
   [Input("bin-selector2", "value"),
    Input("apiary-selector", "value")]
) 
def render_fft_graph(bin_group, apiaryID):

    # PreventUpdate prevents ALL outputs updating
    if bin_group is None or apiaryID is None:
        raise dash.exceptions.PreventUpdate

    # get apiary specific data
    filtered_hivekeepers_data_4d = hivekeepers_data_4d.loc[hivekeepers_data_4d["apiary_id"] == int(apiaryID)].copy(deep=True)
    
    # get bins from drop down selection
    bins = get_fft_bins(bin_group)

    # get subset with selected bin group 
    filtered_hivekeepers_data_4d = filtered_hivekeepers_data_4d.loc[filtered_hivekeepers_data_4d['fft_band'].isin(bins)]

    # set chart data config
    trace1 = go.Scatter3d(x = filtered_hivekeepers_data_4d['timestamp'],
                          y = filtered_hivekeepers_data_4d['fft_band'],
                          z = filtered_hivekeepers_data_4d['fft_amplitude'],
                          mode='markers',
                          marker=dict(size=12,
                                      color=filtered_hivekeepers_data_4d['internal_temperature'],
                                      colorscale='Viridis',
                                      opacity=0.8,
                                      showscale=True,
                                      colorbar=dict(title='internal temp (C)'),))
    
    chart_data = [trace1]

    # set chart axis labels
    layout = go.Layout(
        scene = dict(xaxis = dict(title='timestamp'),
                     yaxis = dict(title='fft_bands'),
                     zaxis = dict(title='amplitude'),),)
    
    # build chart
    fig4 = go.Figure(data=chart_data, layout=layout)

    # set chart title and size
    fig4.update_layout(title='3D FFT chart - Scatter Plot (X-Axis Time, Y-Axis FFT Bins, Z-Axis Amplitude, C-Axis Internal Temp)',
                        autosize=True,
                        height=900)

    return fig4

## =================
## Serve Dash server
## =================

if __name__ == "__main__":
    # set gunincorn through system env var - see docker-compose file
    #app.run_server(host="0.0.0.0", port=8050, debug=False, use_reloader=False)
    app.run_server(host="0.0.0.0", port=os.environ['GUNICORN_PORT'], debug=False, use_reloader=False)