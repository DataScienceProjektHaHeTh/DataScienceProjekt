import pandas as pd
import os

#import the raw csv file into a pandas dataframe
df = pd.read_csv('data/raw/articles.csv')

#remove rows with missing values
df = df.dropna()

#save the cleaned dataframe to a new csv file
df.to_csv('data/processed/articles_cleaned.csv', index=False)