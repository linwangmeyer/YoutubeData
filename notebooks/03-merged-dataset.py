import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

################################################
## Merge datasets
df = pd.read_csv('/Users/linwang/Documents/YoutubeData/data/processed/mydata.csv')
df_recent = df[df['Year'] >= 2016]
df_meta = pd.read_csv('/Users/linwang/Documents/YoutubeData/data/processed/video_meta_data.csv')
df_merged = df_recent[['Title','Timestamp','Year','Month','Weekdays','TimeOfDay','Hour']].merge(df_meta, left_on='Title', right_on='VideoTitle', how='inner')
df_merged = df_merged.loc[:, ~df_merged.columns.str.startswith('Unnamed')]
df_merged = df_merged.drop('Title',axis=1)
df_merged.to_csv('/Users/linwang/Documents/YoutubeData/data/processed/combined_data.csv',index=False)

################################################
## data exploration: since 2016
df_merged = pd.read_csv('/Users/linwang/Documents/YoutubeData/data/processed/combined_data.csv')

# Visualizing Video Categories for each year: top 5
category_counts = df_merged.groupby(["Year", "CategoryName"]).size().reset_index(name="count")
category_counts = category_counts.sort_values(["Year", "count"], ascending=[True, False])
category_counts = category_counts.groupby("Year").head(5)
plt.figure(figsize=(12, 6))
sns.barplot(x='Year', y='count', hue='CategoryName', data=category_counts, width=0.8, dodge=False)
plt.title('Top 5 Categories by Year')
plt.xlabel('Year')
plt.ylabel('Count of Views')
plt.legend(title='Category Name', bbox_to_anchor=(1, 1), loc='upper left')
plt.show()

# Visualizing Video Categories by hour: top 5
category_counts = df_merged.groupby(["Hour", "CategoryName"]).size().reset_index(name="count")
category_counts = category_counts.sort_values(["Hour", "count"], ascending=[True, False])
category_counts = category_counts.groupby("Hour").head(5)
plt.figure(figsize=(12, 6))
sns.barplot(x='Hour', y='count', hue='CategoryName', data=category_counts, width=0.8, dodge=False)
plt.title('Top 5 Categories by Hour')
plt.xlabel('Hour')
plt.ylabel('Count of Views')
plt.legend(title='Category Name', bbox_to_anchor=(1, 1), loc='upper left')
plt.show()

# Group the DataFrame by Hour and CategoryName, and calculate the average duration
grouped = df_merged.groupby(['Hour', 'CategoryName'])['Duration'].mean()/60
grouped = grouped.reset_index()
plot_data = grouped.sort_values('Duration',ascending=False).head(10)
plt.figure(figsize=(12, 6))
sns.barplot(x='Hour', y='Duration', hue='CategoryName', data=plot_data, palette='Set1')
plt.title('Average Duration by Hour and Category')
plt.xlabel('Hour of the Day')
plt.ylabel('Duration (minutes)')
plt.show()

