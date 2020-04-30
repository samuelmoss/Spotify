from SpotifyETL import SpotifyETL

#initiate ShopifyETL Class
s = SpotifyETL()

#call get_recent_songs method
print('Getting Recent Songs')
s.get_recent_songs()
recent_length = len(s.get_recent_songs())
print(f'Retrieved {recent_length} songs')