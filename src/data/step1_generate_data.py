# -*- coding: utf-8 -*-
"""step1_generate-data.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ow9beXDqwTnqsuEX44CMwlgi_tNPvwRH

## Read and pre-process my Youtube data

Read the watching history html file
"""

import os
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pytz
from datetime import datetime
from dateutil import parser

# Load and parse the HTML file
with open('watch-history.html', 'r') as file:
    html_content = file.read()
soup = BeautifulSoup(html_content, 'html.parser')
video_cells = soup.find_all('div', class_='outer-cell mdl-cell mdl-cell--12-col mdl-shadow--2dp')

videos = []
for cell in video_cells:
    content_cell = cell.find('div', class_='content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1')
    
    title_element = content_cell.find('a')
    title = title_element.text.strip() if title_element else ""
    video_url = title_element['href'] if title_element else ""
    
    channel_element = content_cell.find('a', href=lambda href: href and '/channel/' in href)
    channel = channel_element.text.strip() if channel_element else ""
    channel_url = channel_element['href'] if channel_element else ""
    
    timestamp = content_cell.contents[-1].strip()
    
    videos.append({
        'Title': title,
        'Video URL': video_url,
        'Channel': channel,
        'Channel URL': channel_url,
        'Timestamp': timestamp
    })

df = pd.DataFrame(videos)

"""A quick data clean to remove NaN values, and clean text data"""

df.replace('', np.nan, inplace=True)
df = df.dropna(subset=['Channel','Title'])

"""Pre-process text data"""

import re
import nltk
from nltk.corpus import stopwords
import string
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from gensim import corpora, models
from collections import Counter
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('words')
nltk.download('wordnet')

def preprocess_text(text):
    # Convert text to lowercase
    text = text.lower()

    # Remove numbers
    text = re.sub(r'\d+', '', text)

    # Remove punctuations
    text = text.translate(str.maketrans('', '', string.punctuation))

    # Remove non-English strings
    text = re.sub(r'[^\x00-\x7F]+', '', text)

    # Tokenize the text into individual words
    tokens = word_tokenize(text)
    
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words]
    
    '''# Add custom stopwords
    custom_stop_words = ['video', 'min', 'wang']
    tokens = [word for word in tokens if word not in custom_stop_words]
    '''
    # Remove simple letters that are not English words
    english_words = set(nltk.corpus.words.words())
    tokens = [word for word in tokens if word in english_words]
    
    # Lemmatize words
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    
    # Join the tokens back into a single string
    processed_text = ' '.join(tokens)
    return processed_text

df_preprocessed = df['Title'].apply(preprocess_text)

"""Save the cleaned data"""

df['TitleClean']=df_preprocessed
df.to_csv('mydata.csv', index=False)
df.info()

"""## Get meta data associated with the videos and channels

Get category ID, view counts, like counts, dislike counts, and duration for every video
"""

from tqdm import tqdm
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
youtube_api_key = 'YOUR-API-KEY'

video_ID = df['Video URL'].str.split('v=').str[1]
video_id_list = list(set(video_ID.to_list()))

# Create empty lists to store the extracted information
video_ids = []
channel_ids = []
video_titles = []
channel_titles = []
category_ids = []
view_counts = []
like_counts = []
dislike_counts = []
durations = []

# Create YouTube Data API client
youtube = build('youtube', 'v3', developerKey=youtube_api_key)

# Iterate over each video ID in the DataFrame
progress_bar = tqdm(total=len(video_id_list), desc="Processing Videos", unit="video")
for video_id in video_id_list:
    try:
        # Retrieve video details using videos().list() method
        video_response = youtube.videos().list(
            part='snippet,statistics,contentDetails',
            id=video_id
        ).execute()

        # Extract relevant information from the response
        if 'items' in video_response and video_response['items']:
            video_data = video_response['items'][0]
            snippet = video_data['snippet']
            statistics = video_data['statistics']
            content_details = video_data['contentDetails']

            channel_id = snippet['channelId']
            video_title = snippet['title']
            channel_title = snippet['channelTitle']
            category_id = snippet['categoryId']
            view_count = statistics.get('viewCount', 0)
            like_count = statistics.get('likeCount', 0)
            dislike_count = statistics.get('dislikeCount', 0)
            duration = content_details['duration']

            # Append the extracted information to the lists
            video_ids.append(video_id)
            channel_ids.append(channel_id)
            video_titles.append(video_title)
            channel_titles.append(channel_title)
            category_ids.append(category_id)
            view_counts.append(view_count)
            like_counts.append(like_count)
            dislike_counts.append(dislike_count)
            durations.append(duration)
    except HttpError as e:
        print(f"An error occurred for video ID: {video_id}")
        print(f"Error message: {e}")
    
    # Update the progress bar
    progress_bar.update(1)
    
# Close the progress bar
progress_bar.close()

"""Get category name for each category ID"""

uni_category_ids = set(category_ids)
category_names = {}
for category_id in uni_category_ids:
    response = youtube.videoCategories().list(
        part='snippet',
        id=category_id
    ).execute()
    if 'items' in response:
        category_names[category_id] = response['items'][0]['snippet']['title']

"""Get subscriber count information for each channel"""

channelIDs = list(set(channel_ids))
subscriber_counts = {}
for channel_id in channelIDs:
    try:
        # Retrieve channel statistics using channels().list() method
        channel_response = youtube.channels().list(
            part='statistics',
            id=channel_id
        ).execute()        
        if 'items' in channel_response and channel_response['items']:
            channel_data = channel_response['items'][0]
            subscriber_counts[channel_id] = channel_data['statistics'].get('subscriberCount', 0)
    except HttpError as e:
        print(f"An error occurred for channel ID: {channel_id}")
        print(f"Error message: {e}")

"""Put all meta data together"""

category_name_list = [category_names.get(category_id, 'N/A') for category_id in category_ids]
subscriber_count_list = [subscriber_counts.get(channel_id, 'N/A') for channel_id in channel_ids]
data = {
    "VideoID": video_ids,
    "ChannelID": channel_ids,
    "CategoryID": category_ids,
    "VideoTitle": video_titles,
    "ChannelTitle": channel_titles,
    "CategoryName": category_name_list,
    "SubscriberCount": subscriber_count_list,
    "ViewCount": view_counts,
    "LikeCount": like_counts,
    "DislikeCount": dislike_counts,
    "Duration": durations
}
df_meta = pd.DataFrame(data).reset_index()
df_meta['Duration'] = pd.to_timedelta(df_meta['Duration']).dt.total_seconds()
df_meta.to_csv('video_meta_data.csv',index=False)
df_meta.info()

"""Merge df and df_meta"""

df_merged = df[['Title','TitleClean','Timestamp']].merge(df_meta, left_on='Title', right_on='VideoTitle', how='inner')
df_merged = df_merged.loc[:, ~df_merged.columns.str.startswith('Unnamed')]
df_merged = df_merged.drop('Title',axis=1)
df_merged.info()

"""# Generate more features

Time features
"""

df_merged['Timestamp'] = df_merged['Timestamp'].apply(parser.parse)
df_merged['Year'] = df_merged['Timestamp'].dt.year
df_merged['Month'] = df_merged['Timestamp'].dt.month
df_merged['Day'] = df_merged['Timestamp'].dt.day
df_merged['Hour'] = df_merged['Timestamp'].dt.hour
df_merged['Weekdays'] = np.where(df_merged['Timestamp'].dt.weekday < 5, 0, 1)

"""Video features"""

# Convert 'LikeCount' and 'ViewCount' columns to numeric types
df_merged['LikeCount'] = pd.to_numeric(df_merged['LikeCount'], errors='coerce')
df_merged['ViewCount'] = pd.to_numeric(df_merged['ViewCount'], errors='coerce')

# Calculate the ratio between 'LikeCount' and 'ViewCount'
df_merged['LikeViewRatio'] = df_merged['LikeCount'] / df_merged['ViewCount']

df_merged.to_csv('merged_data.csv',index=False)
df_merged.info()