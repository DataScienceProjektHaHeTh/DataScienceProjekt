import pandas as pd
import json
import time
import glob
import os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from multiprocessing import Pool

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PROCESSED_ARTICLES_WITH_SENTIMENT = os.path.join(BASE_DIR, "../../data/processed/articles_with_sentiment")
DATA_RAW_ARTICLES = os.path.join(BASE_DIR, "../../data/raw/news")

os.makedirs(DATA_PROCESSED_ARTICLES_WITH_SENTIMENT, exist_ok=True)

#function calling Vader on the Text, return the Score
def get_sentiment_scores(text):
    #initialize the sentiment analysis pipeline
    sia = SentimentIntensityAnalyzer()
    scores = sia.polarity_scores(text[:512])
    return scores["compound"]

#Function for turning the Vader score into a "usefull" label
def get_sentiment_label(score):
    if score >= 0.05:
        return 'positive'
    elif score <= -0.05:
        return 'negative'
    else:
        return 'neutral'

all_files = glob.glob(os.path.join(DATA_RAW_ARTICLES, "*.json"))

for filepath in all_files:
    print(f"Processing file: {filepath}")

    #load the json file
    with open(filepath, 'r') as f:
        raw_data = json.load(f)

    #flatten the structure into a dataframe
    df = pd.DataFrame([{
        "date": article['webPublicationDate'][:10],
        "title": article['webTitle'],
        "body": article.get('fields', {}).get('bodyText', ''),
    }for article in raw_data])
        
    start = time.time()

    compound_list =  []
    #Use multiprocessing to speed up the sentiment analysis
    with Pool() as pool:
        compound_list = pool.map(get_sentiment_scores, df['body'].tolist())

    end = time.time()
    print(f"Sentiment analysis completed in {end - start:.2f} seconds")

    #add the compount values to the df
    df['compound'] = compound_list

    #get the labels
    sentiment_labels = []
    for score in df['compound']:
        label = get_sentiment_label(score)
        sentiment_labels.append(label)

    #add labels to the df
    df["sentiment"] = sentiment_labels

    print(df.head())
    #save the dataframe to a new csv file

    filename = os.path.basename(filepath).replace(".json", "")
    df.to_csv(os.path.join(DATA_PROCESSED_ARTICLES_WITH_SENTIMENT, f"{filename}_with_sentiment.csv"), index=False)