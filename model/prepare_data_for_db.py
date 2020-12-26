import sqlalchemy
import pandas as pd
import time
import os
from preprocessing import Players, Seasons


def copy_df(df, table_name, engine, if_exists='fail'):
    output = 'temp_copy_upload_' + str(int(time.time())) + '.csv'
    copy_sql = """COPY \"%s\".\"%s\" ("%s") FROM stdin WITH CSV HEADER DELIMITER as '\t' QUOTE '"' """ % \
               ('public', table_name, '","'.join(df.columns))
    df.to_csv(output, sep='\t', index=False, escapechar='"')
    df.head(0).to_sql(table_name, engine, index=False, if_exists=if_exists)
    
    fake_conn = engine.raw_connection()
    fake_cur = fake_conn.cursor()
    with open(output, 'r', encoding='utf-8') as f:
        fake_cur.copy_expert(copy_sql, f)
    os.remove(output)
    fake_conn.commit()


if __name__ == '__main__':
    db_name = 'postgres'
    db_hostname = 'localhost'
    db_user = 'postgres'
    db_password = 'tttBBB777'
    django_db_name = 'HockeyManager'
    django_player_table = 'player'
    django_player_season_table = 'player_season'

    engine = sqlalchemy.create_engine(f'postgresql+psycopg2://{db_user}:{db_password}@{db_hostname}/{db_name}')
    django_engine = sqlalchemy.create_engine(f'postgresql+psycopg2://{db_user}:{db_password}@{db_hostname}/{django_db_name}')

    season = pd.read_sql('select * from player_season', engine)
    players = pd.read_sql('select * from player', engine)
    season = Seasons.preprocess(season)
    season = season.reset_index().rename(columns={season.index.name: 'id'})
    players = Players.preprocess(players)

    players.to_sql(django_player_table, con=django_engine, index=False, if_exists='replace')
    season.to_sql(django_player_season_table, con=django_engine, index=False, if_exists='replace')
