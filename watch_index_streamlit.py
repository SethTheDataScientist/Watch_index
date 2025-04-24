import streamlit as st
import pandas as pd
import numpy as np
import pyreadr
from datetime import datetime, timedelta

st.set_page_config(layout="wide", 
    page_title="Sports Watch Index",
    page_icon="🏈/🏀",
    menu_items={
        'About': "Check out my [Portfolio](https://sites.google.com/view/seth-lanza-portfolio/home), Get in touch at Seth.Lanza@gmail.com, Connect on [Linkedin](https://www.linkedin.com/in/sethlanza/), Check my [Twitter](https://x.com/SethDataScience), or Check out my [Github](https://github.com/SethTheDataScientist?tab=repositories)"
    })


st.title("Sports Watch Index")

tab1, tab2 = st.tabs(['NFL Watch Index', 'NBA Watch Index'])
with tab1:
    
    st.header("NFL Watch Index")
    st.write('This is my watch index for the NFL. It takes a selection of filters and then returns a table of the games since the 2012 season and their corresponding watch index. The score is created by a weighted average of a number of features about the game that create metrics about scoring, excitement, and closeness. It is weighted pretty strongly towards closer games with lots of lead changes and a game coming down to the wire.')

    # Read in the watch_index table 
    st.session_state.nfl_watch_index = pyreadr.read_r('WatchData.rds')[None].drop_duplicates()

    
    st.session_state.nfl_watch_index['playoff'] = 0
    st.session_state.nfl_watch_index.loc[(st.session_state.nfl_watch_index.season < 2021) & (st.session_state.nfl_watch_index.week > 17), 'playoff'] = 1
    st.session_state.nfl_watch_index.loc[(st.session_state.nfl_watch_index.season >= 2021) & (st.session_state.nfl_watch_index.week > 18), 'playoff'] = 1

    # Select specific Filters
    st.session_state.nfl_season_filter = st.multiselect("Select a season",  st.session_state.nfl_watch_index.season.unique().tolist(), default=st.session_state.nfl_watch_index.season.unique().tolist())
    st.session_state.nfl_playoff_filter = st.selectbox("Select playoff preference", ['Yes', 'Only', 'No'])
    st.session_state.nfl_team_filter = st.selectbox("Select a team",  ['All'] + sorted(st.session_state.nfl_watch_index.home_team.unique().tolist()))
    st.session_state.nfl_war_filter = st.checkbox("Exlcude games where the QB played poorly (using PFF WAR)")
    st.session_state.nfl_epa_filter = st.checkbox("Exclude games where the offenses performed poorly (using EPA)")
    st.session_state.nfl_QB_filter = st.selectbox("Select a QB you want in the matchup",  ['All'] + st.session_state.nfl_watch_index['player.x'].unique().tolist())
    st.session_state.nfl_QB_filter2 = st.selectbox("Select the other QB you want in the matchup", ['All'] + st.session_state.nfl_watch_index['player.x'].unique().tolist())


    # Generate random game
    st.subheader("Generate Random Game")
    if st.button("Generates a random NFL game from the entire sample"):
        game_ids = st.session_state.nfl_watch_index.game_id.unique()
        shuffled = np.random.permutation(game_ids)
        st.session_state.nfl_random_id = shuffled[0]
        st.session_state.nfl_random_game = st.session_state.nfl_watch_index[st.session_state.nfl_watch_index.game_id == st.session_state.nfl_random_id][['season', 'playoff', 'week', 'home_team', 'away_team', 'PREPA', 'PRWAR', 'PRWacky', 'PRPenalties', 'WatchIndex']]
        
        for col in ['PREPA', 'PRWAR', 'PRWacky', 'PRPenalties', 'WatchIndex']:
            st.session_state.nfl_random_game[col] = round(st.session_state.nfl_random_game[col] *100, 2)
        st.dataframe(st.session_state.nfl_random_game, use_container_width=True)

    st.session_state.nfl_filtered_watch = st.session_state.nfl_watch_index
    st.subheader("Watch Index Table")
    st.write('Wacky and Penalties are metrics trying to categorize what to expect in the game. Wacky includes things like batted passes, interceptions, fumbles, etc. Penalties is based on penalty yardage.')
    st.session_state.nfl_filtered_watch = st.session_state.nfl_filtered_watch[
        st.session_state.nfl_watch_index.season.isin(st.session_state.nfl_season_filter)
    ]

    if st.session_state.nfl_team_filter != 'All':
        st.session_state.nfl_filtered_watch = st.session_state.nfl_filtered_watch[(st.session_state.nfl_filtered_watch.home_team == st.session_state.nfl_team_filter) | (st.session_state.nfl_filtered_watch.away_team == st.session_state.nfl_team_filter)]

    if st.session_state.nfl_playoff_filter == 'Only':
        st.session_state.nfl_filtered_watch = st.session_state.nfl_filtered_watch[st.session_state.nfl_filtered_watch.playoff == 1]

    elif st.session_state.nfl_playoff_filter == 'No':
        st.session_state.nfl_filtered_watch = st.session_state.nfl_filtered_watch[st.session_state.nfl_filtered_watch.playoff == 0]

    if st.session_state.nfl_QB_filter != 'All':
        st.session_state.nfl_filtered_watch = st.session_state.nfl_filtered_watch[(st.session_state.nfl_filtered_watch['player.x'] == st.session_state.nfl_QB_filter) | (st.session_state.nfl_filtered_watch['player.y'] == st.session_state.nfl_QB_filter)]

    if st.session_state.nfl_QB_filter2 != 'All':
        st.session_state.nfl_filtered_watch = st.session_state.nfl_filtered_watch[(st.session_state.nfl_filtered_watch['player.x'] == st.session_state.nfl_QB_filter2) | (st.session_state.nfl_filtered_watch['player.y'] == st.session_state.nfl_QB_filter2)]
    
    if st.session_state.nfl_war_filter:
        st.session_state.nfl_filtered_watch = st.session_state.nfl_filtered_watch[st.session_state.nfl_filtered_watch.PRWAR >= 0.625]

    if st.session_state.nfl_epa_filter:
        st.session_state.nfl_filtered_watch = st.session_state.nfl_filtered_watch[st.session_state.nfl_filtered_watch.PREPA >= 0.75]


    # Select to only columns I want to show
    st.session_state.nfl_filtered_watch = st.session_state.nfl_filtered_watch[['season', 'playoff', 'week', 'home_team', 'away_team', 'PREPA', 'PRWAR', 'PRWacky', 'PRPenalties', 'WatchIndex']].sort_values('WatchIndex', ascending = False)

    for col in ['PREPA', 'PRWAR', 'PRWacky', 'PRPenalties', 'WatchIndex']:
        st.session_state.nfl_filtered_watch[col] = round(st.session_state.nfl_filtered_watch[col] *100, 2)


    st.dataframe(st.session_state.nfl_filtered_watch, use_container_width=True)



with tab2:
    st.header("NBA Watch Index")
    st.write('This is a recreation of my watch index for the NFL. It takes a selection of filters and then returns a table of the games over the past 5 seasons and their corresponding watch index. The score is created by a weighted average of a number of features about the game that create metrics about scoring, excitement, and closeness. It is weighted pretty strongly towards closer games with lots of lead changes and a game coming down to the wire.')

    # Read in the watch_index table 
    st.session_state.watch_index = pd.read_csv('checkpoints/watch_index_all_seasons.csv').drop_duplicates(subset = ['game_id'])

    today = datetime.now()
    st.session_state.formatted_date = today.strftime("%Y-%m-%d")
    # Calculate the date 30 days ago
    thirty_days_ago = today - timedelta(days=30)

    # Convert to string format
    thirty_days_ago_str = thirty_days_ago.strftime("%Y-%m-%d")

    # Select specific Filters
    st.session_state.season_filter = st.multiselect("Select a season", st.session_state.watch_index.season.unique(), default = st.session_state.watch_index.season.unique())
    st.session_state.team_filter = st.selectbox("Select a team", ['All'] + sorted(st.session_state.watch_index.home_team.unique()))

    # Create a checkbox for the user to decide whether to filter recent games
    filter_recent = st.checkbox("Show only recent games (within the last 30 days)")

    # Generate random game
    st.subheader("Generate Random Game")
    if st.button("Generates a random NBA game from the entire sample"):
        game_ids = st.session_state.watch_index.game_id.unique()
        shuffled = np.random.permutation(game_ids)
        st.session_state.random_id = shuffled[0]
        st.session_state.random_game = st.session_state.watch_index[st.session_state.watch_index.game_id == st.session_state.random_id][['season', 'game_date', 'home_team', 'away_team', 'Scoring', 'Competitiveness', 'Highlights', 'WatchIndex']]
        for col in ['Scoring', 'Competitiveness', 'Highlights', 'WatchIndex']:
            st.session_state.random_game[col] = round(st.session_state.random_game[col] *100, 2)
        st.dataframe(st.session_state.random_game, use_container_width=True)


    st.subheader("Watch Index Table")

    st.session_state.filtered_watch = st.session_state.watch_index

    st.session_state.filtered_watch = st.session_state.filtered_watch[
            st.session_state.filtered_watch.season.isin(st.session_state.season_filter)
        ]
    
    if st.session_state.team_filter != 'All':
        st.session_state.filtered_watch = st.session_state.filtered_watch[(st.session_state.filtered_watch.home_team == st.session_state.team_filter) | (st.session_state.filtered_watch.away_team == st.session_state.team_filter)]

    if filter_recent:
        st.session_state.filtered_watch = st.session_state.filtered_watch[st.session_state.filtered_watch.game_date >= thirty_days_ago_str]


    # Select to only columns I want to show
    st.session_state.filtered_watch = st.session_state.filtered_watch[['season', 'game_date', 'home_team', 'away_team', 'Scoring', 'Competitiveness', 'Highlights', 'WatchIndex']].sort_values('WatchIndex', ascending = False)

    for col in ['Scoring', 'Competitiveness', 'Highlights', 'WatchIndex']:
        st.session_state.filtered_watch[col] = round(st.session_state.filtered_watch[col] *100, 2)

    st.dataframe(st.session_state.filtered_watch, use_container_width=True)

