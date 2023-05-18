import os
import pandas as pd
from tqdm import tqdm
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Load API key from .env file
load_dotenv()
youtube_api_key = os.getenv('API_KEY')

# Load Watch History containing Title, Channel, and timestamp information
df = pd.read_csv('/Users/linwang/Documents/YoutubeData/data/processed/mydata.csv')
df.info()

# Get meta data for every video
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

##############################################
# Get the category name for the category ID
uni_category_ids = set(category_ids)
category_names = {}
for category_id in uni_category_ids:
    response = youtube.videoCategories().list(
        part='snippet',
        id=category_id
    ).execute()
    if 'items' in response:
        category_names[category_id] = response['items'][0]['snippet']['title']


################################################
# Get subscriber count information for each channel
channelIDs = list(set(channel_ids))
subscriber_counts = []
for channel_id in channelIDs:
    try:
        # Retrieve channel statistics using channels().list() method
        channel_response = youtube.channels().list(
            part='statistics',
            id=channel_id
        ).execute()
        
        if 'items' in channel_response and channel_response['items']:
            channel_data = channel_response['items'][0]
            subscriber_count = channel_data['statistics'].get('subscriberCount', 0)
            subscriber_counts.append(subscriber_count)
        else:
            subscriber_counts.append(0)
            
    except HttpError as e:
        print(f"An error occurred for channel ID: {channel_id}")
        print(f"Error message: {e}")

# Assign the subscriber counts to a new column in the DataFrame
df_subscriber = pd.DataFrame({"ChannelID": channelIDs,
                            "SubscriberCount": subscriber_counts})

##########################################
# get the category name for each video, number of subscribers for each channel
category_name_list = [category_names.get(category_id, 'N/A') for category_id in category_ids]
data = {
    "VideoID": video_ids,
    "ChannelID": channel_ids,
    "CategoryID": category_ids,
    "VideoTitle": video_titles,
    "ChannelTitle": channel_titles,
    "CategoryName": category_name_list,
    "ViewCount": view_counts,
    "LikeCount": like_counts,
    "DislikeCount": dislike_counts,
    "Duration": durations
}

df_meta = pd.DataFrame(data).reset_index()
df_meta['Duration'] = pd.to_timedelta(df_meta['Duration']).dt.total_seconds()
df_meta.to_csv('/Users/linwang/Documents/YoutubeData/data/processed/video_meta_data.csv',index=False)


################################################
df_meta = pd.read_csv('/Users/linwang/Documents/YoutubeData/data/processed/video_meta_data.csv')

## Video Categories
category_counts = df_meta["CategoryName"].value_counts().reset_index()
category_counts.columns = ["CategoryName", "count"]
category_counts = category_counts.sort_values("count", ascending=False)
plt.figure(figsize=(10, 6))
chart = category_counts.plot(kind='bar')
chart.set_xticklabels(category_counts['CategoryName'], rotation=45, ha='right')
plt.xlabel('Category')
plt.ylabel('Count')
plt.title('Top Counts of categories')
plt.show()

####################################
# Histogram of video durations
plt.hist(df_meta['Duration'], bins=20)
plt.xlabel('Duration (Seconds)')
plt.ylabel('Frequency')
plt.title('Distribution of Video Durations')
plt.show()

# check extreme values
df_extreme = df_meta[df_meta['Duration']>100000]
print(df_extreme[['VideoTitle','Duration']])

# visualize only non-extreme values
duration_range = (0, 1000)
plt.hist(df_meta['Duration'], bins=20, range=duration_range)
plt.xlabel('Duration (Seconds)')
plt.ylabel('Frequency')
plt.title('Distribution of Video Durations')
plt.show()

####################################
# Relationship between variables
fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(15, 5))
# Scatter plot for 'ViewCount' vs. 'LikeCount'
axes[0].scatter(df_meta['ViewCount'], df_meta['LikeCount'])
axes[0].set_title('View Count vs. Like Count')
axes[0].set_xlabel('View Count')
axes[0].set_ylabel('Like Count')
# Scatter plot for 'ViewCount' vs. 'Duration'
axes[1].scatter(df_meta['ViewCount'], df_meta['Duration'])
axes[1].set_title('View Count vs. Duration')
axes[1].set_xlabel('View Count')
axes[1].set_ylabel('Duration')
# Scatter plot for 'LikeCount' vs. 'Duration'
axes[2].scatter(df_meta['LikeCount'], df_meta['Duration'])
axes[2].set_title('Like Count vs. Duration')
axes[2].set_xlabel('Like Count')
axes[2].set_ylabel('Duration')
plt.tight_layout()
plt.show()

#### Scatter plot, color coded by CategoryName
# Scatter plot of ViewCount vs LikeCount, color coded by CategoryName
plotdata = df_meta[~df_meta['CategoryName'].isin(['Music','Education'])]
plt.figure(figsize=(10, 6))
sns.scatterplot(data=plotdata, x='ViewCount', y='LikeCount', hue='CategoryName')
plt.xlabel('View Count')
plt.ylabel('Like Count')
plt.title('Relationship between View Count and Like Count (Color coded by Category)')
plt.xlim(0,500000000)
plt.show()

# Scatter plot of Duration vs LikeCount, color coded by CategoryName
df_normal = df_meta[df_meta['Duration']<=100000]
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df_normal, x='Duration', y='LikeCount', hue='CategoryName')
plt.xlabel('Duration')
plt.ylabel('Like Count')
plt.title('Relationship between Duration and Like Count (Color coded by Category)')
plt.show()

# Scatter plot of Duration vs ViewCount, color coded by CategoryName
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df_normal, x='Duration', y='ViewCount', hue='CategoryName')
plt.xlabel('Duration')
plt.ylabel('Like Count')
plt.title('Relationship between Duration and View Count (Color coded by Category)')
plt.show()

###################################
df_meta['Ratio'] = df_meta['LikeCount'] / df_meta['ViewCount']
# Group the DataFrame by CategoryName and calculate the mean ratio
category_ratios = df_meta.groupby('CategoryName')['Ratio'].mean()
sorted_ratios = category_ratios.sort_values(ascending=False)
# Plotting the ratio differences across categories
plt.figure(figsize=(10, 6))
sorted_ratios.plot(kind='bar')
plt.xlabel('Category')
plt.ylabel('Mean Ratio')
plt.title('Ratio Differences Across Categories')
plt.xticks(rotation=45,ha='right')
plt.show()


################################################
df = pd.read_csv('/Users/linwang/Documents/YoutubeData/data/processed/data-formodel.csv')
df.info()

unique_rows = df.drop_duplicates(subset=['VideoID'], keep='first')
df_m = unique_rows[['VideoTitle', 'SubscriberCount', 'ViewCount', 'LikeCount', 'DislikeCount', 'Duration', 'LikeViewRatio']]

selected_columns = ['SubscriberCount', 'ViewCount', 'LikeCount', 'DislikeCount', 'Duration']
subset_df = df[selected_columns]
fig, axes = plt.subplots(nrows=len(selected_columns), figsize=(8, 10))
for i, column in enumerate(selected_columns):
    sns.histplot(data=subset_df, x=column, kde=True, ax=axes[i])
    axes[i].set_xlabel(column)
    axes[i].set_ylabel('Frequency')
plt.tight_layout()
plt.savefig('fig9-data-distribution.png')
plt.show()

  
# visualize pairwise relationship
subset_df = df[selected_columns]
sns.pairplot(subset_df)
plt.show()

np.exp(-20)