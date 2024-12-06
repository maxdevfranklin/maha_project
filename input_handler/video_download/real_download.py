import os  

os.environ['SPOTIPY_CLIENT_ID'] = '1d64d140ff024d0fbe251a2a8dedee2c'
os.environ['SPOTIPY_CLIENT_SECRET'] = 'fa67d743c8af4b138e434f8e6defcbde'

playlist_link = "https://podcasts.apple.com/us/podcast/101-make-america-healthy-again-ft-del-bigtree/id1764140307?i=1000675452034"  
download_directory = os.getcwd()  

os.system(f'spotify_dl -l "{playlist_link}" -o "{download_directory}"')