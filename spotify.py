"""Handles Spotify authorization, access tokens, and API requests."""

import os
import base64
import urllib
import requests
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI

SPOTIFY_AUTHORIZATION_URL='https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_ENDPOINT='https://accounts.spotify.com/api/token'
SPOTIFY_USER_ENDPOINT = 'https://api.spotify.com/v1/me'
SPOTIFY_TOP_ARTISTS_ENDPOINT = 'https://api.spotify.com/v1/me/top/artists'
SPOTIFY_RELATED_ARTISTS_ENDPOINT ='https://api.spotify.com/v1/artists'


def get_auth_url():
    """Generate Spotify authorization URL."""

    query_params = {
        'client_id': SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'scope': 'user-library-read user-top-read user-read-private'
    }
    # https://christophergs.github.io/python/2016/12/03/python-urllib-parse/
    # https://github.com/yspark90/UniMuse/blob/master/UniMuse/spotify.py
    # url_args = '&'.join([f"{key}={urllib.parse.quote(val)}" for key, val in query_params.items()])
    url_args = urllib.parse.urlencode(query_params)
    auth_url = f"{SPOTIFY_AUTHORIZATION_URL}/?{url_args}"
    return auth_url


def get_access_token(request):
    """Exchange Spotify authorization code for access token via POST request."""

    auth_code = request.args.get('code')
    payload = {
        'grant_type': 'authorization_code',
        'code': str(auth_code),
        'redirect_uri': SPOTIFY_REDIRECT_URI
    }

    # https://github.com/yspark90/UniMuse/blob/master/UniMuse/spotify.py
    # https://docs.python.org/2/library/base64.html
    # the header, as specified in the docs, needs to be a base64 encoded string that has
    client_encoded_str = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode('ascii'))
    headers = {"Authorization": f"Basic {client_encoded_str.decode('ascii')}"}

    # http://flask.pocoo.org/docs/1.0/reqcontext/
    # http://docs.python-requests.org/en/master/user/quickstart/
    # https://www.pluralsight.com/guides/web-scraping-with-request-python
    response = requests.post(SPOTIFY_TOKEN_ENDPOINT, data=payload, headers=headers)
    return response.json()


def get_top_artists(access_token):
    """Get a user's top 40 artists."""

    # https://www.dataquest.io/blog/python-api-tutorial/
    query_params = {
        'time_range': 'medium_term',
        'limit': '40',
        'offset': '29'
    }
    url_args = urllib.parse.urlencode(query_params)
    url = f"{SPOTIFY_TOP_ARTISTS_ENDPOINT}/?{url_args}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    return response.json()


def format_artist_data(response):
    """Format top artist JSON data as a list of tuples: index, artist name, url, and image."""

    artists = [(index, item['name'], item['external_urls']['spotify'], item['images'][2]['url'])
                for index, item in enumerate(response['items'], 1)]
    return artists


def get_artist_ids(top_artists):
    """Get IDs of top 40 Spotify artists."""

    artist_ids = [(artist['name'], artist['id']) for artist in top_artists['items']]
    return artist_ids


def get_related_artists(artist_ids, access_token):
    """Get related artists for top 40 Spotify artists."""

    related_artists = []
    for artist in artist_ids:
        name = artist[0]
        id = artist[1]
        url = f"{SPOTIFY_RELATED_ARTISTS_ENDPOINT}/{id}/related-artists"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)
        response = response.json()
        filtered_artists = filter_related_artists(response)
        related_artists.extend(filtered_artists)
    return related_artists


def filter_related_artists(response):
    """Limit related artists to 5 and clean up data."""

    filtered_artists = []
    for i in range(0, 5):
        artist = response['artists'][i]
        filtered_artists.append((artist['id'], artist['name']))
    return filtered_artists


def get_user_profile(access_token):
    """Get Spotify profile information about the current user."""

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(SPOTIFY_USER_ENDPOINT, headers=headers)
    return response.json()
