import sqlalchemy
from preprocessing import Players, Seasons

db_name = 'postgres'
db_hostname = 'localhost'
db_user = 'postgres'
db_password = 'tttBBB777'


season = pd.read_sql('select * from player_season', engine)
players = pd.read_sql('select * from player', engine)
season = Seasons.preprocess(season)
players = Players.preprocess(players)
season.to_excel('season.xlsx', index=False)
players.to_excel('players.xlsx', index=False)
