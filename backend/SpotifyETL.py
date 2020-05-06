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

file_handler = logging.FileHandler(f'./logs/{current_date} SpotifyETL.log')
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
        explicit_flags = []

        try:
            for i in range(0, len(songs)):
                ids.append(songs[i]['track']['id'])
                names.append(songs[i]['track']['name'])
                artist_ids.append(songs[i]['track']['album']['artists'][0]['id'])
                artists.append(songs[i]['track']['album']['artists'][0]['name'])
                album_ids.append(songs[i]['track']['album']['id'])
                albums.append(songs[i]['track']['album']['name'])
                popularities.append(songs[i]['track']['popularity'])
                durations.append(songs[i]['track']['duration_ms'])
                datetime_played.append(songs[i]['played_at'])
                explicit_flags.append(songs[i]['track']['explicit'])

            track_zipcols = list(
                zip(ids, names, artist_ids, artists, album_ids, albums, popularities, durations, datetime_played,
                    explicit_flags))

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

        try:
            track_info = self.get_track_entity_data()
            audio_features = self.get_track_audio_features()

            info_df = pd.DataFrame(track_info,
                                   columns=['track_id', 'track_name', 'artist_id', 'artist_name', 'album_id',
                                            'album_name', 'track_popularity', 'track_duration',
                                            'datetime_played', 'explicit'])

            audio_df = pd.DataFrame(audio_features,
                                    columns=['track_id', 'danceability', 'energy', 'song_key', 'loudness',
                                             'mode', 'speechiness', 'acousticness', 'liveness', 'valence',
                                             'tempo', 'uri'])

            track_entity = pd.merge(info_df, audio_df, how='inner')
            track_entity['date_played'] = [datetime.datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M:%S.%fZ') for
                                           date_time_str
                                           in track_entity['datetime_played']]
            track_entity['date_played'] = [d.date() for d in track_entity['date_played']]
            track_entity['time_played'] = [datetime.datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M:%S.%fZ') for
                                           date_time_str
                                           in track_entity['datetime_played']]
            track_entity['time_played'] = [timezone('UTC').localize(d) for d in track_entity['time_played']]
            track_entity['time_played'] = [d.astimezone(timezone('US/Central')) for d in track_entity['time_played']]
            track_entity['time_played'] = [d.time() for d in track_entity['time_played']]
            track_entity['track_duration'] = track_entity['track_duration'] / 1000

            track_entity = track_entity.drop_duplicates()
            track_entity = track_entity.set_index('track_id')

        except Exception as e:
            logger.error(traceback.format_exc())
            print(e.args)

        return track_entity

    def get_artist_ids(self):

        try:
            zippedlist = self.get_track_entity_data()
            artist_id_list = []
            for i in range(0, len(zippedlist)):
                artist_id_list.append(zippedlist[i][2])

            artist_id_set = set(artist_id_list)
            unique_artist_ids = list(artist_id_set)

        except Exception as e:
            logger.error(traceback.format_exc())
            print(e.args)

        return unique_artist_ids

    def get_artist_data(self):

        try:
            artist_ids = self.get_artist_ids()
            artist_method = self.sp.artists(artist_ids)
            artists = artist_method['artists']

            names = []
            popularities = []
            followers = []
            image = []
            genres = []
            for i in range(0, len(artists)):
                names.append(artists[i]['name'])
                popularities.append(artists[i]['popularity'])
                followers.append(artists[i]['followers']['total'])
                image.append(artists[i]['images'][1]['url'])
                try:
                    genres.append(artists[i]['genres'])
                except IndexError:
                    genres.append('Null')

            artist_info_cols = list(
                zip(artist_ids, names, popularities, followers, image, genres))

        except Exception as e:
            logger.error(traceback.format_exc())
            print(e.args)

        return artist_info_cols

    def create_artist_entity(self):

        try:
            artist_info = self.get_artist_data()
            artist_df = pd.DataFrame(artist_info,
                                     columns=['artist_id', 'artist_name', 'artist_popularity', 'artist_followers',
                                              'artist_image', 'artist_genres'])

            artist_df = artist_df.explode('artist_genres')
            artist_df = artist_df.set_index('artist_id')
        except Exception as e:
            logger.error(traceback.format_exc())
            print(e.args)

        return artist_df

    def get_album_ids(self):

        try:
            zippedlist = self.get_track_entity_data()
            album_id_list = []
            for i in range(0, len(zippedlist)):
                album_id_list.append(zippedlist[i][4])

            album_id_set = set(album_id_list)
            unique_album_ids = list(album_id_set)

        except Exception as e:
            logger.error(traceback.format_exc())
            print(e.args)

        return unique_album_ids

    def get_album_data(self):

        try:
            album_ids = self.get_album_ids()
            if 20 < len(album_ids) <= 40:
                composite_list = [album_ids[x:x + 20] for x in range(0, len(album_ids), 20)]
                res1, res2 = zip(composite_list)
                res1 = res1[0]
                res2 = res2[0]
                album_method = self.sp.albums(res1)
                albums = album_method['albums']

                names = []
                popularities = []
                tracks = []
                images = []
                release_dates = []
                labels = []
                artist_ids = []
                artist_names = []
                for i in range(0, len(albums)):
                    names.append(albums[i]['name'])
                    popularities.append(albums[i]['popularity'])
                    tracks.append(albums[i]['total_tracks'])
                    images.append(albums[i]['images'][1]['url'])
                    release_dates.append(albums[i]['release_date'])
                    labels.append(albums[i]['label'])
                    artist_ids.append(albums[i]['artists'][0]['id'])
                    artist_names.append(albums[i]['artists'][0]['name'])

                album_method = self.sp.albums(res2)
                albums = album_method['albums']

                for i in range(0, len(albums)):
                    names.append(albums[i]['name'])
                    popularities.append(albums[i]['popularity'])
                    tracks.append(albums[i]['total_tracks'])
                    images.append(albums[i]['images'][1]['url'])
                    release_dates.append(albums[i]['release_date'])
                    labels.append(albums[i]['label'])
                    artist_ids.append(albums[i]['artists'][0]['id'])
                    artist_names.append(albums[i]['artists'][0]['name'])

            elif len(album_ids) > 40:
                composite_list = [album_ids[x:x + 20] for x in range(0, len(album_ids), 20)]
                res1, res2, res3 = zip(composite_list)
                res1 = res1[0]
                res2 = res2[0]
                res3 = res3[0]
                album_method = self.sp.albums(res1)
                albums = album_method['albums']

                names = []
                popularities = []
                tracks = []
                images = []
                release_dates = []
                labels = []
                artist_ids = []
                artist_names = []
                for i in range(0, len(albums)):
                    names.append(albums[i]['name'])
                    popularities.append(albums[i]['popularity'])
                    tracks.append(albums[i]['total_tracks'])
                    images.append(albums[i]['images'][1]['url'])
                    release_dates.append(albums[i]['release_date'])
                    labels.append(albums[i]['label'])
                    artist_ids.append(albums[i]['artists'][0]['id'])
                    artist_names.append(albums[i]['artists'][0]['name'])

                album_method = self.sp.albums(res2)
                albums = album_method['albums']

                for i in range(0, len(albums)):
                    names.append(albums[i]['name'])
                    popularities.append(albums[i]['popularity'])
                    tracks.append(albums[i]['total_tracks'])
                    images.append(albums[i]['images'][1]['url'])
                    release_dates.append(albums[i]['release_date'])
                    labels.append(albums[i]['label'])
                    artist_ids.append(albums[i]['artists'][0]['id'])
                    artist_names.append(albums[i]['artists'][0]['name'])

                album_method = self.sp.albums(res3)
                albums = album_method['albums']

                for i in range(0, len(albums)):
                    names.append(albums[i]['name'])
                    popularities.append(albums[i]['popularity'])
                    tracks.append(albums[i]['total_tracks'])
                    images.append(albums[i]['images'][1]['url'])
                    release_dates.append(albums[i]['release_date'])
                    labels.append(albums[i]['label'])
                    artist_ids.append(albums[i]['artists'][0]['id'])
                    artist_names.append(albums[i]['artists'][0]['name'])

            else:
                album_method = self.sp.albums(album_ids)
                albums = album_method['albums']

                names = []
                popularities = []
                tracks = []
                images = []
                release_dates = []
                labels = []
                artist_ids = []
                artist_names = []
                for i in range(0, len(albums)):
                    names.append(albums[i]['name'])
                    popularities.append(albums[i]['popularity'])
                    tracks.append(albums[i]['total_tracks'])
                    images.append(albums[i]['images'][1]['url'])
                    release_dates.append(albums[i]['release_date'])
                    labels.append(albums[i]['label'])
                    artist_ids.append(albums[i]['artists'][0]['id'])
                    artist_names.append(albums[i]['artists'][0]['name'])

            album_info_cols = list(
                zip(album_ids, names, popularities, tracks, images, release_dates, labels, artist_ids, artist_names))

        except Exception as e:
            logger.error(traceback.format_exc())
            print(e.args)

        return album_info_cols

    def create_album_entity(self):

        try:
            album_info = self.get_album_data()
            album_df = pd.DataFrame(album_info,
                                    columns=['album_id', 'album_name', 'album_popularity', 'album_tracks',
                                             'album_image', 'album_release_date', 'album_label', 'album_artist_id',
                                             'album_artist_name'])

            album_df = album_df.set_index('album_id')

        except Exception as e:
            logger.error(traceback.format_exc())
            print(e.args)

        return album_df


def clean_entities(sql_file, index):

    try:
        engine = config.engine
        sql = open(f'{sql_file}', 'r')
        index = index
        df = pd.read_sql(sql.read(), engine)
        df = df.drop_duplicates()
        df = df.set_index(index)

    except Exception as e:
        logger.error(traceback.format_exc())
        print(e.args)

    return df
