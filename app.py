from flask import Flask, request, url_for, session, redirect, render_template, g
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import openai 
import time
import os
from dotenv import load_dotenv, find_dotenv
app = Flask(__name__)


app.secret_key = "generate_it_on_the_fly"
app.config['SESSION_COOKIE_NAME'] = 'Ignas Cookie'
TOKEN_INFO = 'token_info'


load_dotenv()
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
print(client_id)

@app.route('/')
def welcome():
    print(client_id,client_secret)
    return render_template('welcome.html')

@app.route('/redirect')
def redirectPage():
    sp_oauth = create_spotify_oauth(session.get('chosen_scope', None))
    if session.get('chosen_scope', None) == "user-library-read":
        redirect_url = 'getSavedTracks'
    if session.get('chosen_scope', None) == "user-top-read":
        redirect_url = 'getTopTracks'
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for(redirect_url, _external=True))

@app.route('/top_songs')
def get_top_songs():
    session['chosen_scope'] = "user-top-read"
    sp_oauth = create_spotify_oauth(session.get('chosen_scope', None))
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route('/getTopTracks', methods=['POST', 'GET'])
def getTopTracks():
    try:
        token_info = get_token()
    except:
        print("user not logged")
        return redirect('/')
    sp = spotipy.Spotify(auth=token_info['access_token'])
    limit_chosen = 3
    song_item = sp.current_user_top_tracks(
        limit=limit_chosen, offset=0, time_range='medium_term')['items']
    id_list = []
    for i in range(len(song_item)):
        id_list.append(song_item[i]['id'])
    features = sp.audio_features(id_list)
    song_list =[]
    for i in range(limit_chosen):
            songs_values = {
                'song_name':song_item[i]['name'],
                'song_artist':song_item[i]['artists'][0]['name'],
                'song_album':song_item[i]['album']['name'],
                'song_popularity':song_item[i]['popularity'],
                'accousticness':features[i]['acousticness'],
                'danceability':features[i]['danceability'],
                'duration_ms':features[i]['duration_ms'],
                'energy':features[i]['energy'],
                'instrumentalness':features[i]['instrumentalness'],
                'key':features[i]['key'],
                'liveness':features[i]['liveness'],
                'loudness':features[i]['loudness'],
                'mode':features[i]['mode'],
                'speechiness':features[i]['speechiness'],
                'tempo':features[i]['tempo'],
                'time_signature':features[i]['time_signature'],
                'valence':features[i]['valence']
            }
            song_list.append(songs_values)
    song_ids_for_recs = []
    for i in range(limit_chosen):
        song_ids_for_recs.append(id_list[i])
    #recommendations = sp.recommendations(seed_tracks=song_ids_for_recs)
    return song_list
            

def create_spotify_oauth(desired_scope):
    return SpotifyOAuth(
        client_id,
        client_secret,
        redirect_uri=url_for('redirectPage', _external=True),
        scope='user-library-read user-top-read')

def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        raise Exception("No token info found")
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    if (is_expired):
        sp_oauth = create_spotify_oauth(session.get('chosen_scope', None))
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info



if __name__ == '__main__':
  app.run( debug=True)