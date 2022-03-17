# HiveKeepers - container2 - dash_app/hivekeepers_app.py
# written by: Andrew McDonald
# initial: 26/01/22
# current: 17/03/22
# version: 0.9

## =======================
## Import needed libraries
## =======================

import os
import subprocess
from datetime import date,timedelta
from pathlib import Path

# pandas vers==1.4.0
import pandas as pd

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

import dash
from dash import Dash, dcc, html, Input, Output

import hivekeepers_helpers as hp
import hivekeepers_config as hc

import logging

## =================
## Configure Logging 
## =================

# build logger
logger = logging.getLogger()

# set stdout and file log handlers
handler_stdout = logging.StreamHandler()
handler_file = logging.FileHandler('/home/hivekeeper/persistent/logs/container2/app.log')

# set log format
formatter = logging.Formatter('%(asctime)s [PYTHON] [%(levelname)s] %(filename)s: %(message)s')

# add formatters
handler_stdout.setFormatter(formatter)
handler_file.setFormatter(formatter)

# add handlers
logger.addHandler(handler_stdout)
logger.addHandler(handler_file)

# get logging level from system environment variable
log_level = hc.APP_LOG_LEVEL

# set logging level from system environment variable
if log_level == 'DEBUG':
    logger.setLevel(logging.DEBUG)
elif log_level == 'INFO':
    logger.setLevel(logging.INFO)
elif log_level == 'WARNING':
    logger.setLevel(logging.WARNING)
elif log_level == 'ERROR':
    logger.setLevel(logging.ERROR)
elif log_level == 'CRITICAL':
    logger.setLevel(logging.CRITICAL)
else:
    logger.setLevel(logging.INFO)

## =================
## MAIN APP SETTINGS
## =================

# Build apiary names list
# logger.info('building apiary names list for drop down menu')
apiary_list = hp.get_apiary_names()

## colours for charts - see fft callback section for full list of colour choices
logger.info('getting colour scale list for 3d chart colour drop down menu')
colorscales = px.colors.named_colorscales()

## ====================================
## Dash Section server & layout section
## ====================================

## Create dash app and set url basen pathame
logger.info('init Dash object with url base pathname set: .../app/')
app = Dash(__name__, url_base_pathname='/app/')

# server var for gunicorn
logger.info('init app server...')
server = app.server

# initialise figures
logger.info('init empty figure objects')
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

                    # database update button
                    html.Div([
                        html.Button('Update Database',
                                    id='update-button',
                                    n_clicks=0,
                                    style={'font-size': '18px', 'width': '287px', 'height':'35px'}),
                        html.Div(id='output-container-button')]),

                    # date range picker
                    html.Div([
                        dcc.DatePickerRange(
                            id='date-picker-range',
                            start_date_placeholder_text="Start Date",
                            end_date_placeholder_text="End Date",
                            updatemode='bothdates',
                            minimum_nights=0),
                        html.Div(id='output-date-picker-range')
                    ]),

                    # drop down apiary selector for all graphs
                    html.Div([
                        dcc.Dropdown(
                            id='apiary-selector',
                            options=[{'label': f"{i}", 'value': i} for i in apiary_list],
                            placeholder="Select an apiary",
                            clearable=False,
                            style = {'font-size': '18px', 'width': '287px'})]),

                    # graph 1 div
                    html.Div([dcc.Graph(id='graph1', figure=fig1)]),

                    # graph 2 div
                    html.Div([dcc.Graph(id='graph2', figure=fig2)]),

                    # drop downs selectors for fft graphs 3 and 4
                    html.Div([
                        # bin selector
                        dcc.Dropdown(
                            id='bin-selector',
                            options=[{'label':'fft bins: 0-16', 'value':1},
                                    {'label':'fft bins: 16-32', 'value':2},
                                    {'label':'fft bins: 32-48', 'value':3},
                                    {'label':'fft bins: 48-64', 'value':4},
                                    {'label':'fft bins: all',   'value':5}],
                            value=5,
                            placeholder="Select FFT bin group",
                            clearable=False,
                            style = {'font-size': '18px', 'width': '287px'}),
                        # colour selector
                        dcc.Dropdown(
                            id='colorscale', 
                            options=[{"value": x, "label": x} for x in colorscales],
                            value='viridis',
                            placeholder="Select FFT colour scale",
                            clearable=False,
                            style = {'font-size': '18px', 'width': '287px'},)
                    ]),

                    # graph 3 div
                    html.Div([dcc.Graph(id='graph3', figure=fig3)]),

                    # graph 4 div
                    html.Div([dcc.Graph(id='graph4', figure=fig4)])])

## ================
## Callback Section
## ================

## date range selector
@app.callback(
    Output(component_id='date-picker-range', component_property='min_date_allowed'),
    Output(component_id='date-picker-range', component_property='max_date_allowed'),
    Output(component_id='date-picker-range', component_property='start_date'),
    Output(component_id='date-picker-range', component_property='end_date'),
    Input('apiary-selector', 'value'))
def get_data_options(apiary_name):
    logger.info('running date range selector callback')
    logger.debug(f'apiary_name: {apiary_name}')

    if apiary_name is None:
        logger.warn('no data sent to date range selector callback...')
        raise dash.exceptions.PreventUpdate

    # grab timestamps for selected apiary
    try:
        apiary_timestamps = hp.get_apiary_timestamps_name(apiary_name)
    except Exception as e:
        logger.info(f'get timestamps from sql-lite db error: {e}')

    # convert timestamps to datetime objects
    apiary_timestamps['timestamp'] = pd.to_datetime(apiary_timestamps['timestamp'])

    # build apiary data date range (days)
    apiary_days_range = [date for numd,date in zip([x for x in range(len(apiary_timestamps['timestamp'].unique()))], apiary_timestamps['timestamp'].dt.date.unique())]
    logger.debug(f'apiary_days_range: {apiary_days_range}')
    
    if len(apiary_days_range) < 1:          # zero days found
        logger.info('apiary_days_range is zero...')
        return None, None, None, None

    if len(apiary_days_range) > 1:          # data > 1 day
        max_date =  apiary_days_range[-1] + timedelta(days=1)
        start_date = apiary_days_range[-1]

    if len(apiary_days_range) == 1:         # data <= 1 day
        max_date =  apiary_days_range[0] + timedelta(days=1)
        start_date = apiary_days_range[0]

    min_date = apiary_days_range[0]
    end_date =  max_date

    logger.debug(f'min_date: {min_date}')
    logger.debug(f'max_date: {max_date}')
    logger.debug(f'start_date: {start_date}')
    logger.debug(f'end_date: {end_date}')

    return min_date, max_date, start_date, end_date

## date range selector text output
@app.callback(
    Output('output-date-picker-range', 'children'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'))
def update_output(start_date, end_date):
    logger.info('running date range selector text output callback')
    logger.debug(f'start_date: {start_date}')
    logger.debug(f'end_date: {end_date}')

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
     Input("bin-selector", "value"),
     Input("colorscale", "value")])
def render_graphs(apiary_name, start_date, end_date, bin_group, scale):
    logger.info('running graph rendering callback')
    logger.debug(f'apiary_name: {apiary_name}')
    logger.debug(f'start_date: {start_date}')
    logger.debug(f'end_date: {end_date}')
    logger.debug(f'bin_group: {bin_group}')
    logger.debug(f'scale: {scale}')

    # PreventUpdate prevents ALL outputs updating
    if apiary_name is None or start_date is None or end_date is None or bin_group is None:
        logger.warn('no data sent to graph rendering callback...')
        raise dash.exceptions.PreventUpdate

    # convert date objects to formatted date strings
    start_date_string = date.fromisoformat(start_date).strftime('%Y-%m-%d')
    end_date_string = date.fromisoformat(end_date).strftime('%Y-%m-%d')
    logger.debug(f'start_date_string: {start_date_string}, end_date_string: {end_date_string}')

    # get data from sql-lite db 
    try:
        filtered_hivekeepers_data = hp.get_data(apiary_name, start_date_string, end_date_string)
    except Exception as e:
        logger.info(f'get data from sql-lite db error: {e}')
    
    logger.debug(f'filtered_hivekeepers_data: {filtered_hivekeepers_data}')
    
    # if dataframe is empty, update fig titles and return empty graphs
    if filtered_hivekeepers_data.empty:
        logger.info('No data found for graphs')

        # empty fig 1
        fig1 = go.Figure(data=[go.Scatter(x=[], y=[])])
        fig1.update_layout(title_text='No data available')

        # empty fig 2
        fig2 = go.Figure(data=[go.Scatter(x=[], y=[])])
        fig2.update_layout(title_text='No data available')

        # empty fig 3
        fig3 = go.Figure(data=[go.Scatter(x=[], y=[])])
        fig3.update_layout(title='No data available')
        
        # empty fig 4
        fig4 = go.Figure(data=[go.Scatter(x=[], y=[])])
        fig4.update_layout(title='No data available')

        return fig1, fig2, fig3, fig4

    ## ===============================================
    ## fig1 = X-Axis Time,
    ##        Y-Axis1 Internal Temp,
    ##        Y-Axis2 External Temp
    ## 2D line chart
    ## ===============================================

    # Create figure with secondary y-axis
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])

    logger.debug(f"fig2 trace1 x = {filtered_hivekeepers_data['timestamp']}")
    logger.debug(f"fig2 trace1 y = {filtered_hivekeepers_data['bme680_internal_temperature']}")

    # add internal temp trace
    try:
        fig1.add_trace(go.Scatter(x=filtered_hivekeepers_data['timestamp'],                    #x=list(filtered_hivekeepers_data.timestamp),
                                  y=filtered_hivekeepers_data['bme680_internal_temperature'],  #y=list(filtered_hivekeepers_data.bme680_internal_temperature),
                                  name="internal_temperature"),
                       secondary_y=False)
    except Exception as e:
        logger.error(f'fig2 1st trace error: {e}')
    
    logger.debug(f"fig2 trace2 x = {filtered_hivekeepers_data['timestamp']}")
    logger.debug(f"fig2 trace2 y = {filtered_hivekeepers_data['bme680_external_temperature']}")

    # add external temp trace
    try:
        fig1.add_trace(go.Scatter(x=filtered_hivekeepers_data['timestamp'],                    #x=list(filtered_hivekeepers_data.timestamp),
                                  y=filtered_hivekeepers_data['bme680_external_temperature'],  #y=list(filtered_hivekeepers_data.bme680_external_temperature),
                                  name="external_temperature"),
                       secondary_y=True)
    except Exception as e:
        logger.error(f'fig1 2nd trace error: {e}')

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

    logger.debug(f"fig2 trace1 x = {filtered_hivekeepers_data['timestamp']}")
    logger.debug(f"fig2 trace1 y = {filtered_hivekeepers_data['bme680_internal_temperature']}")

    # add internal temp trace
    try:
        fig2.add_trace(go.Scatter(x=filtered_hivekeepers_data['timestamp'],
                                  y=filtered_hivekeepers_data['bme680_internal_temperature'],
                                  name="internal_temperature"),
                       secondary_y=False)
    except Exception as e:
        logger.error(f'fig2 trace1 error: {e}')

    logger.debug(f"fig2 trace2 x = {filtered_hivekeepers_data['timestamp']}")
    logger.debug(f"fig2 trace2 y = {filtered_hivekeepers_data['temp_delta']}")

    # add delta temp trace
    try:
        fig2.add_trace(go.Scatter(x=filtered_hivekeepers_data['timestamp'],
                                  y=filtered_hivekeepers_data['temp_delta'],
                                  name="temp_delta",
                                  line=dict(color="orange")),
                       secondary_y=True)
    except Exception as e:
        logger.error(f'fig2 trace2 error: {e}')
    
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
    ## 3D FFT chart - Scatter Plot
    ## ===============================================

    ## ==== plotly colourscale options: default = viridis
    # aggrnyl     agsunset    blackbody   bluered     blues       blugrn      bluyl       brwnyl
    # bugn        bupu        burg        burgyl      cividis     darkmint    electric    emrld
    # gnbu        greens      greys       hot         inferno     jet         magenta     magma
    # mint        orrd        oranges     oryel       peach       pinkyl      plasma      plotly3
    # pubu        pubugn      purd        purp        purples     purpor      rainbow     rdbu
    # rdpu        redor       reds        sunset      sunsetdark  teal        tealgrn     turbo
    # viridis     ylgn        ylgnbu      ylorbr      ylorrd      algae       amp         deep
    # dense       gray        haline      ice         matter      solar       speed       tempo
    # thermal     turbid      armyrose    brbg        earth       fall        geyser      prgn
    # piyg        picnic      portland    puor        rdgy        rdylbu      rdylgn      spectral
    # tealrose    temps       tropic      balance     curl        delta       oxy         edge
    # hsv         icefire     phase       twilight    mrybm       mygbm

    # get fft bin names and amplitude values
    fft_bins = hp.get_fft_bins(filtered_hivekeepers_data)
    logger.debug(f'fft_bins: {fft_bins}')

    # get bins from drop down selection
    bins = hp.get_bin_range(bin_group, fft_bins)
    logger.debug(f'bins: {bins}')

    # get 3d data from sql-lite db
    try:
        date_range_df_3d = hp.build_3d_data(filtered_hivekeepers_data)
    except Exception as e:
        logger.error(f'build_3d_data error: {e}')

    # grab data for selected bin group
    filtered_hivekeepers_data_3d = date_range_df_3d.loc[date_range_df_3d['fft_band'].isin(bins)]
    
    logger.debug(f"fig3 x = {filtered_hivekeepers_data_3d['timestamp']}")
    logger.debug(f"fig3 y = {filtered_hivekeepers_data_3d['fft_band']}")
    logger.debug(f"fig3 z = {filtered_hivekeepers_data_3d['fft_amplitude']}")
    
    # set chart data config
    try:
        trace_3d = go.Scatter3d(x = filtered_hivekeepers_data_3d['timestamp'],
                                y = filtered_hivekeepers_data_3d['fft_band'],
                                z = filtered_hivekeepers_data_3d['fft_amplitude'],
                                mode='markers',
                                marker=dict(size=12,
                                    color=filtered_hivekeepers_data_3d['fft_amplitude'],
                                    colorscale=scale,
                                    opacity=0.8,
                                    showscale=True,
                                    colorbar=dict(title='amplitude'),))
    except Exception as e:
         logger.error(f'fig3 error: {e}')

    data_3d = [trace_3d]

    # set chart axis labels
    layout_3d = go.Layout(
        scene = dict(xaxis = dict(title='timestamp'),
                     yaxis = dict(title='fft_bands'),
                     zaxis = dict(title='amplitude'),),)

    # build chart
    fig3 = go.Figure(data=data_3d, layout=layout_3d)

    # set chart title and size
    fig3.update_layout(title='3D FFT chart - Scatter Plot (X-Axis Time, Y-Axis FFT Bins, Z-Axis Amplitude, C-Axis Internal Temp)',
                       autosize=True,
                       height=900)

    ## ===============================================
    ## fig4 = X-Axis Time,
    ##        Y-Axis FFT Bins,
    ##        Z-Axis Amplitude,
    ##        C-Axis Internal Temp
    ## 3D FFT chart - Scatter Plot
    ## ===============================================

    logger.debug(f"fig4 x = {filtered_hivekeepers_data_3d['timestamp']}")
    logger.debug(f"fig4 y = {filtered_hivekeepers_data_3d['fft_band']}")
    logger.debug(f"fig4 z = {filtered_hivekeepers_data_3d['fft_amplitude']}")
    logger.debug(f"fig4 c = {filtered_hivekeepers_data_3d['internal_temperature']}")

    # set chart data config
    try:
        trace4d = go.Scatter3d(x = filtered_hivekeepers_data_3d['timestamp'],
                               y = filtered_hivekeepers_data_3d['fft_band'],
                               z = filtered_hivekeepers_data_3d['fft_amplitude'],
                               mode='markers',
                               marker=dict(size=12,
                                    color=filtered_hivekeepers_data_3d['internal_temperature'],
                                    colorscale=scale,
                                    opacity=0.8,
                                    showscale=True,
                                    colorbar=dict(title='internal temp (C)'),))
    except Exception as e:
         logger.error(f'fig4 error: {e}')

    data_4d = [trace4d]

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

## database update button - returns prints from update_db script
@app.callback(
    dash.dependencies.Output('output-container-button', 'children'),
    dash.dependencies.Output('apiary-selector', 'options'),
    [dash.dependencies.Input('update-button', 'n_clicks')])
def run_script_onClick(n_clicks):
    logger.info('Running database update button callback')

    if not n_clicks:
        logger.info('no data sent to run script onClick callback...')
        raise dash.exceptions.PreventUpdate

    # without `shell` it needs list ['/full/path/python', 'script.py']
    # with `shell` it needs string 'python script.py'

    # check if SQLite db is empty or not
    db_length = Path(hc.SQLite_db_name).stat().st_size
    logger.debug(f'database length is: {db_length}')

    if db_length < 1:
        logger.debug(f'database length is: {db_length}, which is less than 1')

        try:
            # if empty, build from scratch
            result = subprocess.check_output('python3 startup_update_db.py', shell=True)
        except Exception as e:
            logger.error(f'database update error: {e}')
    else:
        try:
            # if not empty, update it
            result = subprocess.check_output('python3 update_db.py', shell=True)
        except Exception as e:
            logger.error(f'database update error: {e}')

    # convert bytes to string
    result = result.decode()
    logger.debug(f'returned string from update_db.py: {result}')

    # build/update apiary name list
    logger.info('updating apiary name list for drop down menu')
    apiary_list = hp.get_apiary_names()

    # return prints from update_db script
    return result, apiary_list

## CONTAINER health-check
@app.server.route("/ping")
def ping():
    logger.debug('Running healtheck callback ping() via .../ping')
    return "{status: ok}"

## =================
## Serve Dash server
## =================

if __name__ == "__main__":
    # set gunincorn through system env var - see docker-compose file
    #app.run_server(host="0.0.0.0", port=8050, debug=False, use_reloader=False)
    app.run_server(host="0.0.0.0", port=hc.APP_PORT, debug=False, use_reloader=False)
