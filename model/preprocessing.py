import pandas as pd
import sqlalchemy
import re
import tqdm
import numpy as np


month_dict = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 
              'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}


class Players:
    columns_needed = ['name', 'id', 'Position', 'Age', 'Nation', 'Shoots', 'Youth Team', 'date_of_birth', 
                      'height', 'weight', 'birth_country', 'birth_city', 'draft_entry', 'nhl_rights', 'draft_team']
    
    @classmethod
    def preprocess(cls, players):
        players['date_of_birth'] = pd.to_datetime(players['Date of Birth'], infer_datetime_format=True, errors='coerce')
        players['height'] = players['Height'].map(lambda x: x.split(' cm')[0])
        players['height'] = pd.to_numeric(players['height'], errors='coerce')
        players['weight'] = players['Weight'].map(lambda x: x.split(' kg')[0])
        players['weight'] = pd.to_numeric(players['weight'], errors='coerce')
        players['birth_country'] = players['Place of Birth'].map(lambda x: x.split(', ')[-1])
        players['birth_city'] = players['Place of Birth'].map(lambda x: x.split(', ')[0])
        players['draft_entry'] = players['Drafted'].map(lambda x: re.findall(r'#(\d+) overall', str(x)))
        players['draft_entry'] = pd.to_numeric(players['draft_entry'].map(lambda x: x[0] if x else None), errors='coerce')
        players['draft_team'] = players['Drafted'].map(lambda x: re.findall(r'by (.*)', str(x)))
        players['draft_team'] = players['draft_team'].map(lambda x: x[0] if x else None)
        players['nhl_rights'] = players['NHL Rights'].map(lambda x: str(x).split(' /')[0])
        players = players[cls.columns_needed]
        players.columns = players.columns.str.lower()
        return players
        
        
class Seasons:
    columns_needed = ['season', 'team', 'league', 'games', 'goals', 'assists', 'points', 'penalty', 'plus_minus', 'player_id', 'postseason_flag']
    
    @classmethod
    def preprocess(cls, season):
        playoff_columns = ['S', 'Team', 'League', 'GP.1', 'G.1', 'A.1', 'TP.1', 'PIM.1', '+/-.1', 'player_id']
        regular_columns = ['S', 'Team', 'League', 'GP', 'G', 'A', 'TP', 'PIM', '+/-', 'player_id']
        playoff = season.loc[season['POST'] != 'nan', playoff_columns].copy()
        regular = season[regular_columns].copy()
        playoff.columns = regular_columns
        regular['postseason_flag'] = 0
        playoff['postseason_flag'] = 1
        season_stats = regular.append(playoff)
        season_stats.columns = cls.columns_needed
        for column in ['games', 'goals', 'assists', 'points', 'penalty', 'plus_minus']:
            season_stats[column] = pd.to_numeric(season_stats[column], errors='coerce')
        season_stats['year'] = pd.to_datetime(season_stats['season'].map(lambda x: x.split('-')[0]), format='%Y')
        season_stats['years_passed'] = 2021 - season_stats['year'].dt.year
        season_stats = season_stats[season_stats['games'].isnull() == False]
        return season_stats