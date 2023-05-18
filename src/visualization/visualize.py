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

# Calculate the average count per month for each year
average_counts = df.groupby(['Year', 'Month']).size().groupby('Year').mean()
fig, ax = plt.subplots(figsize=(10, 6))
average_counts.plot(kind='line', marker='o', ax=ax)
ax.set_xlabel('Year')
ax.set_ylabel('Average Count per Month')
ax.set_title('Average Count per Month for Each Year')
plt.show()


# Plot the channel counts since 2016
channel_counts = df.query("Year >= 2016")['Channel'].dropna().value_counts().head(10)
plt.figure(figsize=(10, 6))
chart = channel_counts.plot(kind='bar')
chart.set_xticklabels(channel_counts.index, rotation=45, ha='right')
plt.xlabel('Channel')
plt.ylabel('Count')
plt.title('Top 10 Counts of Channels')
plt.show()

# plot channel count since 2016, grouped by time of day
top_10_channels = df.query("Year >= 2016").groupby('TimeOfDay')['Channel'].value_counts().groupby(level=0).nlargest(10)
fig, axes = plt.subplots(nrows=4, ncols=1, figsize=(18, 18))
time_of_day_labels = ['5am-9am', '9am-5pm', '5pm-12am', '12am-5am']
for i, (time_of_day, channel_counts) in enumerate(top_10_channels.groupby(level=0)):
    ax = axes[i]
    channel_counts.plot(kind='bar', ax=ax)
    ax.set_title(f"Top 10 Channel Counts - {time_of_day} ({time_of_day_labels[i]})")
    ax.set_xlabel('Channel')
    ax.set_ylabel('Count')
    ax.set_xticklabels(channel_counts.index.get_level_values('Channel'), rotation=45, ha='right')
plt.tight_layout()
plt.show()

# plot the watching time of day for specified channels
plot_list = ['Ali Abdaal', 'Super Simple Songs - Kids Songs', 'YouAligned', 'StatQuest with Josh Starmer']
fig, ax = plt.subplots(figsize=(12, 6))
for channel in plot_list:
    channel_data = df[df['Channel'] == channel]
    channel_counts = channel_data['TimeOfDay'].value_counts().sort_index()
    ax.plot(channel_counts.index, channel_counts.values, label=channel)
ax.set_xlabel('Year')
ax.set_ylabel('Count')
ax.set_title('Count of Top 10 Channels over the Years')
ax.legend()
plt.show()

# For top 10 channels, plot count along time
top_10_channels = df['Channel'].value_counts().nlargest(10).index
fig, ax = plt.subplots(figsize=(12, 6))
for channel in top_10_channels:
    channel_data = df[df['Channel'] == channel]
    channel_counts = channel_data['Year'].value_counts().sort_index()
    ax.plot(channel_counts.index, channel_counts.values, label=channel)
ax.set_xlabel('Year')
ax.set_ylabel('Count')
ax.set_title('Count of Top 10 Channels over the Years')
ax.legend()
plt.show()

