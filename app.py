import streamlit as st
import pickle
import pandas as pd
import requests
from PIL import Image
import numpy as np
import re
from io import BytesIO
st.set_page_config(page_title='Movie Recommendation System', layout='wide')
mood_dict = {'Happy': 'Horror', 'Sad': 'Drama', 'Satisfied': 'Animation', 'Angry': 'Romance', 'Peaceful': 'Fantasy',
             'Fearful': 'Adventure', 'Excited': 'Crime', 'Depressed': 'Comedy', 'Content': 'Mystery', 'Sorrowful': 'Action'}


def generate_set(attribute):
    Set = set()
    movies[attribute] = movies[attribute].apply(
        lambda x: [] if x != x else (x if isinstance(x, list) else [x]))
    for x in [movies.iloc[x] for x in range(len(list(movies[attribute])))]:
        for y in x.get(attribute):
            Set.add(y)
    if('' in Set):
        Set.remove('')
    return list(Set)


def fetch_poster(index):
    path = movies.iloc[index].poster_path
    if(path != path):
        path = 'poster.png'
    else:
        response = requests.get(path)
        if(response.status_code != 200):
            path = 'poster.png'
        else:
            path = BytesIO(response.content)
    return Image.open(path).resize((400, 600))


def recommend_from_name(movie, adult):
    movie_index = movies[movies['title'] == movie].index[0]
    print(movie_index)
    distances = similarity[movie_index]
    movies_list = [
        x for x in distances if adult or not movies.iloc[x[0]].adult][1:26]
    sorted_list = [x[0] for x in movies_list]
    return sorted_list


def recommend_from_mood(genre, adult):
    sorted_list = sorted([x for x in range(len(list(movies['genres']))) if genre in movies.iloc[x].genres and (
        adult or not movies.iloc[x].adult)], key=lambda x: movies.iloc[x].imdb_rating, reverse=True)[0:25]
    return sorted_list


def recommend_from_details(details):
    sorted_list = []
    for i in movies.index:
        take = True
        if(not movies['genres'][i] or not movies['actors'][i] or not movies['directors'][i] or not movies['writers'][i]):
            take = False
        if not all(genre in movies['genres'][i] for genre in details['genres']):
            take = False
        if float(movies['year_of_release'][i]) < details['release_year'][0] or float(movies['year_of_release'][i]) > details['release_year'][1]:
            take = False
        if movies['imdb_rating'][i] < details['rating'][0] or movies['imdb_rating'][i] > details['rating'][1]:
            take = False

        if float(movies['runtime'][i]) < details['runtime'][0] or float(movies['runtime'][i]) > details['runtime'][1]:
            take = False
        # if not all(production_company in movies['production_companies'][i] for production_company in details['production_companies']):
        #     take = False
        # if movies['release_date'][i] < details['release_date']:
        #     take = False
        if not all(cast in movies['actors'][i] for cast in details['cast']):
            take = False
        if not all(director in movies['directors'][i] for director in details['director']):
            take = False
        if not all(writers in movies['writers'][i] for writers in details['writers']):
            take = False
        if(take):
            sorted_list.append(i)
    sorted_list = sorted([x for x in sorted_list],
                         key=lambda x: movies.iloc[x].imdb_rating, reverse=True)
    if(len(sorted_list) > 25):
        sorted_list = sorted_list[0:25]
    return sorted_list


def display_poster(index_list):
    for i in range(0, len(index_list), 5):
        with st.container():
            cols = st.columns(5)
            for j in range(0, 5):
                if(i+j < len(index_list)):
                    with cols[j]:
                        st.image(fetch_poster(
                            index_list[i+j]), caption=movies.iloc[index_list[i+j]].title)


similarity = pickle.load(open('similarity_2.pkl', 'rb'))
movies_dict = pickle.load(open('movies.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
st.title('Movie Recommender system')
strategy = st.subheader('Recommend according to:')
tab1, tab2, tab3 = st.tabs(["Movie name", "Mood", "Movie Details"])
with tab1:
    selected_movie_name = st.selectbox('Enter movie name',
                                       movies['title'].values.tolist())
    adult = False
    if(st.radio('Are you an adult?', ['Yes', 'No'], key=1) == 'Yes'):
        adult = True
    if st.button('Recommend', key=2):
        index_list = recommend_from_name(selected_movie_name, adult)
        display_poster(index_list)

with tab2:
    selected_mood = st.selectbox('How\'s your mood?', list(
        mood_dict.keys()), label_visibility='collapsed')
    genre = mood_dict[selected_mood]
    adult = False
    if(st.radio('Are you an adult?', ['Yes', 'No'], key=3) == 'Yes'):
        adult = True
    if st.button('Recommend', key=4):
        index_list = recommend_from_mood(genre, adult)
        display_poster(index_list)

with tab3:
    details = {}
    selected_movie_genre = st.multiselect(
        'Enter movie genre', generate_set('genres'))
    details['genres'] = selected_movie_genre
    # min_revenue = st.number_input(
    #     'Enter the minimum revenue(in $)', key=7, min_value=0)
    # details['revenue'] = min_revenue
    # production_company = st.multiselect(
    #     'Enter production company name', generate_set('production_companies'))
    # details['production_companies'] = production_company
    col1, col2 = st.columns(2)
    with col1:
        start_release_year = st.number_input(
            'Enter the minimum release year', key=8, min_value=1950, max_value=2019, value=1950)
    with col2:
        end_release_year = st.number_input(
            'Enter the maximum release year', key=9, min_value=1950, max_value=2019, value=2019)
    details['release_year'] = (start_release_year, end_release_year)
    with col1:
        start_rating = st.number_input(
            'Enter the minimum rating', key=10, min_value=0.0, max_value=10.0, value=0.0, step=0.1)
    with col2:
        end_rating = st.number_input(
            'Enter the maximum rating', key=11, min_value=0.0, max_value=10.0, value=10.0, step=0.1)
    details['rating'] = (start_rating, end_rating)
    with col1:
        start_runtime = st.number_input(
            'Enter the minimum runtime', key=12, min_value=0, max_value=330, value=0, step=15)
    with col2:
        end_runtime = st.number_input(
            'Enter the maximum runtime', key=13, min_value=0, max_value=330, value=330, step=15)
    details['runtime'] = (start_runtime, end_runtime)
    cast = st.multiselect(
        'Enter movie cast', generate_set('actors'))
    if(cast != ''):
        details['cast'] = cast
    director = st.selectbox(
        'Enter movie director\'s name', ['Choose an option']+generate_set('directors'))
    if(director == 'Choose an option'):
        details['director'] = []
    else:
        details['director'] = list(director)
    writers = st.multiselect(
        'Enter movie writers\' name', generate_set('writers'))
    details['writers'] = writers
    if st.button('Recommend', key=5):
        index_list = recommend_from_details(details)
        if(len(index_list)):
            display_poster(index_list)
        else:
            st.text("No results match your search")
