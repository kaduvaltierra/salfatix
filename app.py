from flask import Flask, render_template, request,redirect,url_for,flash
from flask_bootstrap import Bootstrap5
from openai import OpenAI
from dotenv import load_dotenv
from db import db, db_config
from models import User, Message

load_dotenv()
 
client = OpenAI()
app = Flask(__name__)
bootstrap = Bootstrap5(app)
db_config(app)

@app.route('/')
def index():
    # Obtengo nombre del usuario desde la BDatos, class USER
    user = db.session.query(User).first()
  
    return render_template('landing.html',nombre_usuario = user.nombre_usuario)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    user = db.session.query(User).first()

    if request.method == 'GET':
        return render_template('chat.html', messages=user.messages)

    intent = request.form.get('intent')

    intents = {
        'Terror': 'Recomiéndame una película de terror',
        'Comedia': 'Recomiéndame una película de comedia',
        'Accion': 'Recomiéndame una película de acción',
        'Infantil': 'Recomiéndame una película infantil',
        'Romantica': 'Recomiéndame una película romántica',
        'Enviar': request.form.get('message')
    }

    if intent in intents:
        user_message = intents[intent]

        # Guardar nuevo mensaje en la BD
        db.session.add(Message(content=user_message, author="user", user=user))
        db.session.commit()

        messages_for_llm = [{
            "role": "system",
            "content": "Eres un chatbot que recomienda películas, te llamas 'Salfatix'. Tu rol es responder recomendaciones de manera breve y concisa. No repitas recomendaciones.",
        }]

        for message in user.messages:
            messages_for_llm.append({
                "role": message.author,
                "content": message.content,
            })

        chat_completion = client.chat.completions.create(
            messages=messages_for_llm,
            model="gpt-4o",
            temperature=1
        )

        model_recommendation = chat_completion.choices[0].message.content
        db.session.add(Message(content=model_recommendation, author="assistant", user=user))
        db.session.commit()

        return render_template('chat.html', messages=user.messages)

@app.route('/user/<int:id>', methods=['GET', 'POST'])
def user(id, status=None):
    # Manejo del método POST para actualizar datos
    if request.method == 'POST':
        # Busca al usuario en la base de datos por su ID
        user = db.session.query(User).filter_by(id=id).first()

        # Manejo de errores: Si no se encuentra el usuario
        if not user:
            return "Usuario no encontrado", 404

        # Actualiza los campos del usuario con los valores enviados desde el formulario
        user.nombre_usuario = request.form.get('nombre_usuario')
        user.email = request.form.get('email')
        user.pelicula_favorita = request.form.get('pelicula_favorita')
        user.genero_favorito = request.form.get('genero_favorito')

        # Guarda los cambios en la base de datos
        db.session.commit()

        # Redirige con un estado de éxito
        return redirect(url_for('user', id=id, status='success'))

    # Método GET: Mostrar el perfil
    user = db.session.query(User).filter_by(id=id).first()
    if not user:
        return "Usuario no encontrado", 404

    # Leer el estado desde la URL
    status = request.args.get('status', '')

    # Renderiza la plantilla con los datos del usuario y el estado
    return render_template('user.html', user=user, status=status)

@app.route('/update_user', methods=['POST'])
def update_user():
    # Obtener el ID del usuario desde el formulario
    user_id = request.form.get('id')

    # Buscar al usuario en la base de datos por su ID
    user = db.session.query(User).filter_by(id=user_id).first()

    # Manejo de errores: Si no se encuentra el usuario
    if not user:
        return "Usuario no encontrado", 404

    # Actualizar los campos del usuario con los valores enviados desde el formulario
    user.nombre_usuario = request.form.get('nombre_usuario')
    user.email = request.form.get('email')
    user.pelicula_favorita = request.form.get('pelicula_favorita')
    user.genero_favorito = request.form.get('genero_favorito')

    # Guardar los cambios en la base de datos
    db.session.commit()

    # Redirigir a la página del perfil del usuario con un mensaje de éxito
    flash("Datos actualizados correctamente.", "success")
    return redirect(url_for('user', id=user.id))