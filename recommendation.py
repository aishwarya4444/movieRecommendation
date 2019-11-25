# USAGE
# Start the server:
# 	python catalog_enrichment_server.py
# Submit a request via cURL:
# 	curl -X POST http://localhost:5000/predict?text=Wolf%20Printed%20Polo%20Neck%20T-Shirt

import sys
import io
import json
import numpy as np
import pandas as pd
from datetime  import datetime
from scipy.sparse.linalg import svds, eigs
from sklearn.metrics.pairwise import cosine_similarity
import operator
from flask import Flask, request, render_template, jsonify

# initialize our Flask application
app = Flask(__name__)
initialRecommendation = None
user_movie_rating_df = None
rating_feature_columns = None

def initModel():
    global initialRecommendation, user_movie_rating_df, rating_feature_columns
    movies_df = pd.read_csv('movies.csv')
    ratings_df = pd.read_csv('ratings.csv')
    movieId_to_genres = pd.DataFrame(movies_df.genres.str.split('|').tolist(), index=movies_df.movieId).stack().reset_index()[['movieId', 0]]
    movies_df_expanded = movieId_to_genres.merge(movies_df[['movieId', 'title']], how='left', left_on='movieId', right_on='movieId')
    movies_df_expanded.columns = ['movieId', 'genre', 'title']
    movies_idx = movies_df[['movieId', 'title']].set_index('title')['movieId']
    ratings_df.timestamp = ratings_df.timestamp.apply(lambda x: datetime.fromtimestamp(x).year)

    user_movie_rating_df = ratings_df.pivot(index='movieId', columns='userId', values='rating').fillna(0.0)
    user_movie_rating_df = movies_df.merge(user_movie_rating_df, right_index=True, left_on='movieId')
    rating_feature_columns = list(range(1, 611))
    user_movie_rating_data = user_movie_rating_df[rating_feature_columns]
    user_mov_ratings = user_movie_rating_df[rating_feature_columns].T
    user_rating_means = (user_mov_ratings.values).sum(axis=1) / (user_mov_ratings.values > 0).sum(axis=1)
    user_mov_ratings_demean = user_mov_ratings.values - user_rating_means.reshape(-1, 1)
    U, sigma, Vt = svds(user_mov_ratings_demean, k = 50)
    movies_df_with_svd = pd.concat([user_movie_rating_df.reset_index()[['movieId', 'title', 'genres']], pd.DataFrame(Vt.T)], axis=1)
    movie_feature_columns = list(range(Vt.shape[0]))

    # initial recommendations
    popular_movie_ids = ratings_df.merge(movies_df, left_on='movieId', right_on='movieId')\
        .groupby('movieId')\
        .count()\
        .sort_values('rating')\
        .tail(20)\
        .index\
        .tolist()
    initialReco = pd.concat([movies_df[movies_df['movieId']==movieId] for movieId in popular_movie_ids])
    initialRecommendation = dict(zip(initialReco.movieId, initialReco.title))

def get_similar_movies_fast(movie_id, data_frame, feature_columns, sim_function, number_of_recommendations=10):
    # Get query movie features
    query_row = data_frame.loc[data_frame.movieId==movie_id]
    query_feats = query_row[feature_columns].values

    # Get features of all other movies in a m*n array
    # where m is the number of movies and n is the number of features
    data_feats = data_frame[feature_columns].values

    # apply the similarity function on the 2 features sets
    similarities = sim_function(data_feats, query_feats)

    # Sort by similarity and return n most similar movies
    movie_id_similarity = zip(data_frame.movieId.values, similarities)
    movie_id_similarity = sorted(movie_id_similarity, key=operator.itemgetter(1), reverse=True)

    movie_id_similarity = pd.DataFrame(movie_id_similarity[:number_of_recommendations+1],
                                       columns=['movieId', 'similarity'])

    movie_id_similarity = movie_id_similarity[movie_id_similarity.movieId!=movie_id]

    movie_id_similarity = movie_id_similarity.merge(data_frame,
                                                    left_on='movieId',
                                                    right_on='movieId')[:number_of_recommendations]

    return movie_id_similarity[['movieId', 'title', 'genres', 'similarity']]

def get_similarity_cosine(query_feats, data_feats):
    similarities = cosine_similarity(query_feats, data_feats)
    return similarities.flatten()

@app.route('/', methods=['GET'])
def index():
    # Main page
    return render_template('index.html')

@app.route('/welcome', methods=['GET'])
def welcome():
    # print(initialRecommendation)
    return jsonify(initialRecommendation)

@app.route("/recommend", methods=["POST"])
def recommend():
    resultList = {}
    movieId = int(request.data)
    # print(movieId)
    # movieId = 3
    print('recommendation requested for movie id :', movieId)
    result = get_similar_movies_fast(movieId, user_movie_rating_df, rating_feature_columns, get_similarity_cosine)
    resultList = dict(zip(result.movieId, result.title))
    return jsonify(resultList)

# if this is the main thread of execution first load the model and
# then start the server
if __name__ == "__main__":
	print("flask server starting ...")
	initModel()
	app.run(host='0.0.0.0')
