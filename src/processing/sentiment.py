import pandas as pd
import json
import time
import glob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from multiprocessing import Pool

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

all_files = glob.glob('data/raw/guardian_*.json')

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

    filename = filepath.split('/')[-1]  #just filename, without the path
    filename = filename.replace('.json', '')  #remove the .json extension
    df.to_csv(f'data/processed/articles_with_sentiment_{filename}.csv', index=False)