import sqlalchemy
import pandas as pd
from preprocessing import Players, Seasons


db_name = 'postgres'
db_hostname = 'localhost'
db_user = 'postgres'
db_password = 'tttBBB777'
django_db_name = 'HockeyManager'
django_player_table = 'player'
django_player_season_table = 'player_season'

engine = sqlalchemy.create_engine(f'postgresql+psycopg2://{db_user}:{db_password}@{db_hostname}/{db_name}')
django_engine = sqlalchemy.create_engine(f'postgresql+psycopg2://{db_user}:{db_password}@{db_hostname}/{django_db_name}')
chunk_size = 500000

season = pd.read_sql('select * from player_season', engine)
players = pd.read_sql('select * from player', engine)
season = Seasons.preprocess(season)
season = season.reset_index().rename(columns={season.index.name: 'id'})
players = Players.preprocess(players)

players.to_sql(django_player_table, con=django_engine, index=False, if_exists='replace')
season.to_sql(django_player_season_table, con=django_engine, index=False, if_exists='replace')
