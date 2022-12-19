import streamlit as st
import pickle
import pandas as pd
import requests
import numpy as np
from PIL import Image
import re
import tomli
st.set_page_config(page_title='Movie Recommendation System', layout='wide')
mood_dict = {'Happy': 'Horror', 'Sad': 'Drama', 'Satisfied': 'Animation', 'Angry': 'Romance', 'Peaceful': 'Fantasy',
             'Fearful': 'Adventure', 'Excited': 'Crime', 'Depressed': 'Comedy', 'Content': 'Mystery', 'Sorrowful': 'Action'}


def generate_set(attribute):
    Set = set()
    for x in [movies.iloc[x] for x in range(len(list(movies[attribute])))]:
        for y in x.get(attribute):
            Set.add(y)
    return list(Set)


def fetch_poster(movie_id):
    response = requests.get(
        'https://api.themoviedb.org/3/movie/{}?api_key=77eafb7a2d8d0876433444356f90b9d7&language=en-US'.format(movie_id))
    data = response.json()
    if(data.get('poster_path') == None):
        return Image.open('poster.png')
    return "https://image.tmdb.org/t/p/original/"+data['poster_path']


def recommend_from_name(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)),
                         reverse=True, key=lambda x: x[1])[1:26]
    recommended_movies = []
    recommended_movies_posters = []
    for i in movies_list:
        movie_id = movies.iloc[i[0]].id
        recommended_movies.append(movies.iloc[i[0]].title)
        # fetch poster from api
        recommended_movies_posters.append(fetch_poster(movie_id))
    return recommended_movies, recommended_movies_posters


def recommend_from_mood(genre):
    recommended_movies = []
    recommended_movies_posters = []
    sorted_list = sorted([movies.iloc[x] for x in range(len(list(movies['genres']))) if genre in movies['genres']
                         [x]], key=lambda x: x.revenue, reverse=True)[0:25]
    for movie in sorted_list:
        recommended_movies.append(movie.title)
        recommended_movies_posters.append(fetch_poster(movie.id))
    return recommended_movies, recommended_movies_posters

# todo


def recommend_from_details(details):
    recommended_movies = []
    recommended_movies_posters = []
    for i in movies.index:
        if(len(recommended_movies) == 25):
            break
        take = True
        if not all(genre in movies['genres'][i] for genre in details['genres']):
            take = False
        if movies['revenue'][i] < details['revenue']:
            take = False
        if not all(production_company in movies['production_companies'][i] for production_company in details['production_companies']):
            take = False
        if movies['release_date'][i] < details['release_date']:
            take = False
        if not all(cast in movies['cast'][i] for cast in details['cast']):
            take = False
        for job in details['crew']:
            if movies['crew'][i].get(job) == None or not all(crew in movies['crew'][i][job] for crew in details['crew'][job]):
                take = False
                break
        if(take):
            movie_id = movies.iloc[i].id
            recommended_movies.append(movies.iloc[i].title)
            # fetch poster from api
            recommended_movies_posters.append(fetch_poster(movie_id))
    return recommended_movies, recommended_movies_posters


def display_poster(names, posters):
    for i in range(0, len(names), 5):
        with st.container():
            cols = st.columns(5)
            for j in range(0, 5):
                if(i+j < len(names)):
                    with cols[j]:
                        st.text(names[i+j])
                        st.image(posters[i+j])


similarity = pickle.load(open('similarity.pkl', 'rb'))
movies_dict = pickle.load(open('movies.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
st.title('Movie Recommender system')
strategy = st.subheader('Recommend according to:')
tab1, tab2, tab3 = st.tabs(["Mood", "Movie name", "Movie Details"])
with tab1:
    selected_mood = st.selectbox('How\'s your mood?', list(
        mood_dict.keys()), label_visibility='collapsed')
    genre = mood_dict[selected_mood]
    recommend_from_mood(genre)
    if st.button('Recommend', key=1):
        names, posters = recommend_from_mood(genre)
        display_poster(names, posters)

with tab2:
    selected_movie_name = st.selectbox('Enter movie name',
                                       ['Enter movie name']+movies['title'].values.tolist(), label_visibility='collapsed')
    if st.button('Recommend', key=2):
        names, posters = recommend_from_name(selected_movie_name)
        display_poster(names, posters)

with tab3:
    details = {}
    selected_movie_genre = st.multiselect(
        'Enter movie genre', generate_set('genres'))
    details['genres'] = selected_movie_genre
    min_revenue = st.number_input(
        'Enter the minimum revenue(in $)', min_value=0)
    details['revenue'] = min_revenue
    production_company = st.multiselect(
        'Enter production company name', generate_set('production_companies'))
    details['production_companies'] = production_company
    release_year = st.number_input(
        'Enter the minimum release year', min_value=1900)
    details['release_date'] = str(release_year)+'-01-01'
    cast = st.multiselect(
        'Enter movie cast', generate_set('cast'))
    if(cast != ''):
        details['cast'] = cast
    crew = re.split(r'\s*\n\s*', st.text_area('Crew').lower().replace(" ", ""))
    crew_dict = {}
    for i in crew:
        pair = re.split('\s*:\s*', i)
        if(len(pair) <= 1):
            continue
        if(crew_dict.get(pair[0]) == None):
            crew_dict[pair[0]] = re.split('\s*,\s*', pair[1])
        else:
            crew_dict[pair[0]] = crew_dict[pair[0]] + \
                re.split('\s*,\s*', pair[1])
    details['crew'] = crew_dict
# print(crew_dict)
    if st.button('Recommend', key=3):
        names, posters = recommend_from_details(details)
        display_poster(names, posters)
