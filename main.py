import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import pandas as pd
from matplotlib.ticker import LinearLocator
import ssl
from nba_api.stats.endpoints import shotchartdetail
from nba_api.stats.static import players, teams
import json
import scipy.ndimage
import mpl_toolkits.mplot3d.art3d as art3d
ssl._create_default_https_context = ssl._create_unverified_context

#get player object from input
player_dict = players.get_players()
team_dict = teams.get_teams()
player_requested = input('NBA Player Name: ')
player_selected = [p for p in player_dict if p["full_name"].lower() == player_requested.lower()][0]
player_selected_id = player_selected["id"]

# define parameters for request
response = shotchartdetail.ShotChartDetail(
	team_id=0,
	player_id=int(player_selected_id),
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

# only need to get location of shots, attempts, and makes
df = df.filter(items= ['LOC_X', 'LOC_Y', 'SHOT_MADE_FLAG', 'SHOT_ATTEMPTED_FLAG', 'SHOT_ZONE_RANGE'])

#normalize data from 0 to 500
df['LOC_X'] = df['LOC_X'] + (-1*min(df['LOC_X']))
df['LOC_Y'] = df['LOC_Y'] + (-1*min(df['LOC_Y']))

bins = np.arange(10, 501, 10)

dict_x = {}
for val in bins:
    dict_x[val] = []

for i in range(0, len(df)):
    for j in range(0, len(bins)):
        if df['LOC_X'][i] < bins[j]:
            dict_x[bins[j]].append(i)
            break

x_regions = np.arange(0, 50)
y_regions = np.arange(0, 50)
reg_dict = {}
for i in range(1, len(x_regions)*len(y_regions)+1):
    reg_dict[i] = []

temp_regions = np.arange(1, 51)

reg_idx = 0
divisor = 100
for key in dict_x:
    for idx in dict_x[key]:
        reg_idx = int(df['LOC_X'][idx]*df['LOC_Y'][idx]/divisor)
        if reg_idx < len(temp_regions):
            reg_dict[temp_regions[reg_idx]].append(idx)
    temp_regions += 50
    divisor += 100

def calc_fg_pct(arr):
    made = 0
    total = 0
    if len(arr) == 0:
        return 0
    for index in arr:
        made += df['SHOT_MADE_FLAG'][index]
        total += 1
    return float(made/total)

fg_pct = np.array([])
for key in reg_dict:
    fg_pct = np.append(fg_pct, calc_fg_pct(reg_dict[key]))

fg_pct = np.transpose(np.reshape(fg_pct, (50, 50)))

x_data, y_data = np.meshgrid(x_regions, y_regions)

fig, ax = plt.subplots(subplot_kw={"projection": "3d"})

def draw_court(ax = None, color = 'white', lw = 2, outer_lines = False):
    if ax is None:
        ax = plt.gca()
    hoop = Circle((4.75, 25), radius = 0.75, linewidth = lw, color=color, fill=False)
    backboard = Rectangle((4, 22), -0.1, 6, linewidth = lw, color = color)
    inner_box = Rectangle((0, 19), 19, 12, linewidth = lw, color = color, fill = False)
    top_free_throw = Wedge((19, 25), 6, theta1 = 270, theta2 = 90, linewidth = lw, color = color, fill = False)
    bottom_free_throw = Wedge((19, 25), 6, theta1 = 90, theta2 = 270, linewidth = lw, color = color, linestyle = "dashed", fill = False)
    corner_three_right = Rectangle((0, 3), 14, 0.1, linewidth = lw, color = color)
    corner_three_left = Rectangle((0, 47), 14, 0.1, linewidth = lw, color = color)
    #three_arc = Wedge((4.75, 25), 23.75, 270, 90, linewidth = lw, color = color, fill = False)

    court_elements = [hoop, backboard, inner_box, top_free_throw, bottom_free_throw, corner_three_right, corner_three_left]

    if outer_lines:
        outer_lines = Rectangle((0, 0), 50, 50, linewidth = lw, color = color, fill = False)
        court_elements.append(outer_lines)

    for element in court_elements:
        ax.add_patch(element)
        art3d.pathpatch_2d_to_3d(element, z=40, zdir = 'z')

    return ax

# draw_court(outer_lines=True, color='black')
r_arc = 23.75
r_hoop = 0.75

# Theta varies only between pi/2 and 3pi/2. to have a half-circle
theta_arc = np.linspace(22*np.pi/180., 158*np.pi/180., 1000)

y_arc = r_arc*np.sin(theta_arc) + 4.75 # x=0
x_arc = r_arc*np.cos(theta_arc) + 25 # y - y0 = r*cos(theta)
z_arc = np.full_like(theta_arc, 0) # z - z0 = r*sin(theta)

y_left_corner = np.linspace(0, 14, 1000)
x_left_corner = np.linspace(3, 3, 1000)
z_left_corner = np.full_like(x_left_corner, 0)

y_right_corner = np.linspace(0, 14, 1000)
x_right_corner = np.linspace(47, 47, 1000)
z_right_corner = np.full_like(x_right_corner, 0)

theta_hoop = np.linspace(0, 2*np.pi, 1000)
y_hoop = np.sin(theta_hoop) + 4.75
x_hoop = np.cos(theta_hoop) + 25
z_hoop = np.full_like(theta_hoop, 0)

y_backboard = np.linspace(3.75, 3.75, 1000)
x_backboard = np.linspace(22, 28, 1000)
z_backboard = np.full_like(x_backboard, 0)

x_baseline = np.linspace(3, 47, 1000)
y_baseline = np.linspace(0, 0, 1000)
z_baseline = np.full_like(y_baseline, 0)

ax.plot(x_arc, y_arc, z_arc, color = 'black', linewidth = 2, zorder = 10)
ax.plot(x_left_corner, y_left_corner, z_left_corner, color = "black", linewidth = 2, zorder = 10)
ax.plot(x_hoop, y_hoop, z_hoop, color = "black", linewidth = 2, zorder = 10)
ax.plot(x_right_corner, y_right_corner, z_right_corner, color = "black", linewidth = 2, zorder = 10)
ax.plot(x_backboard, y_backboard, z_backboard, color = "black", linewidth = 2, zorder = 10)
box = Rectangle((19, 0), 12, 19, linewidth = 2, color = 'black', fill = False)
ax.plot(x_baseline, y_baseline, z_baseline, linewidth = 2, color = "black", zorder = 10)
ax.add_patch(box)
art3d.pathpatch_2d_to_3d(box, z=0, zdir = 'z')

sigma = [1.5, 1.5]

smooth = scipy.ndimage.filters.gaussian_filter(fg_pct, sigma)

surf = ax.plot_surface(x_data, y_data, smooth, cmap='jet', linewidth=0, antialiased=True)

ax.set_title(player_requested.title() + " Shot Chart")
ax.zaxis.set_major_locator(LinearLocator(10))
ax.zaxis.set_major_formatter('{x:.02f}')
ax.view_init(90, 0)

fig.colorbar(surf, shrink=0.5, aspect=5)

plt.show()