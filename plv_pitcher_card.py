import streamlit as st
import datetime
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.dates as mdates
import seaborn as sns

from datetime import date, timedelta
from matplotlib import colors
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Arc
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                               AutoMinorLocator, FuncFormatter)
from mpl_toolkits.axes_grid1 import make_axes_locatable
from PIL import Image

## Set Styling
# Plot Style
pl_white = '#FEFEFE'
pl_background = '#162B50'
pl_text = '#72a3f7'
pl_line_color = '#293a6b'

sns.set_theme(
    style={
        'axes.edgecolor': pl_line_color,
        'axes.facecolor': pl_background,
        'axes.labelcolor': pl_white,
        'xtick.color': pl_white,
        'ytick.color': pl_white,
        'figure.facecolor':pl_background,
        'grid.color': pl_background,
        'grid.linestyle': '-',
        'legend.facecolor':pl_background,
        'text.color': pl_white
     }
    )

# Marker Style
marker_colors = {
    'FF':'#d22d49', 
    'SI':'#c57a02',
    'FS':'#00a1c5',  
    'FC':'#933f2c', 
    'SL':'#9300c7', 
    'CU':'#3c44cd',
    'CH':'#07b526', 
    'KN':'#999999',
    'SC':'#999999', 
    'UN':'#999999', 
}

marker_list = {
    'FF':'^', 
    'SI':'v', 
    'FC':'D', 
    'FS':'o', 
    'SL':'s',
    'CH':'X', 
    'CU':'P',
    'SC':'*', 
    'KN':'*', 
    'UN':'*'
}

# Pitch Names
pitch_names = {
    'FF':'Four-Seamer', 
    'SI':'Sinker',
    'FS':'Splitter',  
    'FC':'Cutter', 
    'SL':'Slider', 
    'CU':'Curveball',
    'CH':'Changeup', 
    'KN':'Knuckleball',
    'SC':'Screwball', 
    'UN':'Unknown', 
}

# General constants for formatting charts and sizing
y_lim = 5.5
y_bot = -1
sz_bot = 1.5
sz_top = 3.5

# PLV Color Norm
# norm = colors.TwoSlopeNorm(vmin=0, 
#                            vcenter=5,
#                            vmax=10)
bounds = np.linspace(3.5, 6.5, 4)
norm = colors.BoundaryNorm(boundaries=bounds, ncolors=256)

game_norm = colors.TwoSlopeNorm(vmin=4, 
                                vcenter=5,
                                vmax=6)

logo = Image.open('PL_Logo.png')

# Date Formatter
def x_ticks_format(ax,game_dates,scale_val):
  if len(game_dates.unique()) == 1:
    ax.tick_params(left=False, bottom=False, labelsize=round(10*scale_val))
    ax.set_xlim(game_dates.min() - datetime.timedelta(days=7),game_dates.min() + datetime.timedelta(days=7))
    ax.set_xticks(game_dates.unique())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b\n%-d'))
  elif (len(game_dates.unique())<10) & (game_dates.min()+datetime.timedelta(days=90)>=game_dates.max()):
    ax.tick_params(left=False, bottom=False, labelsize=round(10*scale_val))
    ax.set_xticks([x for x in game_dates.unique()])
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b\n%-d'))
  else:
    ax.tick_params(left=False, labelsize=round(10*scale_val))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3, maxticks=8))
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(mdates.AutoDateLocator(minticks=3, maxticks=8),show_offset=False))

# Year
years = [2022,2021,2020]
year = st.radio('Choose a year:', years)

# Load Data
def load_data():
    file_name = f'https://github.com/Blandalytics/PLV_viz/blob/main/data/{year}_PLV_App_Data.parquet?raw=true'
    df = pd.read_parquet(file_name).sort_values('pitch_id')
    return df
plv_df = load_data()

# Player
players = list(plv_df['pitchername'].unique())
default_ix = players.index('Sandy Alcantara')
player = st.selectbox('Choose a player:', players, index=default_ix)

pitch_list = list(plv_df
                .loc[(plv_df['pitchername']==player)# &
                     #plv_df['b_hand'].isin(hand_map[handedness])
                    ]
                .groupby('pitchtype',as_index=False)
                ['pitch_id']
                .count()
                .dropna()
                .sort_values('pitch_id', ascending=False)
                .query(f'pitch_id >= {50}')
                ['pitchtype']
                )

def game_chart(graph_data, game_ax, days=30):
  # Per game/appearance chart
  game_ax.grid(visible=True, which='major', axis='y', color='#FEFEFE', alpha=0.1)
  
  date_min = graph_data['game_played'].max()-datetime.timedelta(days=days)
  
  graph_data = graph_data.loc[graph_data['game_played']>=date_min]

  game_min = graph_data.groupby(['game_played','pitchername'])['PLV'].mean().min()
  game_max = graph_data.groupby(['game_played','pitchername'])['PLV'].mean().max()
  
  # Subtle line to connect the dots
  sns.lineplot(data=graph_data.groupby(['game_played','pitchername'],as_index=False)[['PLV','appearance']].mean(), 
               x='game_played', 
               y='PLV',
               style='pitchername',
               color='#FEFEFE',
               linewidth=2,
               alpha=0.1,
               ax=game_ax,
               legend=False
              )

  # Dots
  sns.scatterplot(data=graph_data.groupby('game_played',as_index=False)[['PLV','appearance']].mean(), 
                  x='game_played', 
                  y='PLV', 
                  s=150, 
                  edgecolor=None, 
                  hue='PLV', 
                  hue_norm=game_norm, 
                  palette='vlag', 
                  alpha=0.8,
                  ax=game_ax,
                  legend=False)

  # League Average line
  game_ax.axhline(5, color='#FEFEFE', linewidth=2, linestyle='--', alpha=0.5)
  
  game_ax.set(xlabel=None, ylabel=None, ylim=(min([4,game_min-0.1]),
                                              max([6,game_max+0.1])))
  x_ticks_format(game_ax,graph_data['game_played'],1.5)
  game_ax.set_yticks([int(x*2)/2 for x in game_ax.get_yticks()])
  game_ax.tick_params(left=False)
  game_ax.set_title(f'PLV per Game\n(Last {days} Days)', fontsize=18)
  
def pitch_qual_charts(graph_data,pitch_plot_ax,qual):
    # Plot of individual pitches
    sns.scatterplot(data=graph_data.loc[(graph_data['p_z']<=y_lim-0.5) &
                                        (graph_data['p_z']>-0.5) &
                                        (graph_data['p_x']>=-2.75) &
                                        (graph_data['pitch_qual']==qual)], 
                    x='p_x', 
                    y='p_z', 
                    s=100, 
                    style='pitchtype',
                    hue='PLV_clip',
                    palette='vlag',
                    hue_norm=norm,
                    markers=marker_list,
                    edgecolor='#293a6b',
                    alpha=1,
                    ax=pitch_plot_ax,
                    legend=False
                    )

    # Strike zone outline
    pitch_plot_ax.axvline(10/12, ymin=(sz_bot-y_bot)/(y_lim-y_bot), ymax=(sz_top-y_bot)/(y_lim-y_bot), color='black', linewidth=4)
    pitch_plot_ax.axvline(-10/12, ymin=(sz_bot-y_bot)/(y_lim-y_bot), ymax=(sz_top-y_bot)/(y_lim-y_bot), color='black', linewidth=4)
    pitch_plot_ax.axhline(sz_top, xmin=26/72, xmax=46/72, color='black', linewidth=4)
    pitch_plot_ax.axhline(sz_bot, xmin=26/72, xmax=46/72, color='black', linewidth=4)

    pitch_plot_ax.set(xlabel=None, xlim=(-3,3), ylabel=None, ylim=(y_bot,y_lim))
    pitch_plot_ax.set_xticklabels([])
    pitch_plot_ax.set_yticklabels([])
    pitch_plot_ax.tick_params(left=False, bottom=False)
#     pitch_plot_ax.text(0.75,y_lim-0.6,"PLV per Pitch", ha='center', va='bottom', fontsize=round(12*scale_val), 
#              bbox=dict(facecolor='#162B50', alpha=0.75, edgecolor='#162B50'))
#     pitch_plot_ax.text(0.75,y_lim-0.7,"(From Pitcher's Perspective)", ha='center', va='top', fontsize=round(10*scale_val), alpha=0.7,
#              bbox=dict(facecolor='#162B50', alpha=0.75, edgecolor='#162B50'))

def plv_card(pitch_threshold=200,scale_val=1.5):
  # Create df for only the pitcher's pitches
  graph_data = plv_df.loc[plv_df['pitchername']==player].iloc[::-1].reset_index(drop=True)
  graph_data['p_x'] = graph_data['p_x'].mul(-1) # To convert to pitcher's perspective
  graph_data['PLV_clip'] = np.clip(graph_data['PLV'], a_min=0, a_max=10)
  graph_data['appearance'] = graph_data['mlb_game_id'].rank(method='dense')

  # Update the pitch count threshold if the pitcher has a low season pitch count
  pitch_threshold = min(pitch_threshold,graph_data.shape[0])

  # Strikeouts and Walks need their own, as they're conditional
  # Card size
  fig = plt.figure(figsize=(7.5*scale_val,10.5*scale_val))

  # Parameters to divide card
  grid_height = 10
  pitch_feats = 8

  # Divide card into tiles
  grid = plt.GridSpec(grid_height, 6, wspace=0.1*scale_val, hspace=0.5*scale_val,
                      height_ratios=[1.5]+[7/pitch_feats]*(pitch_feats)+[1])

  # Title of card (name, etc)
  title_ax = plt.subplot(grid[0, 2:-2])
  title_ax.text(0,0,"{}'s\n{} PLV Card".format(player,year), 
                ha='center', va='center', 
                fontsize=round(16*scale_val),
                bbox=dict(facecolor='#162B50', 
                          alpha=0.6, 
                          edgecolor='#162B50'))
  title_ax.set(xlabel=None, xlim=(-1,1), ylabel=None, ylim=(-1,1))
  title_ax.set_xticklabels([])
  title_ax.set_yticklabels([])
  title_ax.tick_params(left=False, bottom=False)
  
  # Avg PLV
  plv_ax = plt.subplot(grid[1, 0])
  plv_ax.text(0,0,"Avg PLV\n{:.3}".format(graph_data['PLV'].mean()), 
                ha='center', va='center', 
                fontsize=round(18*scale_val),
                bbox=dict(facecolor='#162B50', 
                          alpha=0.6, 
                          edgecolor='#162B50'))
  plv_ax.set(xlabel=None, xlim=(-1,1), ylabel=None, ylim=(-1,1))
  plv_ax.set_xticklabels([])
  plv_ax.set_yticklabels([])
  plv_ax.tick_params(left=False, bottom=False)
  
  game_chart(graph_data,plt.subplot(grid[1:4, 4:]))
  
  x_loc = 0
  y_loc = 2
  qual_bins = [-20,4.5,5.5,20]
  qual_labels = ['BP','AP','QP']
  graph_data['pitch_qual'] = pd.cut(graph_data['PLV_clip'],bins=qual_bins,labels=qual_labels)

  for qual in qual_labels:
    pitch_plot_ax = plt.subplot(grid[y_loc:,y_loc+2 x_loc:x_loc+2])
    pitch_qual_charts(graph_data,pitch_plot_ax,qual)
    x_loc += 2
    y_loc += 2

#   # Add custom legend for markers
#   legend_markers = [Line2D([],[],
#                            color='#FEFEFE',
#                            label=x,
#                            marker=marker_list[x],
#                            markeredgecolor=pl_line_color,
#                            markeredgewidth=round(scale_val),
#                            markersize=round(10*scale_val),
#                            linestyle='None') 
#                     for x in pitch_list]

#   pitch_plot_ax.legend(loc=(0.01,0.05),
#              handles=legend_markers,
#              edgecolor='#162B50',
#              framealpha=0.5, fontsize=round(12*scale_val)
#              )

#   # Colorbar for pitch plot
#   cb_ax = plt.subplot(grid[5:9, 5])
#   sm = plt.cm.ScalarMappable(cmap='vlag', norm=norm)
#   sm.set_array([])
#   fig.colorbar(sm,
#                cax=cb_ax
#               )
#   cb_ax.tick_params(labelsize=round(10*scale_val))
  
  # Chart ownership (PitcherList)
  pl_ax = plt.subplot(grid[0, :2])
  pl_ax.imshow(logo)
  pl_ax.axis('off')

#   # Viz Credit
#   credit_ax = plt.subplot(grid[9:, 5:])
#   credit_ax.text(-0.2,0.6,'Viz by\n@Blandalytics', ha='center', va='center', fontsize=round(8*scale_val),
#            bbox=dict(facecolor='#162B50', alpha=0.6, edgecolor='#162B50'))
#   credit_ax.set(xlabel=None, xlim=(-1,1), ylabel=None, ylim=(-1,1))
#   credit_ax.set_xticklabels([])
#   credit_ax.set_yticklabels([])
#   credit_ax.tick_params(left=False, bottom=False)

  # Box the Pitchtype Charts
  fig.add_artist(Line2D([0.125, 0.302], [0.8, 0.8], linewidth=round(2*scale_val)))
  fig.add_artist(Line2D([0.125, 0.125], [0.125, 0.8], linewidth=round(2*scale_val)))
  fig.add_artist(Line2D([0.302, 0.302], [0.125, 0.8], linewidth=round(2*scale_val)))
  fig.add_artist(Line2D([0.125, 0.302], [0.125, 0.125], linewidth=round(2*scale_val)))

  #Box the games
  fig.add_artist(Line2D([0.32, 0.94], [0.8, 0.8], linewidth=round(2*scale_val))) # Top
  fig.add_artist(Line2D([0.32, 0.32], [0.546, 0.8], linewidth=round(2*scale_val))) # Left
  fig.add_artist(Line2D([0.94, 0.94], [0.546, 0.8], linewidth=round(2*scale_val))) # Right
  fig.add_artist(Line2D([0.32, 0.94], [0.546, 0.546], linewidth=round(2*scale_val))) # Bottom

  #Box the pitch chart
  fig.add_artist(Line2D([0.32, 0.94], [0.536, 0.536], linewidth=round(2*scale_val)))
  fig.add_artist(Line2D([0.32, 0.32], [0.125, 0.536], linewidth=round(2*scale_val)))
  fig.add_artist(Line2D([0.94, 0.94], [0.125, 0.536], linewidth=round(2*scale_val)))
  fig.add_artist(Line2D([0.32, 0.94], [0.125, 0.125], linewidth=round(2*scale_val)))

  sns.despine(left=True, bottom=True)
  st.pyplot(fig)
plv_card()
