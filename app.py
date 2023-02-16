import numpy as np
import pandas as pd
from nba_api.stats.endpoints import shotchartdetail
from nba_api.stats.static import players, teams
import nba_api
import json
import scipy.ndimage
import plotly.graph_objects as go
import plotly.io as pio
import plotly
from flask import Flask, request, render_template, redirect
import flask
# connect app to flask framework
print(pd.__version__)
print(np.__version__)
print(scipy.__version__)
print(plotly.__version__)
# print(nba_api.__version__)
print(json.__version__)
print(flask.__version__)

app = Flask(__name__)

# get players from player database
player_dict = players.get_players()
player_selected = []
team_dict = teams.get_teams()

# route to index (the only html file), takes GET and POST

@app.route("/", methods=["GET", "POST"])
def index():
    error = ""
    if (request.method == "POST"):
        # get player from index.html form
        player = request.form.get("player")
        try:
            # get player from database based on input
            player_selected = [p for p in player_dict if p["full_name"].lower() == player.lower()][0]

            # POST data to send to nba api
            response = shotchartdetail.ShotChartDetail(
                team_id=0,
                player_id=int(player_selected["id"]),
                season_type_all_star='Regular Season',
                context_measure_simple='FGA',
                last_n_games=0,
                league_id='00',
                month=0,
                opponent_team_id=0,
                period=0
            )

            # get response and convert to pandas dataframe
            res = response.get_json()
            raw_data = json.loads(res)

            results = raw_data['resultSets'][0]

            headers = results['headers']
            rows = results['rowSet']

            df = pd.DataFrame(rows)
            df.columns = headers

            # create a grid of shots based on where on the court they're taken
            grid = generate_shot_grid(data=df)

            # turn grid into x and y coordinates to plot, as well as the field goal percentages
            x, y, fgp = plot(grid=grid, data=df)

            # generate a plotly figure with the above data
            fig = draw(fg_pct = fgp, x_data=x, y_data=y, player=player)

            # turn graph into html to render with flask
            graph = pio.to_html(fig, full_html=False, default_height=700, default_width='90%')

            # set error to None
            error = ""

            # re-render index.html
            return render_template("index.html", graph=graph)

        except IndexError:
            # raise error if player's spelled wrong
            error = "Player not found. Please check spelling and type player's full name."
        
        except ValueError:
            # raise error if player's found but no data available
            error = "No shooting data on record. Please try another player."

    # render index with the error displayed
    return render_template("index.html", error=error)

#get player object from input
def get_data(id):
    # define parameters for request
    response = shotchartdetail.ShotChartDetail(
        team_id=0,
        player_id=int(id),
        season_type_all_star='Regular Season',
        context_measure_simple='FGA',
        last_n_games=0,
        league_id='00',
        month=0,
        opponent_team_id=0,
        period=0
    )

    # get response and convert to pandas dataframe
    raw_data = json.loads(response.get_json())

    results = raw_data['resultSets'][0]

    headers = results['headers']
    rows = results['rowSet']

    df = pd.DataFrame(rows)
    df.columns = headers

def generate_shot_grid(data):
    # only need to get location of shots, attempts, and makes
    data = data.filter(items=['LOC_X', 'LOC_Y', 'SHOT_MADE_FLAG', 'SHOT_ATTEMPTED_FLAG', 'SHOT_ZONE_RANGE'])

    #normalize data from 0 to 500
    data['LOC_X'] = data['LOC_X'] + (-1*min(data['LOC_X']))
    data['LOC_Y'] = data['LOC_Y'] + (-1*min(data['LOC_Y']))

    # bins is number of regions court should be split into
    bins = np.arange(10, 501, 10)

    # dictionary for storing x coordinates of the regions
    dict_x = {}
    for val in bins:
        dict_x[val] = []

    # organize all shot data of player into bins
    for i in range(0, len(data)):
        for j in range(0, len(bins)):
            if data['LOC_X'][i] < bins[j]:
                dict_x[bins[j]].append(i)
                break

    # create x and y regions (50)
    x_regions = np.arange(0, 50)
    y_regions = np.arange(0, 50)

    #create a dictionary of all regions
    reg_dict = {}
    for i in range(1, len(x_regions)*len(y_regions)+1):
        reg_dict[i] = []

    temp_regions = np.arange(1, 51)

    # orgnaize all the shots into x and y coordinates and transfer into reg_dict
    reg_idx = 0
    divisor = 100
    for key in dict_x:
        for idx in dict_x[key]:
            reg_idx = int(data['LOC_X'][idx]*data['LOC_Y'][idx]/divisor)
            if reg_idx < len(temp_regions):
                reg_dict[temp_regions[reg_idx]].append(idx)
        temp_regions += 50
        divisor += 100

    return reg_dict

# calculate field goal precentage by taking made shots divided by total shots attempted
def calc_fg_pct(arr, data):
    made = 0
    total = 0
    if len(arr) == 0:
        return 0
    for index in arr:
        made += data['SHOT_MADE_FLAG'][index]
        total += 1
    return float(100 * made/total)

# transfer data into plottable x, y, and z coordinates
def plot(grid, data):
    fg_pct = np.array([])
    for key in grid:
        fg_pct = np.append(fg_pct, calc_fg_pct(grid[key], data))

    fg_pct = np.transpose(np.reshape(fg_pct, (50, 50)))

    x_data, y_data = np.meshgrid(np.arange(0, 50), np.arange(0, 50))

    return x_data, y_data, fg_pct

def draw(fg_pct, x_data, y_data, player):
    r_arc = 23.75

    # Theta varies only between 22 degrees and 158 degrees for the 3-point line
    theta_arc = np.linspace(22*np.pi/180., 158*np.pi/180., 1000)

    # coorindates for the 3-point ard
    y_arc = r_arc*np.sin(theta_arc) + 4.75
    x_arc = r_arc*np.cos(theta_arc) + 25 
    z_arc = np.full_like(theta_arc, 0) 

    # coords for left corner 3-point line
    y_left_corner = np.linspace(0, 14, 1000)
    x_left_corner = np.linspace(3, 3, 1000)
    z_left_corner = np.full_like(x_left_corner, 0)

    # coords for right corner 3
    y_right_corner = np.linspace(0, 14, 1000)
    x_right_corner = np.linspace(47, 47, 1000)
    z_right_corner = np.full_like(x_right_corner, 0)

    # coordinates for basket
    theta_hoop = np.linspace(0, 2*np.pi, 1000)
    y_hoop = np.sin(theta_hoop) + 4.75
    x_hoop = np.cos(theta_hoop) + 25
    z_hoop = np.full_like(theta_hoop, 0)

    # coordinates for backboard
    y_backboard = np.linspace(3.75, 3.75, 1000)
    x_backboard = np.linspace(22, 28, 1000)
    z_backboard = np.full_like(x_backboard, 0)

    # coordinates for baseline
    x_baseline = np.linspace(0, 50, 1000)
    y_baseline = np.linspace(0, 0, 1000)
    z_baseline = np.full_like(y_baseline, 0)

    # coordinates for sidelines
    y_sideline = np.linspace(0, 50, 1000)
    x_right_sideline = np.full_like(y_sideline, 0)
    z_sideline = np.full_like(y_sideline, 0)
    x_left_sideline = np.full_like(y_sideline, 50)

    # apply a filter to make graph more smooth (makes data not 100% accurate however)
    pct_normalized = scipy.ndimage.filters.gaussian_filter(fg_pct, [1, 1])

    # dictionary for lighting
    light = {
        "ambient": 1,
        "roughness": 1,
        "diffuse": 1,
        "specular": 0.2,
        "fresnel": 0
    }

    # create the figure with JSON parameters
    figure = go.Figure(
        data=[
            go.Surface(
                z=pct_normalized,
                x=x_data,
                y=y_data,
                name="Shooting %",
                hoverinfo="z+name",
                opacity=0.92,
                colorscale="YlOrRd",
                lighting=light
            )
        ],
        layout = {
            "title": {
                "text": player.title() + " Shooting Chart"
            },
            "scene": {
                "xaxis": {
                    "showline": False,
                    "showgrid": False,
                    "showticklabels": False,
                    "title": {
                        "text": "<br>"
                    }
                },
                "yaxis": {
                    "showline": False,
                    "showgrid": False,
                    "showticklabels": False,
                    "title": {
                        "text": "<br>"
                    }
                },
                "zaxis": {
                    "title": {
                        "text": "Shooting %"
                    }
                }
            }
        }
    )

    # more specifications for graph
    line_marker = dict(
        color="black",
        width=5
    )

    # add all the court elements, such as hoop, backboard, baseline, etc.
    figure.add_scatter3d(x=x_arc, y=y_arc, z=z_arc, mode="lines", line=line_marker, showlegend=False)
    figure.add_scatter3d(x=x_left_corner, y=y_left_corner, z=z_left_corner, mode="lines", line=line_marker, showlegend=False)
    figure.add_scatter3d(x=x_right_corner, y=y_right_corner, z=z_right_corner, mode="lines", line=line_marker, showlegend=False)
    figure.add_scatter3d(x=x_hoop, y=y_hoop, z=z_hoop, mode="lines", line=line_marker, showlegend=False)
    figure.add_scatter3d(x=x_backboard, y=y_backboard, z=z_backboard, mode="lines", line=line_marker, showlegend=False)
    figure.add_scatter3d(x=x_baseline, y=y_baseline, z=z_baseline, mode="lines", line=line_marker, showlegend=False)
    figure.add_scatter3d(x=x_right_sideline, y=y_sideline, z=z_sideline, mode="lines", line=line_marker, showlegend=False)
    figure.add_scatter3d(x=x_left_sideline, y=y_sideline, z=z_sideline, mode="lines", line=line_marker, showlegend=False)

    return figure
