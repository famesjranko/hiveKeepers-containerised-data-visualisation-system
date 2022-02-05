# HiveKeepers - container1 - dash - hivekeepers_app.py
# written by: Andrew McDonald
# initial: 31/01/22
# current: 04/02/22
# version: 0.3

import dash
from dash import dcc
from dash import html
import pandas as pd
#import flask

# load data
data = pd.read_csv("data.csv")

# select a single device id
data = data.query("device_id == '340051000a504e5354303420'")

# sort by timestamp
data.sort_values("timestamp", inplace=True)

# define flask app.server
#server = flask.Flask(__name__)

# load dash
app = dash.Dash(__name__, url_base_pathname='/app/')

# server var for gunicorn - not used
server = app.server

# dash layout section
app.layout = html.Div(
    children=[
        html.H1(children="test dash",),
        html.P(
            children="simple test line 1"
            " simple test line 2"
            " simple test line 3",
        ),
        dcc.Graph(
            figure={
                "data": [
                    {
                        "x": data["timestamp"],
                        "y": data["health_state_of_charge"],
                        "type": "lines",
                    },
                ],
                "layout": {"title": "state of charge"},
            },
        ),
        dcc.Graph(
            figure={
                "data": [
                    {
                        "x": data["timestamp"],
                        "y": data["health_signal_strength"],
                        "type": "lines",
                    },
                ],
                "layout": {"title": "health of signal strength"},
            },
        ),
    ]
)

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
    #app.run_server(debug=True)
