## =======================
## Import needed libraries
## =======================

import plotly.graph_objects as go # or plotly.express as px
from plotly.subplots import make_subplots
import plotly.express as px

import pandas as pd

import dash
from dash import Dash, dcc, html, Input, Output

import dash_bootstrap_components as dbc


## ===========================
## Get data from database/file 
## ===========================

data = pd.read_csv("data.csv")

# drop unnecessary df columns
data.drop(data.columns[[1,3,4,5,6,7,9,10,11,12,13,14,15,16,18,19,20,22,23,24,25,90,91]], axis=1, inplace=True)

## ==============================
## Build apiary id and bins lists
## ==============================

unique_list = []  
for id in data['apiary_id']:
    # check if exists in unique_list or not
    if id not in unique_list:
        unique_list.append(id)


## ====================================
## Create dash app var and set url base
## ====================================

app = dash.Dash(__name__, url_base_pathname='/app/')

# server var for gunicorn - not used
server = app.server

# initialise figures - might not need with (PreventUpdate prevents ALL outputs updating) ln99
fig1 = go.Figure()
fig2 = go.Figure()
fig3 = go.Figure()


## ===================================
## Set Dash html page layout structure
## ===================================

app.layout = html.Div(
                children=[
                    html.Div(
                        children='HiveKeepers Dash App',
                        style = {'font-size': '48px',
                                 'color': '#413F38',
                                 'backgroundColor': '#F0D466',
                                 'font-family': 'Bahnschrift'},
                    ),
                    
                    html.Div([dcc.Dropdown(
                                id='apiary-selector',
                                options=[{'label': f"Apiary: {i}", 'value': i} for i in unique_list],
                                placeholder="Select an apiaryID",
                                clearable=False,
                                style = {'width': '200px'}
                            ),
                        ], #style = {'backgroundColor': '#696A74',}
                    ), 
                
                    # All elements from the top of the page
                    html.Div([dcc.Graph(id='graph1', figure=fig1)]),
    
                    # New Div for all elements in the new 'row' of the page
                    html.Div([dcc.Graph(id='graph2', figure=fig2)]),
                                
                    # New Div for all elements in the new 'row' of the page
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
                               style = {'width': '200px'}
                           )
                       ], #style = {'backgroundColor': '#696A74',}
                    ),
                    
                    html.Div([dcc.Graph(id='graph3', figure=fig3)]),
                ],
)


## =============
## App callbacks
## =============

@app.callback(
   Output('graph3', 'figure'),
   [Input("bin-selector", "value"),
    Input("apiary-selector", "value")]
) 
def render_fft_graph(bin_group, apiaryID):

    # PreventUpdate prevents ALL outputs updating
    if bin_group is None or apiaryID is None:
        raise dash.exceptions.PreventUpdate
    
    ## ============================================================================
    ## 3D FFT chart – Surface Plot (X-Axis Time, Y-Axis FFT Bins, Z-Axis Amplitude)
    ## ============================================================================

    #filter_data = data[data['apiary_id'] == int(value2)]
    filter_data = data.loc[data["apiary_id"] == int(apiaryID)].copy(deep=True)
    filter_data['timestamp'] = pd.to_datetime(data['timestamp'], unit='s')
    
    ## --------------------------------
    ## build new dataframe for 3d chart 
    ## --------------------------------
    
    # build initial df with timestamp column
    data_3d = [filter_data["timestamp"]]
    headers = ["timestamp"]
    df_new = pd.concat(data_3d, axis=1, keys=headers)
    
    # add internal temperate column and data - repeat 64 times per timestamp row
    df_3d = df_new.loc[df_new.index.repeat(64)].assign(internal_temp=filter_data['bme680_internal_temperature']).reset_index(drop=True).copy()
    
    # get fft bin names and amplitude values
    bin_names = [col for col in filter_data if col.startswith('fft_bin')]
    fft_amplitude = filter_data[bin_names].values
    
    amp_list = []
    bin_list = []
    
    # build lists for converting to dataframe
    for i in fft_amplitude:
        n = 0
        for j in i:
            amp_list.append(j)
            bin_list.append(bin_names[n])
            n += 1
    
    # convert each list to dataframe
    df_fft_amplitude = pd.DataFrame(amp_list, columns=['fft_amplitude'])
    df_fft_band = pd.DataFrame(bin_list, columns=['fft_band'])
    
    # build final dataframe 
    data_final = [df_3d["timestamp"], df_3d["internal_temp"], df_fft_amplitude['fft_amplitude'], df_fft_band['fft_band']]
    headers_final = ["timestamp", "internal_temperature", "fft_amplitude", "fft_band"]
    df_final = pd.concat(data_final, axis=1, keys=headers_final)
    
    ## ---------------------------------
    ## finished building chart dataframe
    ## ---------------------------------
    
    # set bin group from drop down selection
    if bin_group == 1:
        bin_names = bin_names[0:16]
    elif bin_group == 2:
        bin_names = bin_names[16:32]
    elif bin_group == 3:
        bin_names = bin_names[32:48]
    elif bin_group == 4:
        bin_names = bin_names[48:64]
    elif bin_group == 5:
        bin_names = bin_names

    # get subset with selected bin group 
    df_final = df_final.loc[df_final['fft_band'].isin(bin_names)]

    # set chart data config
    trace1 = go.Scatter3d(x = df_final['timestamp'],
                          y = df_final['fft_band'],
                          z = df_final['fft_amplitude'],
                          mode='markers',
                          marker=dict(size=12,
                                      color=df_final['internal_temperature'],
                                      colorscale='Viridis',
                                      opacity=0.8))
    
    chart_data = [trace1]

    # set chart layout
    layout = go.Layout(
        scene = dict(xaxis = dict(title='timestamp'),
                     yaxis = dict(title='fft_bands'),
                     zaxis = dict(title='amplitude'),),
        margin=dict(r=20, b=10, l=10, t=10))
    
    # build chart
    fig3 = go.Figure(data=chart_data, layout=layout)
    
    return fig3

@app.callback(
    [Output('graph1', 'figure'),
     Output('graph2', 'figure')],
    [Input("apiary-selector", "value")]
)
def render_graphs(apiaryID):
    
    # PreventUpdate prevents ALL outputs updating
    if apiaryID is None:
        raise dash.exceptions.PreventUpdate

    ## ================================
    ## Load HiveKeepers data for charts
    ## ================================

    # get apiary data
    filter_data = data.loc[data["apiary_id"] == int(apiaryID)].copy()
    
    # convert timestamp to human readable
    filter_data['timestamp'] = pd.to_datetime(data['timestamp'], unit='s')

    ## ==============================================================================
    ## 2D Chart – Line Plot (X-Axis Time, Y-Axis Internal Temp, Y2-Axis External Temp
    ## ==============================================================================

    # Create figure with secondary y-axis
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])

    # add internal temp trace
    fig1.add_trace(
        go.Scatter(x=list(filter_data.timestamp), y=list(filter_data.bme680_internal_temperature), name="internal_temperature"), secondary_y=False)

    # add external temp trace
    fig1.add_trace(
        go.Scatter(x=list(filter_data.timestamp), y=list(filter_data.bme680_external_temperature), name="external_temperature"), secondary_y=True)

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
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
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
                    dict(step="all")
                ])
            ),
            rangeslider=dict(
                visible=True
            ),
            type="date"
        )
    )
    
    #fig1.update_layout(paper_bgcolor="LightSteelBlue",)
    
    ## ============================================================================================================
    ## 2D Chart – Line Plot (X-Axis Time, Y-Axis Internal Temp, Y2-Axis Internal External Temp delta [WITH SCALING]
    ## ============================================================================================================
    
    # get temp delta
    filter_data['temp_delta'] = filter_data['bme680_internal_temperature'] - filter_data['bme680_external_temperature']
 
    # Create figure with secondary y-axis
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])

    # add internal temp trace
    fig2.add_trace(
        go.Scatter(x=filter_data['timestamp'], y=filter_data['bme680_internal_temperature'], name="internal_temperature"), secondary_y=False)

    # add delta temp trace
    fig2.add_trace(
        go.Scatter(x=filter_data['timestamp'], y=filter_data['temp_delta'], name="temp_delta"), secondary_y=True,
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
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
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
                    dict(step="all")
                ])
            ),
            rangeslider=dict(
                visible=True
            ),
            type="date"
        )
    )
    
    #fig2.update_layout(paper_bgcolor="LightSteelBlue",)

    ## ============================================================================
    ## 3D FFT chart – Surface Plot (X-Axis Time, Y-Axis FFT Bins, Z-Axis Amplitude)
    ## ============================================================================

    # bins = [col for col in filter_data if col.startswith('fft_bin')]
    
    # bins = bins[32:48]

    # # get bin numbers only fft_bin60 -> 60
    # bin_nums = [bin.replace("fft_bin", "") for bin in bins]

    # fig3 = go.Figure(data=[go.Surface(x=filter_data['timestamp'], z=filter_data[bins].values, y=bin_nums)])


    # fig3.update_layout(title='3D FFT chart – Surface Plot (X-Axis Time, Y-Axis FFT Bins, Z-Axis Amplitude)',
                        # autosize=True,
                        # height=900)


    # fig3.update_layout(scene = dict(
                        # xaxis_title = 'Date',
                        # yaxis_title = 'FFT Bins',
                        # zaxis_title = 'Amplitude'))

    return fig1, fig2


## ==================
## Call main function
## ==================

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)