import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import seaborn as sns
import matplotlib.pyplot as plt
from nba_api.stats.static import players
from nba_api.stats.static import teams
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.endpoints import shotchartdetail
from nba_api.stats.library.parameters import SeasonAll
from nba_api.stats.endpoints import leaguedashplayerstats
from nba_api.stats.endpoints import BoxScoreAdvancedV2, BoxScoreTraditionalV2, BoxScoreSummaryV2
from nba_api.stats.endpoints import LeagueGameLog, PlayByPlayV2, ScoreboardV2


team_colors = {
    'ATL': '#E03A3E',
    'BOS': '#007A33',
    'BKN': '#000000',
    'CHA': '#1D1160',
    'CHI': '#CE1141',
    'CLE': '#860038',
    'DAL': '#00538C',
    'DEN': '#0E2240',
    'DET': '#C8102E',
    'GSW': '#1D428A',
    'HOU': '#CE1141',
    'IND': '#002D62',
    'LAC': '#C8102E',
    'LAL': '#552583',
    'MEM': '#5D76A9',
    'MIA': '#98002E',
    'MIL': '#00471B',
    'MIN': '#0C2340',
    'NOP': '#0C2340',
    'NYK': '#F58426',
    'OKC': '#007AC1',
    'ORL': '#0077C0',
    'PHI': '#006BB6',
    'PHX': '#1D1160',
    'POR': '#E03A3E',
    'SAC': '#5A2D81',
    'SAS': '#C4CED4',
    'TOR': '#CE1141',
    'UTA': '#002B5C',
    'WAS': '#E31837'
}



def get_basketball_watch_index(season, start_date=None, end_date=None, num_games=None):
    """
    Create a basketball watch index similar to the football version.
    
    Parameters:
    ----------
    season : str
        Season in format 'YYYY-YY' (e.g., '2022-23')
    start_date : str, optional
        Start date in format 'MM/DD/YYYY'
    end_date : str, optional
        End date in format 'MM/DD/YYYY'
    num_games : int, optional
        Number of most recent games to analyze
        
    Returns:
    -------
    pd.DataFrame
        DataFrame with watch index and component metrics
    """
    # Get game IDs for the specified season and date range
    games_df = LeagueGameLog(season=season).get_data_frames()[0]
    
    # Filter by date if specified
    if start_date:
        start = datetime.strptime(start_date, '%m/%d/%Y')
        games_df = games_df[pd.to_datetime(games_df['GAME_DATE']) >= start]
        
    if end_date:
        end = datetime.strptime(end_date, '%m/%d/%Y')
        games_df = games_df[pd.to_datetime(games_df['GAME_DATE']) <= end]
    
    # Get specified number of games
    if num_games:
        game_ids = games_df['GAME_ID'].unique()[:num_games]
    else:
        game_ids = games_df['GAME_ID'].unique()
    
    results = []
    
    for i, game_id in enumerate(game_ids):
        try:
            print(f"Processing game {i+1}/{len(game_ids)}: {game_id}")
            
            # Basic game information
            game_summary = BoxScoreSummaryV2(game_id=game_id).get_data_frames()
            game_info = game_summary[0]
            line_score = game_summary[1]
            
            # Team stats
            traditional_stats = BoxScoreTraditionalV2(game_id=game_id).get_data_frames()[0]
            advanced_stats = BoxScoreAdvancedV2(game_id=game_id).get_data_frames()[0]
            
            # Play-by-play data
            pbp = PlayByPlayV2(game_id=game_id).get_data_frames()[0]
            
            # Get team IDs and names
            home_team_id = game_info['HOME_TEAM_ID'].iloc[0]
            away_team_id = game_info['VISITOR_TEAM_ID'].iloc[0]
            
            home_team_abbr = line_score[line_score['TEAM_ID'] == home_team_id]['TEAM_ABBREVIATION'].iloc[0]
            away_team_abbr = line_score[line_score['TEAM_ID'] == away_team_id]['TEAM_ABBREVIATION'].iloc[0]
            
            game_date = game_info['GAME_DATE_EST'].iloc[0]
            
            # SCORING METRICS
            # ---------------------------------------
            
            # Total score and pace
            home_score = int(line_score[line_score['TEAM_ID'] == home_team_id]['PTS'].iloc[0])
            away_score = int(line_score[line_score['TEAM_ID'] == away_team_id]['PTS'].iloc[0])
            total_score = home_score + away_score
            
            # Points per possession
            home_poss = advanced_stats[advanced_stats['TEAM_ID'] == home_team_id]['POSS'].mean()
            away_poss = advanced_stats[advanced_stats['TEAM_ID'] == away_team_id]['POSS'].mean()
            avg_poss = (home_poss + away_poss) / 2
            pts_per_poss = total_score / avg_poss if avg_poss > 0 else 0
            
            # 3-POINT METRICS
            # ---------------------------------------
            home_3pm = int(traditional_stats[traditional_stats['TEAM_ID'] == home_team_id]['FG3M'].sum())
            away_3pm = int(traditional_stats[traditional_stats['TEAM_ID'] == away_team_id]['FG3M'].sum())
            threes_made = home_3pm + away_3pm
            
            home_3pa = int(traditional_stats[traditional_stats['TEAM_ID'] == home_team_id]['FG3A'].sum())
            away_3pa = int(traditional_stats[traditional_stats['TEAM_ID'] == away_team_id]['FG3A'].sum())
            threes_attempted = home_3pa + away_3pa
            
            three_pt_pct = threes_made / threes_attempted if threes_attempted > 0 else 0
            
            # EFFICIENCY METRICS
            # ---------------------------------------
            # True Shooting
            home_ts = advanced_stats[advanced_stats['TEAM_ID'] == home_team_id]['TS_PCT'].mean()
            away_ts = advanced_stats[advanced_stats['TEAM_ID'] == away_team_id]['TS_PCT'].mean()
            avg_ts = (home_ts + away_ts) / 2
            
            # COMPETITIVENESS METRICS
            # ---------------------------------------
            # Final score difference
            score_diff = abs(home_score - away_score)
            closeness = 1 - (score_diff / total_score if total_score > 0 else 0)
            
            # Calculate lead changes from play-by-play data
            lead_changes = 0
            last_leader = None
            
            # Filter for scoring plays
            scoring_plays = pbp[pbp['SCORE'].notna()]
            
            for _, play in scoring_plays.iterrows():
                if isinstance(play['SCORE'], str) and '-' in play['SCORE']:
                    try:
                        score_parts = play['SCORE'].split(' - ')
                        if len(score_parts) == 2:
                            away_score_pbp = int(score_parts[0])
                            home_score_pbp = int(score_parts[1])
                            
                            current_leader = None
                            if home_score_pbp > away_score_pbp:
                                current_leader = 'HOME'
                            elif away_score_pbp > home_score_pbp:
                                current_leader = 'AWAY'
                            
                            if current_leader and last_leader and current_leader != last_leader:
                                lead_changes += 1
                            
                            last_leader = current_leader
                    except:
                        pass
            
            # Calculate clutch time (4th quarter/OT within 5 points)
            late_game = pbp[(pbp['PERIOD'] >= 4)]
            clutch_plays = 0
            total_late_plays = len(late_game)
            
            for _, play in late_game.iterrows():
                if isinstance(play['SCORE'], str) and '-' in play['SCORE']:
                    try:
                        score_parts = play['SCORE'].split(' - ')
                        if len(score_parts) == 2:
                            away_score_pbp = int(score_parts[0])
                            home_score_pbp = int(score_parts[1])
                            diff = abs(home_score_pbp - away_score_pbp)
                            if diff <= 5:
                                clutch_plays += 1
                    except:
                        pass
            
            clutch_time = clutch_plays / total_late_plays if total_late_plays > 0 else 0
            
            # Check if the game went to overtime
            overtime = 1 if game_info['GAME_STATUS_TEXT'].iloc[0].startswith('Final/OT') else 0
            
            # HIGHLIGHT METRICS
            # ---------------------------------------
            # Dunks and blocks (approximation)
            dunks = 0
            blocks = int(traditional_stats['BLK'].sum())
            
            # Get counts for highlight moments from play-by-play
            for _, play in pbp.iterrows():
                description = str(play['HOMEDESCRIPTION']).lower() if not pd.isna(play['HOMEDESCRIPTION']) else ""
                description += str(play['VISITORDESCRIPTION']).lower() if not pd.isna(play['VISITORDESCRIPTION']) else ""
                
                if 'dunk' in description:
                    dunks += 1
            
            # PACE & CHAOS METRICS
            # ---------------------------------------
            # Turnovers
            home_to = int(traditional_stats[traditional_stats['TEAM_ID'] == home_team_id]['TO'].sum())
            away_to = int(traditional_stats[traditional_stats['TEAM_ID'] == away_team_id]['TO'].sum())
            turnovers = home_to + away_to
            
            # Steals 
            steals = int(traditional_stats['STL'].sum())
            
            # Free throws
            free_throws_attempted = int(traditional_stats['FTA'].sum())
            
            # Net rating difference
            home_net = advanced_stats[advanced_stats['TEAM_ID'] == home_team_id]['NET_RATING'].mean()
            away_net = advanced_stats[advanced_stats['TEAM_ID'] == away_team_id]['NET_RATING'].mean()
            net_rating_diff = abs(home_net - away_net)
            
            # STAR POWER METRICS
            # ---------------------------------------
            # Player with highest Game Score
            player_traditional = traditional_stats[traditional_stats['MIN'] >= 15]  # Min 15 minutes played
            
            # Calculate Game Score (simplified version of John Hollinger's formula)
            player_traditional['GAME_SCORE'] = (
                player_traditional['PTS'] + 
                0.4 * player_traditional['FGM'] - 
                0.7 * player_traditional['FGA'] - 
                0.4 * (player_traditional['FTA'] - player_traditional['FTM']) + 
                0.7 * player_traditional['OREB'] + 
                0.3 * player_traditional['DREB'] + 
                player_traditional['STL'] + 
                0.7 * player_traditional['AST'] + 
                0.7 * player_traditional['BLK'] - 
                0.4 * player_traditional['PF'] - 
                player_traditional['TO']
            )
            
            max_game_score = player_traditional['GAME_SCORE'].max()
            star_player = player_traditional[player_traditional['GAME_SCORE'] == max_game_score]['PLAYER_NAME'].iloc[0]
            
            # Collect all metrics
            game_data = {
                'game_id': game_id,
                'game_date': game_date,
                'home_team': home_team_abbr,
                'away_team': away_team_abbr,
                'home_score': home_score,
                'away_score': away_score,
                'total_score': total_score,
                'pts_per_poss': pts_per_poss,
                'threes_made': threes_made,
                'threes_attempted': threes_attempted,
                'three_pt_pct': three_pt_pct,
                'avg_ts': avg_ts,
                'lead_changes': lead_changes,
                'score_diff': score_diff,
                'closeness': closeness,
                'clutch_time': clutch_time,
                'overtime': overtime,
                'dunks': dunks,
                'blocks': blocks,
                'turnovers': turnovers,
                'steals': steals,
                'free_throws_attempted': free_throws_attempted,
                'net_rating_diff': net_rating_diff,
                'star_player': star_player,
                'max_game_score': max_game_score
            }
            
            results.append(game_data)
            
            # Avoid hitting API rate limits
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error processing game {game_id}: {e}")
    
    # Create DataFrame from results
    df = pd.DataFrame(results)
    
    if len(df) == 0:
        return df
    
    # Calculate percentile ranks for key metrics
    rank_columns = [
        'total_score', 'pts_per_poss', 'threes_made', 'three_pt_pct', 
        'avg_ts', 'lead_changes', 'closeness', 'clutch_time',
        'overtime', 'dunks', 'blocks', 'turnovers', 'steals',
        'free_throws_attempted', 'max_game_score'
    ]
    
    # Some metrics are better when lower
    inverse_rank = ['turnovers']
    
    for col in rank_columns:
        if col in df.columns:  # Check if column exists
            if col in inverse_rank:
                df[f'PR_{col}'] = 1 - df[col].rank(pct=True)
            else:
                df[f'PR_{col}'] = df[col].rank(pct=True)
    
    # Calculate Watch Index components
    df['Scoring'] = (
        df.get('PR_total_score', 0) + 
        df.get('PR_pts_per_poss', 0) + 
        df.get('PR_threes_made', 0) + 
        df.get('PR_avg_ts', 0)
    ) / 4
    
    df['Competitiveness'] = (
        2 * df.get('PR_lead_changes', 0) + 
        2 * df.get('PR_closeness', 0) + 
        2 * df.get('PR_clutch_time', 0) + 
        1 * df.get('PR_overtime', 0)
    ) / 7
    
    df['Highlights'] = (
        df.get('PR_dunks', 0) + 
        df.get('PR_blocks', 0) + 
        df.get('PR_steals', 0)
    ) / 3
    
    df['Pace'] = (
        df.get('PR_pts_per_poss', 0) + 
        df.get('PR_turnovers', 0) + 
        df.get('PR_free_throws_attempted', 0) * 0.5
    ) / 2.5
    
    df['StarPower'] = df.get('PR_max_game_score', 0)
    
    # Final Watch Index
    df['WatchIndex'] = (
        2 * df['Scoring'] + 
        3 * df['Competitiveness'] + 
        1.5 * df['Highlights'] + 
        1 * df['Pace'] + 
        0.5 * df['StarPower']
    ) / 8
    
    # Sort by Watch Index
    df = df.sort_values('WatchIndex', ascending=False).reset_index(drop=True)
    
    return df

def get_recent_games_watch_index(days_back=7):
    """
    Get watch index for games in the recent past
    
    Parameters:
    ----------
    days_back : int
        How many days to look back
    
    Returns:
    -------
    pd.DataFrame
        DataFrame with watch index for recent games
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Format dates for API
    start_str = start_date.strftime('%m/%d/%Y')
    end_str = end_date.strftime('%m/%d/%Y')
    
    # Determine season based on date
    year = end_date.year
    month = end_date.month
    if month >= 10:  # New season starts in October
        season = f"{year}-{str(year+1)[-2:]}"
    else:
        season = f"{year-1}-{str(year)[-2:]}"
    
    return get_basketball_watch_index(season, start_date=start_str, end_date=end_str)

def get_watchability_preview(date_str=None):
    """
    Preview upcoming games with predicted watchability
    
    Parameters:
    ----------
    date_str : str
        Date in format 'MM/DD/YYYY', defaults to today
    
    Returns:
    -------
    pd.DataFrame
        DataFrame with predicted watch index for upcoming games
    """
    if date_str is None:
        date = datetime.now()
    else:
        date = datetime.strptime(date_str, '%m/%d/%Y')
    
    # Format for the API
    month = date.month
    day = date.day
    year = date.year
    
    # Get scoreboard for the given day
    scoreboard = ScoreboardV2(month=month, day=day, year=year).get_data_frames()
    game_header = scoreboard[0]
    
    # Extract team info
    team_ids = pd.concat([
        game_header[['HOME_TEAM_ID', 'VISITOR_TEAM_ID']]
    ]).values.flatten()
    
    # We would need previous results to predict game watchability
    # This is a simplified approach that would need refining with historical data
    
    # Return a simple DataFrame with game info
    games_preview = pd.DataFrame({
        'game_id': game_header['GAME_ID'],
        'home_team': game_header['HOME_TEAM_ABBREVIATION'],
        'away_team': game_header['VISITOR_TEAM_ABBREVIATION'],
        'game_time': game_header['GAME_STATUS_TEXT'],
        # Actual watch index would need prediction model
    })
    
    return games_preview

# Example usage
if __name__ == "__main__":
    # Get watch index for recent NBA games
    recent_games = get_recent_games_watch_index(days_back=14)
    
    # Display top 10 most watchable games
    print("Top 10 Most Watchable Recent Games:")
    if len(recent_games) > 0:
        top_games = recent_games[['game_date', 'home_team', 'away_team', 
                                 'home_score', 'away_score', 'WatchIndex', 
                                 'lead_changes', 'clutch_time', 'overtime']][:10]
        print(top_games)
    else:
        print("No games found in the specified period.")
    
    # Preview upcoming games
    upcoming = get_watchability_preview()
    print("\nUpcoming Games:")
    print(upcoming)