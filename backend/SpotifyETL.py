import spotipy
import spotipy.util as util
import config
import datetime
import logging
import traceback

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

    def create_track_table(self):
        """
        Method to create table for track-specific data
        """
        songs = self.get_recent_songs()
        ids = []
        names = []
        # TODO - define empty lists for vaiables in track entity
        # TODO - figure out if track_info needs to be in a different class
        # TODO - check track analysis
