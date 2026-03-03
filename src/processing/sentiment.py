import pandas as pd
from transformers import pipeline

#load the csv file into a pandas dataframe
df = pd.read_csv('data/raw/articles.csv')

#initialize the sentiment analysis pipeline
sentiment = pipeline("sentiment-analysis")

#apply the sentiment analysis pipeline to the 'content' column of the dataframe
results = sentiment(df['body'].tolist(), truncation=True, max_length=512)

#add the results to the dataframe
df['sentiment'] = [result['label'] for result in results]
df['confidence'] = [result['score'] for result in results]


print(df.head())
#save the dataframe to a new csv file
df.to_csv('data/processed/articles_with_sentiment.csv', index=False)