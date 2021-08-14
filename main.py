import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Wedge
import pandas as pd
from matplotlib.ticker import LinearLocator
import ssl
from nba_api.stats.endpoints import shotchartdetail
from nba_api.stats.static import players
import json
import scipy.ndimage
import mpl_toolkits.mplot3d.art3d as art3d
ssl._create_default_https_context = ssl._create_unverified_context


player_dict = players.get_players()
player_requested = input("NBA Player: ")
player_selected = [p for p in player_dict if p["full_name"].lower() == player_requested.lower()][0]
player_selected_id = player_selected["id"]

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

raw_data = json.loads(response.get_json())
results = raw_data['resultSets'][0]
headers = results['headers']
rows = results['rowSet']
df = pd.DataFrame(rows)
df.columns = headers

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
    return float(made/total) * 100

def calc_total_made(arr):
    made = 0
    if len(arr) == 0:
        return 0
    for index in arr:
        made += df['SHOT_MADE_FLAG'][index]
    return made

fg_pct = np.array([])
for key in reg_dict:
    fg_pct = np.append(fg_pct, calc_fg_pct(reg_dict[key]))

fg_pct = np.flipud(np.reshape(fg_pct, (50, 50)))

total_made = np.array([])
for key in reg_dict:
    total_made = np.append(total_made, calc_total_made(reg_dict[key]))

total_made = np.flipud(np.reshape(total_made, (50, 50)))

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
        art3d.pathpatch_2d_to_3d(element, z=0, zdir = 'z')

    return ax

draw_court(outer_lines=True, color='black')
r = 23.75
y0 = 25
x0 = 4.75

# Theta varies only between pi/2 and 3pi/2. to have a half-circle
theta = np.linspace(22*np.pi/180., 158*np.pi/180., 1000)

x = r*np.sin(theta) + x0 # x=0
y = r*np.cos(theta) + y0 # y - y0 = r*cos(theta)
z = np.zeros_like(theta) # z - z0 = r*sin(theta)

ax.plot(x, y, z, color = 'black', linewidth = 2, zorder = 10)
sigma = [1.5, 1.5]

smooth = scipy.ndimage.filters.gaussian_filter(fg_pct, sigma)

surf = ax.plot_surface(x_data, y_data, smooth, cmap='jet', linewidth=0, antialiased=True)

ax.set_title(player_requested.title() + " Shot Chart")
ax.zaxis.set_major_locator(LinearLocator(10))
# A StrMethodFormatter is used automatically
ax.zaxis.set_major_formatter('{x:.02f}')
ax.view_init(90, 0)

fig.colorbar(surf, shrink=0.5, aspect=5)

plt.show()

