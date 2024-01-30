import csv
import os
import pickle
import json
import logging
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Setup basic logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_authenticated_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json', 
                scopes=['https://www.googleapis.com/auth/youtube.readonly']
            )
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('youtube', 'v3', credentials=creds)

def get_playlists(youtube, channel_id, page_token=None):
    try:
        logging.info(f"Fetching playlists for channel: {channel_id}")
        response = youtube.playlists().list(
            part="snippet,contentDetails",
            channelId=channel_id,
            maxResults=50,
            pageToken=page_token
        ).execute()
        logging.info("Playlists fetched successfully.")
        return response
    except Exception as e:
        logging.error(f"Error in get_playlists: {e}")
        return None

def get_playlist_items_by_playlist_id(youtube, playlist_id, page_token=None):
    try:
        logging.info(f"Fetching playlist items for playlist ID: {playlist_id}")
        response = youtube.playlistItems().list(
            part="snippet,contentDetails",
            maxResults=50,
            playlistId=playlist_id,
            pageToken=page_token
        ).execute()
        logging.info("Playlist items fetched successfully.")
        return response
    except Exception as e:
        logging.error(f"Error in get_playlist_items_by_playlist_id: {e}")
        return None

def get_video_details(youtube, video_id):
    try:
        logging.info(f"Fetching details for video ID: {video_id}")
        response = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=video_id
        ).execute()
        logging.info("Video details fetched successfully.")
        return response
    except Exception as e:
        logging.error(f"Error in get_video_details: {e}")
        return None

def get_channel(channel_id):
    youtube = get_authenticated_service()

    logging.info(f"Starting data retrieval for channel ID: {channel_id}")

    playlists_response = get_playlists(youtube, channel_id)
    if playlists_response is None:
        logging.error("Failed to fetch playlists.")
        return

    if not playlists_response.get('items'):
        logging.warning("No playlists found for this channel.")
        return

    all_playlists = []
    for playlist in playlists_response.get('items', []):
        playlist_data = {
            'playlist_id': playlist['id'],
            'playlist_title': playlist['snippet']['title'],
            'videos': []
        }

        videos_response = get_playlist_items_by_playlist_id(youtube, playlist['id'])
        while videos_response:
            for video in videos_response['items']:
                video_id = video['snippet']['resourceId']['videoId']
                video_details_response = get_video_details(youtube, video_id)

                for item in video_details_response['items']:
                    video_data = {
                        'video_title': item['snippet']['title'],
                        'video_id': video_id,
                        'video_url': f"https://www.youtube.com/watch?v={video_id}",
                        'video_description': item['snippet']['description'],
                        'view_count': item['statistics'].get('viewCount'),
                        'like_count': item['statistics'].get('likeCount'),
                        'channel_id': channel_id,
                        'channel_url': f"https://www.youtube.com/channel/{channel_id}",
                    }
                    playlist_data['videos'].append(video_data)

            next_page_token = videos_response.get('nextPageToken')
            if next_page_token:
                videos_response = get_playlist_items_by_playlist_id(youtube, playlist['id'], next_page_token)
            else:
                videos_response = None

        all_playlists.append(playlist_data)

    logging.info("Data retrieval complete.")
    return all_playlists
