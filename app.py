import json
from flask import Flask, request, redirect, g, render_template, session, url_for
from flask_apscheduler import APScheduler
from flask_session import Session
import requests
from urllib.parse import quote
import time
import uuid
import serial
import os

# Authentication Steps, paramaters, and responses are defined at https://developer.spotify.com/web-api/authorization-guide/
# Visit this url to see all the steps, parameters, and expected response.


app = Flask(__name__)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()
app.secret_key = os.environ.get("SESSION_KEY")
app.config['SESSION_TYPE'] = 'filesystem'

Session(app)

bpm = 0

#  Client Keys
CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

# Server-side Parameters
CLIENT_SIDE_URL = "http://127.0.0.1"
PORT = 8080
REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)
SCOPE = ("streaming playlist-modify-public playlist-modify-private user-library-read "
         "user-read-email user-read-private user-modify-playback-state user-read-playback-state playlist-modify-private"
         )

SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    # "show_dialog": SHOW_DIALOG_str,
    "client_id": CLIENT_ID
}


@app.route("/")
def index():
    # Auth Step 1: Authorization
    session["state"] = str(uuid.uuid4())
    return render_template('index.html')


@app.route('/authorize')
def authorize():
    url_args = "&".join(["{}={}".format(key, quote(val)) for key, val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)


@app.route("/callback/q")
def callback():
    # Auth Step 4: Requests refresh and access tokens
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload)

    # Auth Step 5: Tokens are Returned to Application
    response_data = json.loads(post_request.text)
    access_token = response_data["access_token"]
    refresh_token = response_data["refresh_token"]
    token_type = response_data["token_type"]
    expires_in = response_data["expires_in"]
    session['token'] = access_token

    # Auth Step 6: Use the access token to access Spotify API
    authorization_header = {"Authorization": "Bearer {}".format(session['token'])}

    # Get profile data
    user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
    profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
    profile_data = json.loads(profile_response.text)

    # Get user playlist data
    tracks_api_endpoint = "{}/tracks".format(profile_data["href"])
    tracks_response = requests.get(
        tracks_api_endpoint,
        headers=authorization_header,
        params={'limit': '50'}
    )

    playlist_data = json.loads(tracks_response.text)
    # Combine profile and playlist data to display
    # display_arr = playlist_data["items"]
    # for item in display_arr:
    #     print(json.dumps(item, indent=4, sort_keys=True))
    return redirect(url_for('dashboard'))


@app.route("/sys_info.json")
def system_info():  # you need an endpoint on the server that returns your info...
    return str(bpm)


def print_test():
    global bpm
    ser = serial.Serial(
        port="COM4",
        baudrate=115200
    )
    while True:
        data_raw = ser.readline().decode().strip()
        if data_raw:
            data = data_raw.split(",")
            if int(data[0]) > 0:
                bpm = int(data[0])


@app.route("/dashboard")
def dashboard():
    if not session.get('token'):
        redirect(url_for('index'))
    return render_template("player.html", token=session['token'])


@app.route("/play", methods=['GET', 'POST'])
def play_track():
    app.apscheduler.add_job(func=print_test, trigger='date', id=str('test'))
    authorization_header = {"Authorization": "Bearer {}".format(session['token'])}
    device_list = json.loads(requests.get(
        'https://api.spotify.com/v1/me/player/devices',
        headers=authorization_header,
    ).text)
    for device in device_list['devices']:
        if device:
            player_api_endpoint = "{}/me/player".format(SPOTIFY_API_URL)
            payload = {
                'device_ids': [device['id']],
                'play': 'True'
            }
            if not device['is_active']:
                print('Activating Device')
                requests.put(
                    url=player_api_endpoint,
                    headers=authorization_header,
                    json=payload
                )
            else:
                play_api_endpoint = "{}/me/player/play".format(SPOTIFY_API_URL)
                requests.put(
                    play_api_endpoint,
                    headers=authorization_header,
                )
            print("Playing Now!")
            return "Nothing"

    print("No Devices Found for Playback!")
    return "Nothing"


@app.route("/pause", methods=['GET', 'POST'])
def pause_track():
    authorization_header = {"Authorization": "Bearer {}".format(session['token'])}
    device_list = json.loads(requests.get(
        'https://api.spotify.com/v1/me/player/devices',
        headers=authorization_header,
    ).text)
    for device in device_list['devices']:
        if device:
            player_api_endpoint = "{}/me/player".format(SPOTIFY_API_URL)
            payload = {
                'device_ids': [device['id']],
                'play': 'false'
            }
            if not device['is_active']:
                print('Activating Device')
                requests.put(
                    url=player_api_endpoint,
                    headers=authorization_header,
                    json=payload
                )
            else:
                play_api_endpoint = "{}/me/player/pause".format(SPOTIFY_API_URL)
                requests.put(
                    play_api_endpoint,
                    headers=authorization_header,
                )
            print("Paused!")
            return "Nothing"

    print("No Devices Found for Playback!")
    return "Nothing"


if __name__ == "__main__":
    app.run(debug=True, port=PORT)
