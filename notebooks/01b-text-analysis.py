import pandas as pd
import re
import nltk
from nltk.corpus import stopwords
import re
import string
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import emoji
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from gensim import corpora, models
from collections import Counter

##############################################
## pre-process text data
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

    # Remove emojis
    text = emoji.demojize(text)
    text = re.sub(r':[a-z_]+:', '', text)

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

df = pd.read_csv('/Users/linwang/Documents/YoutubeData/data/processed/mydata.csv')
df_preprocessed = df['Title'].apply(preprocess_text)
df_preprocessed.to_csv('/Users/linwang/Documents/YoutubeData/data/processed/videotitle-preprocessed.csv', index=False)

#####################################################
# Use wordcloud to visualize texts
combined_text = ' '.join(df_preprocessed)
word_frequencies = Counter(combined_text.split())
wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(word_frequencies)
plt.figure(figsize=(10, 5))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
plt.show()


#####################################################
## topic modeling
# Tokenize the titles
tokenized_titles = [title.split() for title in df_preprocessed]

# Create a dictionary from the tokenized titles
dictionary = corpora.Dictionary(tokenized_titles)

# Create a corpus
corpus = [dictionary.doc2bow(title) for title in tokenized_titles]

# Set the number of topics
num_topics = 12

# Build the LDA model
lda_model = models.LdaModel(corpus, num_topics=num_topics, id2word=dictionary, passes=10)

# Print the topics
for topic_num in range(num_topics):
    print(f"Topic #{topic_num + 1}:")
    print(lda_model.print_topic(topic_num))
    print()
    
# Assign topic labels
topic_labels = ['Topic 1', 'Topic 2', 'Topic 3', 'Topic 4', 'Topic 5']  # Provide meaningful labels for your topics
    
# Assign dominant topic for each title
topics = []
for bow in corpus:
    topic_distribution = lda_model.get_document_topics(bow)
    dominant_topic = max(topic_distribution, key=lambda x: x[1])
    topics.append(dominant_topic[0])

# Create a new DataFrame with titles and corresponding topics
titles_with_topics = pd.DataFrame({'Title': df['Title'], 'Topic': topics})
titles_with_topics['Topic'] = titles_with_topics['Topic'].map(lambda x: topic_labels[x])

# Print the titles with their assigned topics
print(titles_with_topics)