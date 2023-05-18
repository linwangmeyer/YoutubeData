import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pytz
from datetime import datetime
from dateutil import parser

# Load the environment variables from .env
load_dotenv()
api_key = os.getenv('API_KEY')

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
df.to_csv('/Users/linwang/Documents/YoutubeData/data/processed/rawdata.csv', index=False)


################################################
## data cleaning and generating more features
df = pd.read_csv('/Users/linwang/Documents/YoutubeData/data/processed/rawdata.csv')
df = df.dropna(subset=['Channel','Title'])

# get more time information
df['Timestamp'] = df['Timestamp'].apply(parser.parse)
df['Year'] = df['Timestamp'].dt.year  # Extract the year from 'Timestamp' column
df['Month'] = df['Timestamp'].dt.month  # Extract the month from 'Timestamp' column
df['Weekdays'] = np.where(df['Timestamp'].dt.weekday < 5, 0, 1) #Weekdays as 0 and weekends as 1 
df['Hour'] = df['Timestamp'].dt.hour
df['TimeOfDay'] = pd.cut(df['Timestamp'].dt.hour,
                         bins=[0, 5, 9, 17, 24],
                         labels=['After Midnight', 'Early Morning', 'Working Hours', 'After Work Hours'],
                         right=False) # Categorize the hour of the day
df.to_csv('/Users/linwang/Documents/YoutubeData/data/processed/mydata.csv', index=False)


################################################
## data exploration
df = pd.read_csv('/Users/linwang/Documents/YoutubeData/data/processed/mydata.csv')
category_order = ['Early Morning', 'Working Hours', 'After Work Hours', 'After Midnight']
df['TimeOfDay'] = df['TimeOfDay'].astype('category').cat.set_categories(category_order)

# Calculate the average count per month for each year
average_counts = df.groupby(['Year', 'Month']).size().groupby('Year').mean()
fig, ax = plt.subplots(figsize=(10, 6))
average_counts.plot(kind='line', marker='o', ax=ax)
x_ticks = np.arange(2012, 2024)  # Generate tick positions at every 2 hours
ax.set_xticks(x_ticks)  # Set the tick positions
ax.set_xticklabels(x_ticks)  # Set the tick labels
ax.set_xlabel('Year')
ax.set_ylabel('Average Count per Month')
ax.set_title('Average Count per Month for Each Year')
plt.savefig('/Users/linwang/Documents/YoutubeData/reports/figures/fig1-countbyyear.png')
plt.show()

# Calculate the the average count of videos based on the hour of the day
average_counts = df.groupby(['Year', 'Month', 'Hour']).size().groupby('Hour').mean()
fig, ax = plt.subplots(figsize=(10, 6))
average_counts.plot(kind='line', marker='o', ax=ax)
x_ticks = np.arange(0, 24)  # Generate tick positions at every 2 hours
ax.set_xticks(x_ticks)  # Set the tick positions
ax.set_xticklabels(x_ticks)  # Set the tick labels
ax.set_xlabel('Hour of the Day')
ax.set_ylabel('Average Counts of Videos Watched')
ax.set_title('Average Video Counts by Hour of the Day')
plt.savefig('/Users/linwang/Documents/YoutubeData/reports/figures/fig2-countbyhour.png')


# Plot the channel counts since 2016
channel_counts = df.query("Year >= 2016")['Channel'].dropna().value_counts().head(10)
plt.figure(figsize=(10, 6))
chart = channel_counts.plot(kind='bar')
chart.set_xticklabels(channel_counts.index, rotation=45, ha='right')
plt.xlabel('Channel')
plt.ylabel('Count')
plt.title('Top 10 Counts of Channels')
plt.savefig('/Users/linwang/Documents/YoutubeData/reports/figures/fig3-countbychannel.png')
plt.show()

# For top 4 selected channels, plot total count along time, area under the curve
top_10_channels = df['Channel'].value_counts().nlargest(10).index
items = ['Ali Abdaal', 'Super Simple Songs - Kids Songs', 'YouAligned', 'StatQuest with Josh Starmer']
fig, ax = plt.subplots(figsize=(12, 6))
for i, channel in enumerate(items):
    channel_counts = df[df['Channel'] == channel]['Hour'].value_counts().sort_index()
    ax.fill_between(channel_counts.index, 0, channel_counts.values, alpha=0.3, label=channel)
x_ticks = np.arange(5, 24)  # Generate tick positions at every 2 hours
ax.set_xticks(x_ticks)  # Set the tick positions
ax.set_xticklabels(x_ticks)  # Set the tick labels
ax.set_xlabel('Hour')
ax.set_ylabel('Count')
ax.set_title('Total Video Counts by Hours of the Day (Area Under the Curve)')
ax.legend(loc='upper center')  # Position the legend to the top-left corner
plt.savefig('/Users/linwang/Documents/YoutubeData/reports/figures/fig4-countbychannel_hour.png')
plt.show()

# plot the average count per hour for listed channels
items = ['Ali Abdaal', 'Super Simple Songs - Kids Songs', 'YouAligned', 'StatQuest with Josh Starmer']
fig, ax = plt.subplots(figsize=(10, 6))
for item in items:
    average_counts = df[df['Channel'] == item].groupby(['Year', 'Month', 'Hour']).size().groupby('Hour').mean()
    ax.plot(average_counts.index, average_counts.values, marker='o', label=item)
x_ticks = np.arange(5, 24)  # Generate tick positions at every 2 hours
ax.set_xticks(x_ticks)  # Set the tick positions
ax.set_xticklabels(x_ticks)  # Set the tick labels
ax.set_xlabel('Hour of the Day')
ax.set_ylabel('Average Counts of Videos Watched')
ax.set_title('Average Video Counts by Hour of the Day')
ax.legend()


# For top 10 channels, plot total count along time
top_10_channels = df['Channel'].value_counts().nlargest(10).index
fig, ax = plt.subplots(figsize=(12, 6))
for channel in top_10_channels:
    channel_data = df[df['Channel'] == channel]
    channel_counts = channel_data['Hour'].value_counts().sort_index()
    ax.plot(channel_counts.index, channel_counts.values, label=channel)
ax.set_xlabel('Hour')
ax.set_ylabel('Count')
ax.set_title('Total Video Counts by Hours of the Day')
ax.legend()
plt.show()


