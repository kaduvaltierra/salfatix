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

def where_to_watch(search_term: str, user: User):
    api_key_tmdb = os.environ.get("API_TMDB_TOKEN")
    url_movie = "https://api.themoviedb.org/3/search/movie?query="+search_term+"&include_adult=false&language=es-CL&page=1&region=Chile"

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer "+api_key_tmdb
    }

    response_movie = requests.get(url_movie, headers=headers)
    data_movie = response_movie.json()
    id = data_movie['results'][0]['id']
    url_watch_provider = "https://api.themoviedb.org/3/movie/"+str(id)+"/watch/providers"

    response_watch_providers = requests.get(url_watch_provider, headers=headers)
    data_providers = response_watch_providers.json()
    providers = [d['provider_name'] for d in data_providers['results']['CL']['flatrate']]
    # movie_or_tv_show = search_platforms(search_term)

    # if not movie_or_tv_show:
    #     return f'No estoy seguro de dónde puedes ver esta película o serie :(, pero quizas puedes revisar en JustWatch: https://www.justwatch.com/cl/buscar?q={search_term}'
    string_providers = ', '.join(providers)
    print(string_providers)

    return f'Puedes ver {search_term} en las siguientes plataformas: {string_providers}'

    # system_prompt = build_prompt(user, string_providers) #ID 273481

    # messages_for_llm = [{"role": "system", "content": system_prompt}]

    # for message in user.messages:
    #     messages_for_llm.append({
    #         "role": message.author,
    #         "content": message.content,
    #     })

    # chat_completion = client.chat.completions.create(
    #     messages=messages_for_llm,
    #     model="gpt-4o",
    #     temperature=1,
    # )

    # return chat_completion.choices[0].message.content


#def search_movie_or_tv_show(client: OpenAI, search_term: str, user: User):
    # movie_or_tv_show = search(search_term)

    # if movie_or_tv_show:
    #     system_prompt = build_prompt(user, str(movie_or_tv_show))
    # else:
    #     system_prompt = build_prompt(user, '')

    # messages_for_llm = [{"role": "system", "content": system_prompt}]

    # for message in user.messages:
    #     messages_for_llm.append({
    #         "role": message.author,
    #         "content": message.content,
    #     })

    # chat_completion = client.chat.completions.create(
    #     messages=messages_for_llm,
    #     model="gpt-4o",
    #     temperature=1,
    # )

    # return chat_completion.choices[0].message.content