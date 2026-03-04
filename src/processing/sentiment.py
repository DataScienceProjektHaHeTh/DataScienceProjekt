import pandas as pd
import json
from transformers import pipeline

#load the json file
with open('data/raw/guardian_articles.json', 'r') as f:
    raw_data = json.load(f)

#flatten the structure into a dataframe
df = pd.DataFrame([{
    "date": article['webPublicationDate'][:10],
    "title": article['webTitle'],
    "body": article.get('fields', {}).get('bodyText', ''),
}for article in raw_data])


#initialize the sentiment analysis pipeline
sentiment = pipeline("sentiment-analysis")

#apply the sentiment analysis pipeline to the 'content' column of the dataframe
results = sentiment(df['body'].tolist(), batch_size=32, truncation=True, max_length=256)

#add the results to the dataframe
df['sentiment'] = [result['label'] for result in results]
df['confidence'] = [result['score'] for result in results]


print(df.head())
#save the dataframe to a new csv file
df.to_csv('data/processed/articles_with_sentiment.csv', index=False)