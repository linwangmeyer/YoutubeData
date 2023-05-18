import os
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Load the environment variables from .env
load_dotenv()
api_key = os.getenv('API_KEY')
youtube = build('youtube', 'v3', developerKey=api_key)

# Set the channel ID and retrieve the channel information
channel_id = "UC-lHJZR3Gqxm24_Vd_AJ5Yw"
channel_response = youtube.channels().list(
    part="snippet,statistics",
    id=channel_id
).execute()
channel_info = channel_response['items'][0]['snippet']
channel_stats = channel_response['items'][0]['statistics']

# Retrieve all videos of the channel
videos = []
next_page_token = None
while True:
    video_response = youtube.search().list(
        part="snippet",
        channelId=channel_id,
        maxResults=50,
        pageToken=next_page_token,
        type="video"
    ).execute()
    videos += video_response['items']
    next_page_token = video_response.get('nextPageToken')
    if not next_page_token:
        break

# Extract the desired information from each video
video_info = []
for video in videos:
    video_id = video['id']['videoId']
    video_response = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=video_id
    ).execute()
    video_snippet = video_response['items'][0]['snippet']
    video_stats = video_response['items'][0]['statistics']
    video_content = video_response['items'][0]['contentDetails']
    video_info.append({
        'title': video_snippet['title'],
        'duration': video_content['duration'],
        'view_count': video_stats['viewCount'],
        'like_count': video_stats['likeCount'],
        'comment_count': video_stats['commentCount']
    })

# Save the video information to a CSV file
df = pd.DataFrame(video_info)
df.to_csv('AliAbdaal_videos.csv', index=False)