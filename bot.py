import requests
import os
from openai import OpenAI
from models import User

def build_prompt(user: User, context: str):
    system_prompt = '''Eres un chatbot que recomienda películas, te llamas 'Salfatix'.
    - Tu rol es responder recomendaciones de manera breve y concisa.
    - No repitas recomendaciones.
    '''

    # Incluir preferencias del usuario
    if user.genero_favorito:
        system_prompt += f'- El género favorito del usuario es: {user.genero_favorito}.\n'
    if user.pelicula_favorita:
        system_prompt += f'- La película favorita del usuario es: {user.pelicula_favorita}.\n'

    if context:
        system_prompt += f'Además considera el siguiente contenido: {context}\n'

    return system_prompt

def where_to_watch(search_term: str, medita_type: str):
    api_key_tmdb = os.environ.get("API_TMDB_TOKEN")    
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer "+api_key_tmdb
    }

    if medita_type == 'movie':
        print(medita_type)
        url_movie = "https://api.themoviedb.org/3/search/movie?query="+search_term+"&include_adult=false&language=es-CL&page=1&region=Chile"
        try:
            response_movie = requests.get(url_movie, headers=headers)
            data_movie = response_movie.json()        
        except:
            return f'No pude encontrar {search_term} en mi base de datos de películas 😞. Tal vez puedes intentar revisando en TMDB: https://www.themoviedb.org/search?language=es&query={search_term}'
        
        if not data_movie['results']:
            return f'No pude encontrar {search_term} en mi base de datos de películas 😞. Tal vez puedes intentar revisando en TMDB: https://www.themoviedb.org/search?language=es&query={search_term}'
            
        id = data_movie['results'][0]['id']
        name = data_movie['results'][0]['original_title']
        overview = data_movie['results'][0]['overview']
        vote_average = data_movie['results'][0]['vote_average']

        url_watch_provider = "https://api.themoviedb.org/3/movie/"+str(id)+"/watch/providers"    
        try:
            response_watch_providers = requests.get(url_watch_provider, headers=headers)
            data_providers = response_watch_providers.json()
        except:
            return f'No pude encontrar la película {search_term} en mi base de datos de proveedores 😞.'

        if not data_providers['results']:
            return f'No pude encontrar la película {search_term} en mi base de datos de proveedores 😞.'
        
        providers = [d['provider_name'] for d in data_providers['results']['CL']['flatrate']]
        string_providers = ', '.join(providers)
        print(string_providers)

        return f'Puedes ver la película {name} en las siguientes plataformas: {string_providers}.<br/>🍿🎬{overview}<br/>Puntuación: {vote_average}/10'
    else:
        print(medita_type)    
        url_tvserie = "https://api.themoviedb.org/3/search/tv?query="+search_term+"&include_adult=false&language=es-CL&page=1"
        try:
            response_tvserie = requests.get(url_tvserie, headers=headers)
            data_tvserie = response_tvserie.json()        
        except:
            return f'No pude encontrar {search_term} en mi base de datos de series 😞. Tal vez puedes intentar revisando en TMDB: https://www.themoviedb.org/search?language=es&query={search_term}'
        
        if not data_tvserie['results']:
            return f'No pude encontrar {search_term} en mi base de datos de series 😞. Tal vez puedes intentar revisando en TMDB: https://www.themoviedb.org/search?language=es&query={search_term}'
            
        id = data_tvserie['results'][0]['id']    

        url_watch_provider = "https://api.themoviedb.org/3/tv/"+str(id)+"/watch/providers"    
        try:
            response_watch_providers = requests.get(url_watch_provider, headers=headers)
            data_providers = response_watch_providers.json()
        except:
            return f'No pude encontrar la serie {search_term} en mi base de datos de proveedores 😞.'

        if not data_providers['results']:
            return f'No pude encontrar la serie {search_term} en mi base de datos de proveedores 😞.'
        
        providers = [d['provider_name'] for d in data_providers['results']['CL']['flatrate']]
        string_providers = ', '.join(providers)
        print(string_providers)

        return string_providers #f'Puedes ver la serie {name} en las siguientes plataformas: {string_providers}.<br/>🍿🎬{overview}<br/>Puntuación: {vote_average}/10'

def search_movie_or_tv_show(search_term: str, user: User, client: OpenAI):
    api_key_tmdb = os.environ.get("API_TMDB_TOKEN")    
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer "+api_key_tmdb
    }

    print(search_term)
    url_multi = "https://api.themoviedb.org/3/search/multi?query="+search_term+"&include_adult=false&language=es-CL&page=1&region=Chile"
    try:
        response_multi = requests.get(url_multi, headers=headers)
        data_multi = response_multi.json()        
    except:
        return f'No pude encontrar {search_term} en mi base de datos de películas/series 😞. Tal vez puedes intentar revisando en TMDB: https://www.themoviedb.org/search?language=es&query={search_term}'
    
    if not data_multi['results']:
        return f'No pude encontrar {search_term} en mi base de datos de películas/series 😞. Tal vez puedes intentar revisando en TMDB: https://www.themoviedb.org/search?language=es&query={search_term}'
    
    media_type = data_multi['results'][0]['media_type']
    if media_type == 'movie':
        name = data_multi['results'][0]['original_title']
    else:
        name = data_multi['results'][0]['original_name']

    overview = data_multi['results'][0]['overview']
    vote_average = data_multi['results'][0]['vote_average']
    
    poster_path = data_multi['results'][0]['poster_path']

    system_prompt = build_prompt(user, f'''
    La información que tengo y debes utilizar para entregar una respuesta son:
    - Nombre: {name}
    - Descripción: {overview}
    - Puntuación: {vote_average}/10
    - URL Imagen Poster: https://image.tmdb.org/t/p/w500{poster_path}    
    - Tipo de contenido: {media_type}
    ''')
    
    messages_for_llm = [{"role": "system", "content": system_prompt}]

    for message in user.messages:
        messages_for_llm.append({
            "role": message.author,
            "content": message.content,
        })

    chat_completion = client.chat.completions.create(
        messages=messages_for_llm,
        model="gpt-4o",
        temperature=1,
    )

    return chat_completion.choices[0].message.content