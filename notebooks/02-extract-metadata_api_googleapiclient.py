import os
import pandas as pd
from tqdm import tqdm
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
youtube_api_key = os.getenv('API_KEY')

# Load Watch History containing Title, Channel, and timestamp information
df = pd.read_csv('/Users/linwang/Documents/YoutubeData/data/processed/mydata.csv')
df.info()

# Only examine the top 10 viewed videos
video_ID = df['Video URL'].str.split('v=').str[1]
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
            category_id = snippet['categoryId']
            view_count = statistics.get('viewCount', 0)
            like_count = statistics.get('likeCount', 0)
            dislike_count = statistics.get('dislikeCount', 0)
            duration = content_details['duration']

            # Append the extracted information to the lists
            video_ids.append(video_id)
            channel_ids.append(channel_id)
            video_titles.append(video_title)
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

# get the category name for each video
category_name_list = [category_names.get(category_id, 'N/A') for category_id in category_ids]
data = {
    "VideoID": video_ids,
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
df_meta.to_csv('video_meta_data.csv')



################################################
## data exploration: only for top 10 channels
df = pd.read_csv('/Users/linwang/Documents/YoutubeData/data/processed/mydata.csv')
df_recent = df[df['Year'] >= 2016]
df_meta = pd.read_csv('/Users/linwang/Documents/YoutubeData/data/processed/video_meta_data.csv')
df_merged = df_recent[['Title','Timestamp','Year','Month','Weekdays','TimeOfDay','Hour']].merge(df_meta, left_on='Title', right_on='VideoTitle', how='inner')
df_merged = df_merged.loc[:, ~df_merged.columns.str.startswith('Unnamed')]
df_merged.to_csv('/Users/linwang/Documents/YoutubeData/data/processed/combined_data.csv')


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