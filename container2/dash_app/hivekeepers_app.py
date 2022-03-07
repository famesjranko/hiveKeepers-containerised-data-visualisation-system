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

import subprocess

import sqlite3
from sqlalchemy import create_engine # database connection

import hivekeepers_helpers as hp

from datetime import date

import copy

## ===========================
## Get data from database/file
## ===========================

data_file = 'data.csv'
hivekeepers_data = hp.convert_csv_to_df(data_file)

## ========================
## Wrangle Hivekeepers Data
## ========================

# drop unneeded columns, and add interna/external temp delta column
hivekeepers_data = hp.clean_data(hivekeepers_data)

# confirm db creation - print current last index value
#print(hp.get_last_index_db('hivekeepers.db', 'hivedata', 'id'))

# Build apiary id lists
apiary_list = hivekeepers_data['apiary_id'].unique()

# get fft bin names and amplitude values
fft_bins = hp.get_fft_bins(hivekeepers_data)

# get fft bin names and amplitude values
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

days = [date for numd,date in zip([x for x in range(len(hivekeepers_data['timestamp'].unique()))], hivekeepers_data['timestamp'].dt.date.unique())]

app.layout = html.Div(
                children=[
                    #dcc.Store(id='memory-apiary'),
                    #dcc.Store(id='memory-days'),
                    # web header, title bar
                    html.Div(
                        children='HiveKeepers Dash App',
                        style = {'font-size': '48px',
                                 'color': '#413F38',
                                 'backgroundColor': '#F0D466',
                                 'font-family': 'Bahnschrift'},),

                    # database update button
                    html.Div([
                        html.Button('Update Database', id='update-button', n_clicks=0),
                        html.Div(id='output-container-button')]),

                    # date range picker
                    html.Div([
                        dcc.DatePickerRange(
                            id='date-picker-range',
                            start_date_placeholder_text="Set start Period",
                            end_date_placeholder_text="Set End Period",
                            updatemode='bothdates',
                            #min_date_allowed=days[0],
                            #max_date_allowed=days[-1],
                            #initial_visible_month=days[0],
                            #end_date=days[-1]
                        ),
                        html.Div(id='output-date-picker-range')
                    ]),

                    # drop down apiary selector for all graphs
                     html.Div([dcc.Dropdown(
                                id='apiary-selector',
                                options=[{'label': f"Apiary: {i}", 'value': i} for i in apiary_list],
                                placeholder="Select an apiaryID",
                                clearable=False,
                                style = {'width': '200px'})]),

                    # graph 1 div
                    html.Div([dcc.Graph(id='graph1', figure=fig1)]),

                    # graph 2 div
                    html.Div([dcc.Graph(id='graph2', figure=fig2)]),

                    # drop down bin selector for fft graphs 3 and 4
                    html.Div([dcc.Dropdown(
                                id='bin-selector',
                                options=[{'label':'fft bins: 0-16',  'value':1},
                                         {'label':'fft bins: 16-32', 'value':2},
                                         {'label':'fft bins: 32-48', 'value':3},
                                         {'label':'fft bins: 48-64', 'value':4},
                                         {'label':'fft bins: all',   'value':5}],
                                value=5,
                                placeholder="Select an FFT bin group",
                                clearable=False,
                                style = {'width': '200px'})]),

                    # graph 3 div
                    html.Div([dcc.Graph(id='graph3', figure=fig3)]),

                    # graph 4 div
                    html.Div([dcc.Graph(id='graph4', figure=fig4)])])

## ================
## Callback Section
## ================

@app.callback(
    Output(component_id='date-picker-range', component_property='min_date_allowed'),
    Output(component_id='date-picker-range', component_property='max_date_allowed'),
    Output(component_id='date-picker-range', component_property='start_date'),
    Output(component_id='date-picker-range', component_property='end_date'),
    Input('apiary-selector', 'value'))
def get_data_options(apiaryID):

    if apiaryID is None:
        raise dash.exceptions.PreventUpdate

    # grab data for selected apiary
    apiary_data = copy.deepcopy(hivekeepers_data.loc[hivekeepers_data["apiary_id"] == int(apiaryID)])
    apiary_days_range = [date for numd,date in zip([x for x in range(len(apiary_data['timestamp'].unique()))], apiary_data['timestamp'].dt.date.unique())]

    from datetime import timedelta

    # default to showing the most recent single day of data
    if len(apiary_days_range) > 1:
        min_date = apiary_days_range[0]
        max_date =  apiary_days_range[-1] + timedelta(days=1)
        start_date = apiary_days_range[-2]
        end_date =  apiary_days_range[-1]
        return min_date, max_date, start_date, end_date
    elif len(apiary_days_range) == 1:
        min_date = apiary_days_range[0]
        max_date =  apiary_days_range[0] + timedelta(days=1)
        start_date = min_date
        end_date =  max_date
        return min_date, max_date, start_date, max_date
    else:
        return None, None, None, None

## dash health-check
@app.server.route("/ping")
def ping():
  return "{status: ok}"

## date range selector
@app.callback(
    Output('output-date-picker-range', 'children'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'))
def update_output(start_date, end_date):

    string_prefix = 'You have selected: '

    if start_date is not None:
        start_date_object = date.fromisoformat(start_date)
        start_date_string = start_date_object.strftime('%B %d, %Y')
        string_prefix = string_prefix + 'Start Date: ' + start_date_string + ' | '

    if end_date is not None:
        end_date_object = date.fromisoformat(end_date)
        end_date_string = end_date_object.strftime('%B %d, %Y')
        string_prefix = string_prefix + 'End Date: ' + end_date_string

    if len(string_prefix) == len('You have selected: '):
        return 'Please select a date range for graphs...'
    else:
        return string_prefix

## database update button
@app.callback(
    dash.dependencies.Output('output-container-button', 'children'),
    [dash.dependencies.Input('update-button', 'n_clicks')])
def run_script_onClick(n_clicks):
    #print('[DEBUG] n_clicks:', n_clicks)

    if not n_clicks:
        raise dash.exceptions.PreventUpdate
        #return dash.no_update

    # without `shell` it needs list ['/full/path/python', 'script.py']
    #result = subprocess.check_output( ['/usr/bin/python', 'script.py'] )

    # with `shell` it needs string 'python script.py'
    result = subprocess.check_output('python update_db.py', shell=True)

    # convert bytes to string
    result = result.decode()

    return result

## all graphs, using: date range selector,
##                    apiaryID selector,
##                    & bin selector,
@app.callback(
    [Output('graph1', 'figure'),
     Output('graph2', 'figure'),
     Output('graph3', 'figure'),
     Output('graph4', 'figure')],
    [Input('apiary-selector', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input("bin-selector", "value")])
def render_graphs(apiaryID, start_date, end_date, bin_group):

    # PreventUpdate prevents ALL outputs updating
    if apiaryID is None or start_date is None or end_date is None or bin_group is None:
        raise dash.exceptions.PreventUpdate

    # convert date objects to formatted date strings
    start_date_string = date.fromisoformat(start_date).strftime('%Y-%m-%d')
    end_date_string = date.fromisoformat(end_date).strftime('%Y-%m-%d')

    # grab data within selected date range
    date_range_df = hivekeepers_data.loc[(hivekeepers_data['timestamp'] >= start_date_string) & (hivekeepers_data['timestamp'] < end_date_string)]

    # grab data for selected apiary
    filtered_hivekeepers_data = copy.deepcopy(date_range_df.loc[date_range_df["apiary_id"] == int(apiaryID)])

    ## ===============================================
    ## fig1 = X-Axis Time,
    ##        Y-Axis1 Internal Temp,
    ##        Y-Axis2 External Temp
    ## 2D line chart
    ## ===============================================

    # Create figure with secondary y-axis
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])

    # add internal temp trace
    fig1.add_trace(
        go.Scatter(x=list(filtered_hivekeepers_data.timestamp),
                   y=list(filtered_hivekeepers_data.bme680_internal_temperature),
                   name="internal_temperature"),
                   secondary_y=False)

    # add external temp trace
    fig1.add_trace(
        go.Scatter(x=list(filtered_hivekeepers_data.timestamp),
                   y=list(filtered_hivekeepers_data.bme680_external_temperature),
                   name="external_temperature"),
                   secondary_y=True)

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

    ## ===============================================
    ## fig2 = X-Axis Time,
    ##        Y-Axis1 Internal Temp,
    ##        Y-Axis2 Internal to External Detla Temp
    ## 2D line chart
    ## ==============================================

    # Create figure with secondary y-axis
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])

    # add internal temp trace
    fig2.add_trace(
        go.Scatter(x=filtered_hivekeepers_data['timestamp'],
                   y=filtered_hivekeepers_data['bme680_internal_temperature'],
                   name="internal_temperature"),
                   secondary_y=False)

    # add delta temp trace
    fig2.add_trace(
        go.Scatter(x=filtered_hivekeepers_data['timestamp'],
                   y=filtered_hivekeepers_data['temp_delta'],
                   name="temp_delta"),
                   secondary_y=True)

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

    ## ===============================================
    ## fig3 = X-Axis Time,
    ##        Y-Axis FFT Bins,
    ##        Z-Axis Amplitude
    ## 3D FFT chart - Surface Plot
    ## ===============================================

    # get fft bin names and amplitude values
    fft_bins = hp.get_fft_bins(filtered_hivekeepers_data)

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

    ## ===============================================
    ## fig4 = X-Axis Time,
    ##        Y-Axis FFT Bins,
    ##        Z-Axis Amplitude,
    ##        C-Axis Internal Temp
    ## 3D FFT chart - Surface Plot
    ## ===============================================

    # grab 4d data within selected date range
    date_range_df_4d = hivekeepers_data_4d.loc[(hivekeepers_data_4d['timestamp'] >= start_date_string) & (hivekeepers_data_4d['timestamp'] < end_date_string)]

    # grab data for selected bin group
    filtered_hivekeepers_data_4d = date_range_df_4d.loc[date_range_df_4d['fft_band'].isin(bins)]

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

    data_4d = [trace1]

    # set chart axis labels
    layout_4d = go.Layout(
        scene = dict(xaxis = dict(title='timestamp'),
                     yaxis = dict(title='fft_bands'),
                     zaxis = dict(title='amplitude'),),)

    # build chart
    fig4 = go.Figure(data=data_4d, layout=layout_4d)

    # set chart title and size
    fig4.update_layout(title='3D FFT chart - Scatter Plot (X-Axis Time, Y-Axis FFT Bins, Z-Axis Amplitude, C-Axis Internal Temp)',
                        autosize=True,
                        height=900)

    return fig1, fig2, fig3, fig4

## =================
## Serve Dash server
## =================

if __name__ == "__main__":
    # set gunincorn through system env var - see docker-compose file
    #app.run_server(host="0.0.0.0", port=8050, debug=True, use_reloader=False)
    app.run_server(host="0.0.0.0", port=os.environ['GUNICORN_PORT'], debug=True, use_reloader=False)
