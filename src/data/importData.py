import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
import nltk
from nltk.corpus import stopwords
import pytz
from datetime import datetime
from dateutil import parser


# Load the environment variables from .env
load_dotenv()
api_key = os.getenv('API_KEY')
print(api_key)


# Load and parse the HTML file
with open('/Users/linwang/Documents/YoutubeData/data/raw/Takeout/YouTube and YouTube Music/history/watch-history.html', 'r') as file:
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
df.replace('', np.nan, inplace=True)

# get more time information
df['Timestamp'] = df['Timestamp'].apply(parser.parse)
df['Year'] = df['Timestamp'].dt.year  # Extract the year from 'Timestamp' column
df['Month'] = df['Timestamp'].dt.month  # Extract the month from 'Timestamp' column
df['Weekdays'] = np.where(df['Timestamp'].dt.weekday < 5, 0, 1) #Weekdays as 0 and weekends as 1 
df['TimeOfDay'] = pd.cut(df['Timestamp'].dt.hour,
                         bins=[0, 5, 9, 17, 24],
                         labels=['After Midnight', 'Early Morning', 'Working Hours', 'After Work Hours'],
                         right=False) # Categorize the hour of the day
df.to_csv('mydata.csv', index=False)


