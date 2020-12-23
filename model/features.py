import pandas as pd
import tqdm
import numpy as np


class Features:
    dummies = ['shoots', 'birth_country', 'nhl_rights', 'draft_team']
    aggregates = ['sum', 'mean', 'max', 'min']
    stats_columns = ['games', 'goals', 'assists', 'points', 'penalty', 'plus_minus']
    
    def __init__(self, players, seasons):
        self.merged = seasons.merge(players, left_on='player_id', right_on='id')
    
    def get_age_at_season(self):
        self.merged['age'] = (self.merged['year'] - self.merged['date_of_birth']) / np.timedelta64(1, 'Y')
        
    def get_nationality(self):
        nations = [x.split(' / ') for x in self.merged['nation'].unique()]
        nations = list(set([item for sublist in nations for item in sublist]))
        for nation in tqdm.tqdm(nations):
            column = f'nation_{nation}'
            self.merged.loc[self.merged['nation'].str.contains(nation), column] = 1
            self.merged[column].fillna(0, inplace=True)
            
    def get_position(self):
        positions = [x.split('_')[-1].split('/') for x in self.merged['position'].unique()]
        positions = list(set([item.upper() for sublist in positions for item in sublist]))
        for position in tqdm.tqdm(positions):
            column = f'position_{position}'
            self.merged.loc[self.merged['position'].str.contains(position, case=False), column] = 1
            self.merged[column].fillna(0, inplace=True)
            
    def get_dummies(self):
        self.merged = pd.concat([self.merged, pd.get_dummies(self.merged[self.dummies], drop_first=True)], axis=1)
        
    def get_aggregates(self):
        groupby_columns = ['player_id', 'season', 'postseason_flag']
        aggregates = self.merged.groupby(groupby_columns)[self.stats_columns].sum().reset_index()
        regular = aggregates[aggregates['postseason_flag'] == 0].reset_index(drop=True).sort_values(['player_id', 'season'])
        playoff = aggregates[aggregates['postseason_flag'] == 1].reset_index(drop=True).sort_values(['player_id', 'season'])
        regular = self.aggregate_rolling(regular)
        playoff = self.aggregate_rolling(playoff)
        aggregated_features = regular.append(playoff, sort=False)
        shape_before = self.merged.shape[0]
        self.merged = self.merged.merge(aggregated_features, on=['player_id', 'season', 'postseason_flag'], how='left')
        assert shape_before == self.merged.shape[0], "Shapes doesn't match"
        
    def aggregate_rolling(self, df):
        max_window = 50
        aggregations = []
        for function in tqdm.tqdm(self.aggregates):
            aggr = getattr(df.groupby(['player_id'])[self.stats_columns].rolling(max_window, 1), function)()
            aggr = aggr.groupby('player_id')[self.stats_columns].shift()
            aggr.columns = [f'{function}_{x}' for x in aggr.columns]
            aggregations.append(aggr.reset_index(drop=True))
        df = df.merge(pd.concat(aggregations, axis=1), left_index=True, right_index=True)
        df = df.drop(self.stats_columns, axis=1)
        return df
    
    def gather_all_features(self):
        self.get_age_at_season()
        print("Gathering nationalities...")
        self.get_nationality()
        print('Gathering positions...')
        self.get_position()
        print('Gathering dummies...')
        self.get_dummies()
        print('Gathering aggregates...')
        self.get_aggregates()
        return self.merged
        