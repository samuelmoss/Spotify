# Spotify App

This app is in initial exploration phases, with use cases including but not limited to:
* Analyzing genres/subgenres
* Analyzing time-of-day/weather and Spotify use
* Predicting songs I might like
* Creating playlists


# Setup
1. Download python requirements: pip3 install -r requirements.txt
2. Config file contains client_id, client_secret, redirect_uri, username, scope, server, database, db_user, db_password, engine_connection

# Spotify to Azure DB Connections
This app calls Spotify's REST API via Spotipy to retrieve, clean, and store your 50 most recent tracks listened to along with metrics about the tracks, and passes to three DB entities - tracks, artists, and albums.
