import argparse
import os
from nltk import tokenize
from nltk import download as nltk_download
from newsplease import NewsPlease
from newsfetch.news import newspaper
#
from . import lib

#for library use
def run(input, client, output_path, index_name):
    INPUT = str(input)
    CLIENT = lib.create_connection(client)
    OUTPUT_PATH = output_path
    INDEX_NAME = index_name
    MODE = "url"
    
    if not lib.check_index(client=CLIENT, index=INDEX_NAME):
        lib.logger.debug(f"{INDEX_NAME} not found.")
        return Exception(f"{INDEX_NAME} not found.")
    
    website = newspaper(INPUT)
    fulltext = website.article
    
    try:
        nltk_download('punkt')
    except:
        pass
    sentences = tokenize.sent_tokenize(fulltext.strip())
        
    scores_sentences = lib.get_scores(CLIENT, INDEX_NAME, sentences)
    format_scores_sentences = lib.format_scores(sentences, scores_sentences)
    result = lib.save_result(fulltext, INDEX_NAME, INPUT, format_scores_sentences, OUTPUT_PATH, MODE)
    return result