#Research question 4:
#To what degree does the co-occurrence of spikes across multiple news categories in the Guardian on the same day
# amplify the cumulative 3-day price return compared to days with an isolated single-category spike,
# and which asset class shows the greatest sensitivity to this multi-category overlap effect?


#get spike days for single article categories
#find days that only have spikes in single category
#find days that have spikes in all categories

#calculate x day return on each investment for all found dates

#compare different returns for single and all spike

from data_loader.py import compute_returns
from research_questions_2_implementation import get_spike_days_of_single_class, get_shared_spike_days
from glob import glob
import pandas as pd

#get all filepaths for the processed news data
paths = glob("data/processed/articles_with_sentiment_guardian*.csv")

def get_spike_days_of_all_category(paths):
    single_category_spike_days = []
    for path in paths:
        #get the name of the category
        category_name = path.replace("data/processed/articles_with_sentiment_guardian_","").replace(".csv", "")
        #read the news data for the current category into a DataFrame
        news_data = pd.read_csv(path)
        #calculate the spike days for the current news category
        spike_days = get_spike_days_of_single_class(news_data)
        #append the spike days to the list of all spike days
        single_category_spike_days.append((category_name,spike_days))
    return single_category_spike_days

single_category_spike_days = get_spike_days_of_all_category(paths)

shared_spike_days = get_shared_spike_days(all_spike_days)

for single_category_spike_day in single_category_spike_days:
    




