import requests  
import json  
import spotipy  
from spotipy.oauth2 import SpotifyClientCredentials  

def get_episode_name(episode_id):
    # Set up credentials. You'll need to replace these with your own.  
    client_id = '1d64d140ff024d0fbe251a2a8dedee2c'  
    client_secret = 'fa67d743c8af4b138e434f8e6defcbde'  

    client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)  

    # Initialize Spotipy  
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)  

    # Get episode's metadata  
    episode = sp.episode(episode_id,  market='US')  

    # Get episode's name  
    episode_name = episode['name']  
    return episode_name

def get_apple_episode_url(episode_name):  
    base_url = 'https://itunes.apple.com/search'  
    params = {"term": episode_name, "entity": "podcastEpisode", "attribute":"titleTerm"}  
    response = requests.get(base_url, params=params)  
    data = json.loads(response.text)  
    if data['resultCount'] > 0:   
        #return url of first podcast found  
        return data['results'][0]['trackViewUrl']  
    else:  
        print("No podcast found with specified name.")  
        return None  

spotify_episode_url = "https://open.spotify.com/episode/1jQCNSZkoNC9QZRmDtyg7c"
episode_id = spotify_episode_url.split("/episode/",1)[1].split("?")[0]
episode_name = get_episode_name(episode_id)
apple_episode_url = get_apple_episode_url(episode_name)
print(apple_episode_url)