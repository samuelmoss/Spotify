import spotipy
import spotipy.util as util
import config
import datetime
from pytz import timezone
import logging
import traceback
import pandas as pd

date_stage = datetime.datetime.today()
current_date = date_stage.strftime('%m-%d-%Y')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('	%(asctime)s - %(name)s - %(message)s')

file_handler = logging.FileHandler(f'./logs/{current_date} SpotifyETL.py')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


class SpotifyETL:
    """
    This class will function as the primary class for pulling information out of the Spotify REST API via Spotipy.
    I will add more to this class as time goes on for any analysis/visualization I want to do.
    """

    def __init__(self):
        self.client_id = config.client_id
        self.client_secret = config.client_secret
        self.redirect_uri = config.redirect_uri
        self.username = config.username
        self.scope = config.scope
        self.token = util.prompt_for_user_token(self.username, self.scope, self.client_id, self.client_secret,
                                                self.redirect_uri)
        try:
            if self.token:
                self.sp = spotipy.Spotify(auth=self.token)
        except Exception as e:
            logger.error(traceback.format_exc())
            print(e.args)

    def get_recent_songs(self):
        """
        Method to retrieve 50 most recent played songs
        """

        try:
            recent_songs_method = self.sp.current_user_recently_played()
            songs = recent_songs_method['items']
        except Exception as e:
            logger.error(traceback.format_exc())
            print(e.args)
        return songs

    def get_track_entity_data(self):
        """
        Method to create table for track-specific data
        """
        songs = self.get_recent_songs()
        ids = []
        names = []
        artist_ids = []
        artists = []
        album_ids = []
        albums = []
        popularities = []
        durations = []
        datetime_played = []

        try:
            for i in range(0, len(songs)):
                ids.append(songs[i]['track']['id'])
                names.append(songs[i]['track']['name'])
                artist_ids.append(songs[i]['track']['album']['artists']['id'])
                artists.append(songs[i]['track']['album']['artists']['name'])
                album_ids.append(songs[i]['track']['album']['id'])
                albums.append(songs[i]['track']['album']['name'])
                popularities.append(songs[i]['track']['popularity'])
                durations.append(songs[i]['track']['duration_ms'])
                datetime_played.append(songs[i]['played_at'])

            track_zipcols = list(
                zip(ids, names, artist_ids, artists, album_ids, albums, popularities, durations, datetime_played))

        except Exception as e:
            logger.error(traceback.format_exc())
            print(e.args)

        return track_zipcols

    def get_track_ids(self):

        try:
            zippedlist = self.get_track_entity_data()
            id_list = []
            for i in range(0, len(zippedlist)):
                id_list.append(zippedlist[i][0])

        except Exception as e:
            logger.error(traceback.format_exc())
            print(e.args)

        return id_list

    def get_track_audio_features(self):

        ids = self.get_track_ids()
        dance = []
        energy = []
        key = []
        loudness = []
        mode = []
        speechiness = []
        acousticness = []
        liveness = []
        valence = []
        tempo = []
        uri = []

        try:
            track_info_method = self.sp.audio_features(ids)

            for track in track_info_method:
                dance.append(track['danceability'])
                energy.append(track['energy'])
                key.append(track['key'])
                loudness.append(track['loudness'])
                mode.append(track['mode'])
                speechiness.append(track['speechiness'])
                acousticness.append(track['acousticness'])
                liveness.append(track['liveness'])
                valence.append(track['valence'])
                tempo.append(track['tempo'])
                uri.append(track['uri'])

            track_info_cols = list(
                zip(ids, dance, energy, key, loudness, mode, speechiness, acousticness, liveness, valence, tempo, uri))

        except Exception as e:
            logger.error(traceback.format_exc())
            print(e.args)

        return track_info_cols

    def create_track_entity(self):

        track_info = self.get_track_entity_data()
        audio_features = self.get_track_audio_features()

        info_df = pd.DataFrame(track_info, columns=['track_id', 'track_name', 'artist_id', 'artist_name', 'album_id',
                                                    'album_name', 'track_popularity', 'track_duration',
                                                    'datetime_played'])

        audio_df = pd.DataFrame(track_info, columns=['track_id', 'danceability', 'energy', 'key', 'loudness',
                                                     'mode', 'speechiness', 'acousticness', 'liveness', 'valence',
                                                     'tempo', 'uri'])

        track_entity = pd.merge(info_df,audio_df, how='inner')
        track_entity['date_played'] = [datetime.datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M:%S.%fZ') for date_time_str
                                  in track_entity['datetime_played']]
        track_entity['date_played'] = [d.date() for d in track_entity['date_played']]
        track_entity['time_played'] = [datetime.datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M:%S.%fZ') for date_time_str
                                    in track_entity['datetime_played']]
        track_entity['time_played'] = [timezone('UTC').localize(d) for d in track_entity['time_played']]
        track_entity['time_played'] = [d.astimezone(timezone('US/Central')) for d in track_entity['time_played']]
        track_entity['time_played'] = [d.time() for d in track_entity['time_played']]
        track_entity['track_duration'] = track_entity['track_duration']/1000

        return track_entity
