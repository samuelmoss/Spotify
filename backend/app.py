from SpotifyETL import SpotifyETL, clean_entities
import datetime
import time
import logging
import sqlalchemy
import pyodbc
import config

date_stage = datetime.datetime.today()
current_date = date_stage.strftime('%m-%d-%Y')

#defining logger conditions
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('	%(asctime)s - %(name)s - %(message)s')

file_handler = logging.FileHandler(f'./logs/{current_date} app.log')
file_handler.setFormatter(formatter)

start_time = time.time()

#initiate ShopifyETL Class
s = SpotifyETL()

#call get_recent_songs method
print('Getting Recent Songs')
s.get_recent_songs()
recent_length = len(s.get_recent_songs())
print(f'Retrieved {recent_length} songs')

#call get artist ids method
print('Getting Recent Artists')
s.get_artist_ids()
artist_length = len(s.get_artist_ids())
print(f'Retrieved {artist_length} artists')

#call get album ids method
print('Getting Recent Albums')
s.get_album_ids()
album_length = len(s.get_album_ids())
print(f'Retrieve {album_length} albums')

#create_Spotify csvs for staging
print('Creating Track Entity')
track_entity = s.create_track_entity()
print('Track Entity Created')
print('Creating Artist Entity')
artist_entity = s.create_artist_entity()
print('Artist Entity Created')
print('Creating Album Entity')
album_entity = s.create_album_entity()
print('Album Entity Created')

print('Storing Entities as CSVs')
track_entity.to_csv(f'./output/tracks {current_date}.csv')
artist_entity.to_csv(f'./output/artists {current_date}.csv')
album_entity.to_csv(f'./output/albums {current_date}.csv')


#establishing SQL Server Engine to Azure DB
engine = config.engine


# write the DataFrame to a table in the sql database
print('Writing DataFrames to Azure DB Tables')
track_entity.to_sql("tracks", schema='dbo', if_exists='append', con=engine)
artist_entity.to_sql("artists", schema='dbo', if_exists='append', con=engine)
album_entity.to_sql("albums", schema='dbo', if_exists='append', con=engine)

print('Cleaning Album and Artist Tables')
clean_tracks_df = clean_entities('tracks.sql', 'track_id')
clean_artist_df = clean_entities('artists.sql', 'artist_id')
clean_album_df = clean_entities('albums.sql', 'album_id')
track_data_types = {'track_id': sqlalchemy.types.VARCHAR(50)}
artist_data_types = {'artist_id': sqlalchemy.types.VARCHAR(50)}
album_data_types = {'album_id': sqlalchemy.types.VARCHAR(50)}
clean_tracks_df.to_sql("tracks", schema='dbo', if_exists='replace', dtype=track_data_types, con=engine)
clean_artist_df.to_sql("artists", schema='dbo', if_exists='replace', dtype=artist_data_types, con=engine)
clean_album_df.to_sql("albums", schema='dbo', if_exists='replace', dtype=album_data_types, con=engine)
print('Azure DB Tables Populated')


end_time = time.time()

total_time = end_time - start_time

logger.debug(f'Process took {int(total_time/60)} minutes and {(total_time % 60):.2f} seconds')