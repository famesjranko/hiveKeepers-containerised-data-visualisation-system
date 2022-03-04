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

import hivekeeper_helpers as hp

## ===========================
## Get data from database/file 
## ===========================

data_file = "data.csv"
hivekeepers_data = hp.convert_csv_to_df(data_file)

## ========================
## Wrangle Hivekeepers Data
## ========================

hivekeepers_data = hp.clean_data(hivekeepers_data)

# store in local sqllite db
hp.update_sql_db(hivekeepers_data, 'hivekeepers.db', 'hivedata')

# confirm db creation - print current last index value
print(hp.get_last_index_db('hivekeepers.db', 'hivedata', 'id'))

# Build apiary id lists
apiary_list = hp.get_uniques_in_column(hivekeepers_data, 'apiary_id')

# get fft bin names and amplitude values
fft_bins = hp.get_fft_bins(hivekeepers_data)
fft_amplitudes = hivekeepers_data[fft_bins].values

## build new dataframe for 4d chart 
hivekeepers_data_4d = hp.get_4d_data(hivekeepers_data, fft_bins, fft_amplitudes)

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
                                options=[{'label': f"Apiary: {i}", 'value': i} for i in apiary_list],
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
    filtered_hivekeepers_data = hivekeepers_data.loc[hivekeepers_data["apiary_id"] == int(apiaryID)].copy(deep=True)

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
            rangeselector=hp.get_2d_xrangeslider(),
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
            rangeselector=hp.get_2d_xrangeslider(),
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
    filtered_hivekeepers_data = hivekeepers_data.loc[hivekeepers_data["apiary_id"] == int(apiaryID)].copy(deep=True)

    # get bins from drop down selection
    bins = hp.get_bin_group(bin_group, fft_bins)

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
    bins = hp.get_bin_group(bin_group, fft_bins)

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
    app.run_server(host="0.0.0.0", port=8050, debug=False, use_reloader=False)