import streamlit as st
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

## Set Styling
# Plot Style
pl_white = '#FEFEFE'
pl_background = '#162B50'
pl_text = '#72a3f7'
pl_line_color = '#293a6b'

sns.set_theme(
    style={
        'axes.edgecolor': pl_background,
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

# Year
years = [2022,2021,2020]
year = st.radio('Choose a year:', years)

seasonal_constants = pd.read_csv('https://github.com/Blandalytics/PLV_viz/blob/main/data/plv_seasonal_constants.csv?raw=true').set_index('year')

@st.cache
# Load Data
def load_data(year):
    df = pd.DataFrame()
    for chunk in [1,2,3]:
        file_name = f'https://github.com/Blandalytics/PLV_viz/blob/main/data/{year}_PLV_App_Data-{chunk}.parquet?raw=true'
        df = pd.concat([df,
                        pd.read_parquet(file_name)[['pitchername','pitcher_mlb_id','pitch_id',
                                                    'p_hand','b_hand','pitchtype','PLV']]
                       ])
    df = (df
          .sort_values('pitch_id')
          .astype({'pitch_id':'int',
                   'pitcher_mlb_id':'int'})
          .query(f'pitchtype not in {["KN","SC"]}')
          .reset_index(drop=True)
         )
    
    df['pitch_runs'] = df['PLV'].mul(seasonal_constants.loc[year]['run_plv_coef']).add(seasonal_constants.loc[year]['run_plv_constant'])
    
    df['pitch_quality'] = 'Average'
    df.loc[df['PLV']>=5.5,'pitch_quality'] = 'Quality'
    df.loc[df['PLV']<4.5,'pitch_quality'] = 'Bad'

    for qual in df['pitch_quality'].unique():
      df[qual+' Pitch'] = 0
      df.loc[df['pitch_quality']==qual,qual+' Pitch'] = 1

    df['QP-BP'] = df['Quality Pitch'].sub(df['Bad Pitch'])
    
    return df
plv_df = load_data(year)

def get_ids():
    id_df = pd.DataFrame()
    for chunk in list(range(0,10))+['a','b','c','d','e','f']:
        chunk_df = pd.read_csv(f'https://github.com/chadwickbureau/register/blob/master/data/people-{chunk}.csv?raw=true')
        id_df = pd.concat([id_df,chunk_df])
    return id_df[['key_mlbam','key_fangraphs']].dropna().astype('int') 

st.title("Season PLA")
st.write('- ***Pitch Level Average (PLA)***: Value of all pitches (ERA scale), using IP and the total predicted run value of pitches thrown.')
st.write('- ***Pitchtype PLA***: Value of a given pitch type (ERA-scale), using total predicted run values and an IP proxy for that pitch type (pitch usage % * Total IP).')

pitch_threshold = 200

# Num Pitches threshold
pitch_min_1 = st.number_input(f'Min # of Pitches:',
                              min_value=pitch_threshold, 
                              max_value=2000,
                              step=50, 
                              value=500)

# Season data
pla_df = pd.read_csv(f'https://github.com/Blandalytics/PLV_viz/blob/main/data/PLA_{year}.csv?raw=true', encoding='latin1')
pla_df = pla_df.loc[pla_df['# Pitches'] >= pitch_min_1].set_index('Pitcher').copy()
# pla_df = pla_df.rename(columns={'# Pitches':'Num_Pitches'}).query(f'Num_Pitches >= {pitch_min_1}')

format_cols = ['PLA','FF','SI','SL','CH','CU','FC','FS']

fill_val = pla_df[format_cols].max().max()+0.01

def pitchtype_color(s):
    return f"background-color: {marker_colors[s]}" if s in list(marker_colors.keys()) else None

st.write('At least 20 pitches thrown, per pitch type. Table is sortable.')
st.dataframe(pla_df
             .astype({'# Pitches': 'int'})
             .fillna(fill_val)
             .style
             .format(precision=2, thousands=',')
             .background_gradient(axis=0, vmin=2, vmax=6,
                                  cmap="vlag_r", subset=format_cols)
             .applymap(lambda x: 'color: transparent; background-color: transparent' if x==fill_val else '')
             #.applymap_index(pitchtype_color, axis='columns') # Apparently Streamlit doesn't style headers
            )

st.title("PLV Distributions")

## Selectors
# Player
players = list(plv_df
               .groupby('pitchername', as_index=False)
               [['pitch_id','PLV']]
               .agg({
                   'pitch_id':'count',
                   'PLV':'mean'
               })
               .query(f'pitch_id >={pitch_threshold}')
               .sort_values('PLV', ascending=False)
               ['pitchername']
              )
default_ix = players.index('Sandy Alcantara')
player = st.selectbox('Choose a player:', players, index=default_ix)

# Hitter Handedness
handedness = st.select_slider(
    'Hitter Handedness',
    options=['Left', 'All', 'Right'],
    value='All')

# Pitcher Handedness
if handedness=='All':
    pitcher_hand = ['L','R']
else:
    pitcher_hand = list(plv_df.loc[(plv_df['pitchername']==player),'p_hand'].unique())

hand_map = {
    'Left':['L'],
    'All':['L','R'],
    'Right':['R']
}

pitches_thrown = plv_df.loc[(plv_df['pitchername']==player) &
                            plv_df['b_hand'].isin(hand_map[handedness])].shape[0]

st.write('Distribution of PLV for all pitches thrown by {}{} in {}'.format(player,
                                                                           '' if handedness=='All' else f' to {handedness} Handed Hitters',
                                                                           year))
st.write('Pitches Thrown: {:,}'.format(pitches_thrown))

if pitches_thrown >= pitch_threshold:
    pitch_type_thresh = 20
    pitch_list = list(plv_df
                .loc[(plv_df['pitchername']==player) &
                     plv_df['b_hand'].isin(hand_map[handedness])]
                .groupby('pitchtype',as_index=False)
                ['pitch_id']
                .count()
                .dropna()
                .sort_values('pitch_id', ascending=False)
                .query(f'pitch_id >= {pitch_type_thresh}')
                ['pitchtype']
                )

## Chart function
    def arsenal_dist():
        # Subplots based off of # of pitchtypes
        fig, axs = plt.subplots(len(pitch_list),1,figsize=(8,8), sharex='row', sharey='row', constrained_layout=True)
        ax_num = 0
        max_count = 0
        for pitch in pitch_list:
            # Data just for that pitch type
            chart_data = plv_df.loc[(plv_df['pitchtype']==pitch) &
                                    plv_df['b_hand'].isin(hand_map[handedness])].copy()
            # Restrict to 0-10
            chart_data['PLV_clip'] = np.clip(chart_data['PLV'], a_min=0, a_max=10)
            num_pitches = chart_data.loc[chart_data['pitchername']==player].shape[0]
            
            # Plotting
            sns.histplot(data=chart_data.loc[chart_data['pitchername']==player],
                        x='PLV_clip',
                        hue='pitchtype',
                        palette=marker_colors,
                        binwidth=0.5,
                        binrange=(0,10),
                        alpha=1,
                        ax=axs[ax_num],
                        legend=False
                        )
            # Season Avg Line
            axs[ax_num].axvline(chart_data.loc[chart_data['pitchername']==player,'PLV'].mean(),
                                color=marker_colors[pitch],
                                linestyle='--',
                                linewidth=2.5)
            
            # League Avg Line
            axs[ax_num].axvline(chart_data.loc[chart_data['p_hand'].isin(pitcher_hand),'PLV'].mean(), 
                                color='w', 
                                label='Lg. Avg.',
                                alpha=0.5)
            
            # Format Axes Style
            axs[ax_num].get_xaxis().set_visible(False)
            axs[ax_num].get_yaxis().set_visible(False)
            axs[ax_num].set(xlim=(0,10))
            axs[ax_num].set_title('')
            if axs[ax_num].get_ylim()[1] > max_count:
                max_count = axs[ax_num].get_ylim()[1]
            ax_num += 1
            if ax_num==len(pitch_list):
                axs[ax_num-1].get_xaxis().set_visible(True)
                axs[ax_num-1].set_xticks(range(0,11))
                axs[ax_num-1].set(xlabel='')

        # Chart Styling & Add-Ons
        for axis in range(len(pitch_list)):
            # Fix Y-Axis size to most thrown pitch, for all pitches
            axs[axis].set(ylim=(0,max_count*1.025))
            
            num_pitches = plv_df.loc[(plv_df['pitchtype']==pitch_list[axis]) & 
                                     (plv_df['pitchername']==player) &
                                     plv_df['b_hand'].isin(hand_map[handedness])].shape[0]
            pitch_usage = round(num_pitches / plv_df.loc[(plv_df['pitchername']==player) &
                                                         plv_df['b_hand'].isin(hand_map[handedness])].shape[0] * 100,1)
            
            # Define the plot legend
            axs[axis].legend([pitch_names[pitch_list[axis]]+': {:.3}'.format(plv_df.loc[(plv_df['pitchtype']==pitch_list[axis]) & 
                                                                                        (plv_df['pitchername']==player) &
                                                                                        plv_df['b_hand'].isin(hand_map[handedness]),'PLV'].mean()),
                              'Lg. Avg'+': {:.3}'.format(plv_df.loc[(plv_df['pitchtype']==pitch_list[axis]) &
                                                                     plv_df['b_hand'].isin(hand_map[handedness]) &
                                                                     plv_df['p_hand'].isin(pitcher_hand),'PLV'].mean())], 
                             framealpha=0, edgecolor=pl_background, loc=(0,0.4), fontsize=14)
            
            # Pitch Totals
            axs[axis].text(9,max_count*0.425,'{:,} Pitches\n({}%)'.format(num_pitches,
                                                                          pitch_usage),
                           ha='center',va='bottom', fontsize=14)
        
        # Filler for Title
        hand_text = f'{pitcher_hand[0]}HP vs {hand_map[handedness][0]}HB, ' if handedness!='All' else ''

        fig.suptitle("{}'s {} PLV Distributions\n({}>=20 Pitches Thrown)".format(player,year,hand_text),fontsize=16)
        sns.despine(left=True, bottom=True)
        st.pyplot(fig)
    arsenal_dist()
else:
    st.write('Not enough pitches thrown in {} (<{})'.format(year,pitch_threshold))
    
st.title("General Pitch Quality")
st.write('- ***Quality Pitch (QP%)***: Pitch with a PLV >= 5.5')
st.write('- ***Average Pitch (AP%)***: Pitch with 4.5 < PLV < 5.5')
st.write('- ***Bad Pitch (BP%)***: Pitch with a PLV <= 4.5')
st.write('- ***QP-BP%***: Difference between QP and BP. Avg is 7%')

# Num Pitches threshold
pitch_min_2 = st.number_input(f'Min # of Pitches:', 
                            min_value=pitch_threshold, 
                            max_value=plv_df.groupby('pitchername')['pitch_id'].count().max().round(-2)-200,
                            step=50, 
                            value=500)

st.dataframe(plv_df
             .groupby('pitchername')
             [['Quality Pitch','Average Pitch','Bad Pitch','pitch_id']]
             .agg({
                 'Quality Pitch':'mean',
                 'Average Pitch':'mean',
                 'Bad Pitch':'mean',
                 'pitch_id':'count'
             })
             .query(f'pitch_id >={pitch_min_2}')
             .assign(QP_BP=lambda x: x['Quality Pitch'] - x['Bad Pitch'])
             .rename(columns={
                 'Quality Pitch':'QP%',
                 'Average Pitch':'AP%',
                 'Bad Pitch':'BP%',
                 'QP_BP':'QP-BP%',
                 'pitch_id':'# Pitches'
             })
             [['# Pitches','QP%','AP%','BP%','QP-BP%']]
             .mul([1,100,100,100,100])
             .sort_values('QP-BP%', ascending=False)
             .style
             .format(precision=1, thousands=',')
             .background_gradient(axis=0, cmap="vlag", subset=['QP%','QP-BP%'])
             .background_gradient(axis=0, cmap="vlag_r", subset=['BP%'])
            )
 
