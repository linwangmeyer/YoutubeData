import os
from dotenv import load_dotenv
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import json
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from PIL import Image
import numpy as np
import re
from collections import Counter
from tqdm import tqdm

# Load the environment variables from .env
load_dotenv()
youtube_api_key = os.getenv('API_KEY')

# Load Watch History containing Title, Channel and timestamp informaiton
df = pd.read_csv('/Users/linwang/Documents/YoutubeData/data/processed/mydata.csv')
df.info()

# only examine the top 10 viewed videos
channel_counts = df.query("Year >= 2016")['Channel'].dropna().value_counts().head(10)
top10_channels = channel_counts.index.tolist()
df_top10 = df[df['Channel'].isin(top10_channels)]
video_ID = df_top10['Video URL'].str.split('v=').str[1]
video_id_list = list(set(video_ID.to_list()))

# Create empty lists to store the extracted information
video_ids = []
channel_ids = []
video_titles = []
category_ids = []
view_counts = []
like_counts = []
dislike_counts = []
durations = []

# Iterate over each video ID in the DataFrame
progress_bar = tqdm(total=len(video_id_list), desc="Processing Videos", unit="video")
base_url = "https://www.googleapis.com/youtube/v3/videos"
for video_id in video_id_list:
    snippet_params = {
        "key": youtube_api_key,
        "id": video_id,
        "part": "snippet",
        "fields": "items(id,snippet(channelId,title,categoryId))"
    }
    statistics_params = {
        "key": youtube_api_key,
        "id": video_id,
        "part": "statistics",
        "fields": "items(statistics(viewCount,likeCount,dislikeCount))"
    }

    # Retrieve video snippet
    snippet_response = requests.get(base_url, params=snippet_params)
    snippet_data = snippet_response.json()

    # Retrieve video statistics
    statistics_response = requests.get(base_url, params=statistics_params)
    statistics_data = statistics_response.json()

    # Extract relevant information
    if "items" in snippet_data and "items" in statistics_data:
        snippet = snippet_data["items"][0]["snippet"]
        statistics = statistics_data["items"][0]["statistics"]

        channel_id = snippet["channelId"]
        video_title = snippet["title"]
        category_id = snippet["categoryId"]
        view_count = statistics.get("viewCount", 0)
        like_count = statistics.get("likeCount", 0)
        dislike_count = statistics.get("dislikeCount", 0)

        # Retrieve video duration
        video_info_url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={youtube_api_key}&part=contentDetails"
        video_info_response = requests.get(video_info_url)
        video_info_data = video_info_response.json()
        duration = video_info_data["items"][0]["contentDetails"]["duration"]

        # Append the extracted information to the lists
        video_ids.append(video_id)
        channel_ids.append(channel_id)
        video_titles.append(video_title)
        category_ids.append(category_id)
        view_counts.append(view_count)
        like_counts.append(like_count)
        dislike_counts.append(dislike_count)
        durations.append(duration)
    # Update the progress bar
    progress_bar.update(1)
    
# Close the progress bar
progress_bar.close()


# Get the category name for the category ID
base_url = "https://www.googleapis.com/youtube/v3/videoCategories"
uni_category_ids = set(category_ids)
category_names = {}
for id in uni_category_ids:    
    params = {
        "key": youtube_api_key,
        "id": id,
        "part": "snippet"
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    category_names[id] = data["items"][0]["snippet"]["title"]

# get the category name for each video
category_name_list = [category_names.get(category_id, 'N/A') for category_id in category_ids]

# Create a new DataFrame with the extracted information
data = {
    "VideoID": video_id_list[:143],
    "ChannelID": channel_ids,
    "VideoTitle": video_titles,
    "CategoryID": category_ids,
    "CategoryName": category_name_list,
    "ViewCount": view_counts,
    "LikeCount": like_counts,
    "DislikeCount": dislike_counts,
    "Duration": durations
}

df_meta = pd.DataFrame(data)
df_meta['Duration'] = pd.to_timedelta(df_meta['Duration']).dt.total_seconds()

df_meta.to_csv('video_meta_data')



################################################
## data exploration: only for top 10 channels
df = pd.read_csv('/Users/linwang/Documents/YoutubeData/data/processed/mydata.csv')
top10_channels = df.query("Year >= 2016")['Channel'].dropna().value_counts().head(10).index.tolist()
df_top10 = df[df['Channel'].isin(top10_channels)]
df_top10['VideoID'] = df_top10['Video URL'].str.split('v=').str[1]

df_meta = pd.read_csv('video_meta_data.csv')
df_merged = df_top10[['VideoID','Timestamp','Year','Month','Weekdays','TimeOfDay']].merge(df_meta, on='VideoID', how='inner')



# Visualizing Video Categories
category_counts = df_merged["CategoryName"].value_counts().reset_index()
category_counts.columns = ["CategoryName", "count"]
category_counts = category_counts.sort_values("count", ascending=False)
print(category_counts)

plt.figure(figsize=(10, 6))
chart = category_counts.plot(kind='bar')
chart.set_xticklabels(category_counts.index, rotation=45, ha='right')
plt.xlabel('Category')
plt.ylabel('Count')
plt.title('Top 4 Counts of categories')
plt.show()

category_counts.plot(x="category", y="count", kind="bar", legend=False)
plt.xlabel("Category")
plt.ylabel("Count")
plt.title("Video Categories Watched")
plt.show()

# Visualizing Clock Watches per Hour
clock_df = df_merged.groupby(df_merged["Duration"]).size().reset_index(name="count")
fig = plt.figure()
ax = fig.add_subplot(111, polar=True)
ax.plot(np.radians(clock_df["time"] * 15), clock_df["count"])
ax.set_xticks(np.radians(np.arange(0, 360, 30)))
ax.set_xticklabels(["12AM", "3AM", "6AM", "9AM", "12PM", "3PM", "6PM", "9PM"])
ax.set_title("Time of Day for Watching YouTube")
ax.grid(True)
plt.show()

# Most Re-Watched Videos
most_rewatched = df_merged.groupby(["Year", "VideoTitle"]).size().reset_index(name="count")
most_rewatched = most_rewatched.sort_values(["Year", "count"], ascending=[True, False])
most_rewatched = most_rewatched.groupby("Year").head(5)
print(most_rewatched)

# Word Cloud for Most frequent Words
search_words = df_merged["VideoTitle"].str.lower().str.split()
search_words = [word for sublist in search_words for word in sublist]
word_counts = dict(Counter(search_words))

mask = np.array(Image.open("cloud_mask.png"))
wordcloud = WordCloud(background_color="white", mask=mask).generate_from_frequencies(word_counts)
plt.imshow(wordcloud, interpolation="bilinear")
plt.axis("off")
plt.show()

