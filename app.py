import json
from flask import Flask, render_template, request,redirect,url_for,flash,jsonify
from flask_bootstrap import Bootstrap5
from openai import OpenAI
from dotenv import load_dotenv
from db import db, db_config
from os import getenv
from bot import where_to_watch, search_movie_or_tv_show, search_video_movie
from models import User, Message
from forms import ProfileForm, SignUpForm, LoginForm
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from flask_bcrypt import Bcrypt

load_dotenv()
 
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Inicia sesión para continuar'
client = OpenAI()
app = Flask(__name__)
app.secret_key = getenv("KEY_SALFATIX")
bootstrap = Bootstrap5(app)
csrf = CSRFProtect(app)
login_manager.init_app(app)
bcrypt = Bcrypt(app)
db_config(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

tools = [
    {
        'type': 'function',
        'function': {
            "name": "where_to_watch",
            "description": "Returns a list of platforms where a specified movie can be watched.",
            "parameters": {
                "type": "object",
                "required": [
                    "name",
                    "media_type"
                ],
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the movie or tv serie to search for"
                    },
                    "media_type": {
                        "type": "string",
                        "description": "The type of media(movie or tv serie) to search for"
                    }
                },
                "additionalProperties": False
            }
        },
    },
    {
        'type': 'function',
        'function': {
            "name": "search_movie_or_tv_show",
            "description": "Returns information about a specified movie or TV show.",
            "parameters": {
                "type": "object",
                "required": [
                    "name"
                ],
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the movie/tv show to search for"
                    }
                },
                "additionalProperties": False
            }
        },
    },
    {
        'type': 'function',
        'function': {
            "name": "search_video_movie",
            "description": "Returns video about a specified movie.",
            "parameters": {
                "type": "object",
                "required": [
                    "name"
                ],
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the movie to search for"
                    }
                },
                "additionalProperties": False
            }
        },
    }
]

@app.route('/')
def index():  
    return render_template('landing.html')

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    user = db.session.query(User).get(current_user.id)

    if request.method == 'GET':
        return render_template('chat.html', messages=user.messages)
    
    user_message = request.form.get('message')
    print(user_message)
    # Guardar nuevo mensaje en la BD
    db.session.add(Message(content=user_message, author="user", user=user))
    db.session.commit()

    # Crear prompt para el modelo
    system_prompt = '''Eres un chatbot que recomienda películas, te llamas 'Salfatix'.
    - Tu rol es responder recomendaciones de manera breve y concisa.
    - No repitas recomendaciones.
    - Tienes la capacidad de recomendar películas y series de televisión.
    - Puedes recuperar videos de YouTube sobre películas.
    '''

        # Incluir preferencias del usuario
    if user.genero_favorito:
        system_prompt += f'- El género favorito del usuario es: {user.genero_favorito}.\n'
    if user.pelicula_favorita:
        system_prompt += f'- La película favorita del usuario es: {user.pelicula_favorita}.\n'

    print(system_prompt)
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
        tools=tools,
    )

    model_recommendation = ''
    if chat_completion.choices[0].message.tool_calls:        
        if(len(chat_completion.choices[0].message.tool_calls) > 1):
            tool_calls = chat_completion.choices[0].message.tool_calls
            tool_call_smotv = [tool_call for tool_call in tool_calls if tool_call.function.name == 'search_movie_or_tv_show']
            tool_call_wtw = [tool_call for tool_call in tool_calls if tool_call.function.name == 'where_to_watch']
            tool_call_svm = [tool_call for tool_call in tool_calls if tool_call.function.name == 'search_video_movie']

            if(tool_call_wtw and tool_call_smotv):
                print('Primero ejecuto where_to_watch')
                arguments_wtw = json.loads(tool_call_wtw[0].function.arguments)
                name = arguments_wtw['name']
                medita_type = arguments_wtw['media_type']
                response_wtw = where_to_watch(name, medita_type, 'small')
                
                print('Segundo ejecuto search_movie_or_tv_show')
                arguments_smotv = json.loads(tool_call_smotv[0].function.arguments)
                name = arguments_smotv['name']
                model_recommendation = search_movie_or_tv_show(name, user, client, response_wtw)                

            elif(tool_call_svm and tool_call_smotv):                
                print('Solo ejecuto search_video_movie [smotv]')
                arguments_svm = json.loads(tool_call_svm[0].function.arguments)
                name = arguments_svm['name']
                model_recommendation = search_video_movie(name)

            else:
                print('Primero ejecuto where_to_watch')
                arguments_wtw = json.loads(tool_call_wtw[0].function.arguments)
                name = arguments_wtw['name']
                medita_type = arguments_wtw['media_type']
                response_wtw = where_to_watch(name, medita_type, 'small')

                print('Segundo ejecuto search_video_movie [wtw]')
                arguments_svm = json.loads(tool_call_svm[0].function.arguments)
                name = arguments_svm['name']
                model_recommendation = search_video_movie(name, response_wtw)

            db.session.add(Message(content=model_recommendation, author="assistant", user=user))
            db.session.commit()           

        else:
            tool_call = chat_completion.choices[0].message.tool_calls[0]
            print(tool_call.function.name)
            if tool_call.function.name == 'where_to_watch':                
                arguments = json.loads(tool_call.function.arguments)
                name = arguments['name']
                medita_type = arguments['media_type']
                model_recommendation = where_to_watch(name, medita_type, 'full')                                

            if tool_call.function.name == 'search_movie_or_tv_show':
                arguments = json.loads(tool_call.function.arguments)
                name = arguments['name']
                model_recommendation = search_movie_or_tv_show(name, user, client)

            if tool_call.function.name == 'search_video_movie':
                arguments = json.loads(tool_call.function.arguments)
                name = arguments['name']
                model_recommendation = search_video_movie(name)

            db.session.add(Message(content=model_recommendation, author="assistant", user=user))
            db.session.commit()

    else:
        model_recommendation = chat_completion.choices[0].message.content    
        db.session.add(Message(content=model_recommendation, author="assistant", user=user))
        db.session.commit()

    accept_header = request.headers.get('Accept')
    if accept_header and 'application/json' in accept_header:
        last_message = user.messages[-1]
        return jsonify({
            'author': last_message.author,
            'content': last_message.content,
        })

    return render_template('chat.html', messages=user.messages)

@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    form = SignUpForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            nombre_usuario = form.nombre_usuario.data
            email = form.email.data
            password = form.password.data
            user = User(email=email, password_hash=bcrypt.generate_password_hash(password).decode('utf-8'), nombre_usuario=nombre_usuario)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('chat'))
    return render_template('sign-up.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data
            user = db.session.query(User).filter_by(email=email).first()
            if user and bcrypt.check_password_hash(user.password_hash, password):
                login_user(user)
                return redirect('chat')

            flash("El correo o la contraseña es incorrecta.", "error")

    return render_template('log-in.html', form=form)

@app.route('/user', methods=['GET', 'POST'])
@login_required
def user():
    user = db.session.query(User).get(current_user.id)
    # Manejo del método POST para actualizar datos
    if request.method == 'POST':
        form = ProfileForm()
        if form.validate_on_submit():
            user.nombre_usuario = form.nombre_usuario.data
            user.pelicula_favorita = form.pelicula_favorita.data
            user.genero_favorito = form.genero_favorito.data
            db.session.commit()
            flash('Datos actualizados correctamente.', 'message')
        else:
            flash('Error al actualizar los datos.', 'error')
    else:
        form = ProfileForm(obj=user)
    
    return render_template('user.html', form=form)

@app.get('/logout')
def logout():
    logout_user()
    return redirect('/')