import os
import json
import numpy as np
import pandas as pd
import argparse
from tqdm import tqdm
from elasticsearch import Elasticsearch
from newsplease import NewsPlease

from lib.logger import logger

#config
PREDICT_FILE_COLUMNS = ['tweet_id', 'vclaim_id', 'score', 'ratingName', 'link']
PREDICT_VCLAIMS_COLUMNS = ['_id', '_score', 'ratingName', 'link']
PREDICT_NEWS_COLUMNS = ['tweet_content','link']
INDEX_NAME = 'vclaim'

RATING_FILTER = ['TRUE', 'FALSE','MIXTURE', 'OTHER']
#RATING_FILTER = ['TRUE', 'FALSE']
MAX_OUTPUT_CLAIMS  = None

#modified by Erwin Letkemann for special uses
#right now only work for one url

def create_connection(conn_string):
    logger.debug("Starting ElasticSearch client")
    try:
        es = Elasticsearch([conn_string], sniff_on_start=True)
    except:
        raise ConnectionError(f"Couldn't connect to Elastic Search instance at: {conn_string} \
                                Check if you've started it or if it listens on the port listed above.")
    logger.debug("Elasticsearch connected")
    return es

def get_score(es, tweet, search_keys, size=10000):
    query = {"query": {"multi_match": {"query": tweet, "fields": search_keys}}}
    try:
        response = es.search(index=INDEX_NAME, body=query, size=size)
    except:
        logger.error(f"No elasticsearch results for {tweet}")
        raise

    results = response['hits']['hits']
    for result in results:
        info = result.pop('_source')
        result.update(info)
    df = pd.DataFrame(results)
    df['id'] = df._id.astype('int32').values
    df = df[PREDICT_VCLAIMS_COLUMNS]
    return df
    #df = df.set_index('id')
    #return df._score

def get_scores(es, tweets, search_keys, size):
    vclaims_count = es.cat.count(INDEX_NAME, params={"format": "json"})[0]['count']
    tweets_count  = len(tweets)
    scores = {}

    logger.info(f"Geting RM5 scores for {tweets_count} tweets and {vclaims_count} vclaims")
    for i, tweet in tqdm(tweets.iterrows(), total=tweets_count):
        score = get_score(es, tweet.tweet_content, search_keys=search_keys, size=size)
        scores[i] = score
    return scores

def format_scores(scores):
    formatted_scores = None
    for tweet_id, s in scores.items():   
        x,y = s.shape
        v = pd.DataFrame(data=np.transpose(np.random.randint(tweet_id,tweet_id+1,x)),columns=['tweet_id'])
        try:
            formatted_scores = np.append(formatted_scores,v.join(s).values,axis=0)
        except ValueError:
            formatted_scores = v.join(s).values

        #formatted_scores.append(row)
        formatted_scores_df = pd.DataFrame(formatted_scores, columns=PREDICT_FILE_COLUMNS)
        
        formatted_scores_df = formatted_scores_df[formatted_scores_df['ratingName'].isin(RATING_FILTER)] 

    return formatted_scores_df[:MAX_OUTPUT_CLAIMS]

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predict-file", "-p", default="result.csv",
                        help="File in TREC Run format containing the model predictions")
    parser.add_argument("--keys", "-k",nargs='+', default=['vclaim', 'title', 'named_entities_claim', 'named_entities_article'],
                        help="Keys to search in the document")
    parser.add_argument("--size", "-s", default=10000,
                        help="Maximum results extracted for a query")
    parser.add_argument("--output_size", "-x", default=10000,
                        help="Maximum results extracted for news")
    parser.add_argument("--conn", "-c", default="127.0.0.1:9200",
                        help="HTTP/S URI to a instance of ElasticSearch")
    parser.add_argument("--url", "-u", required=True,
                        help="HTTP/S URI to website wich should used for searching Claims")
    return parser.parse_args()

def main(args):
    article = NewsPlease.from_url(args.url)
    news = pd.DataFrame([(article.maintext.replace('\t','\b'),article.url)], columns=PREDICT_NEWS_COLUMNS)

    es = create_connection(args.conn)

    scores = get_scores(es, news, search_keys=args.keys, size=args.size)
    formatted_scores = format_scores(scores)
    formatted_scores.to_csv(args.predict_file, sep=',', index=False, header=False)
    logger.info(f"Saved scores from the model in file: {args.predict_file}")

    print(formatted_scores)

if __name__=='__main__':
    args = parse_args()
    MAX_OUTPUT_CLAIMS = args.output_size
    #print(args)
    main(args)