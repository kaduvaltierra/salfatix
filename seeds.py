from db import db
from app import app
from models import User, Message

with app.app_context():
    db.create_all()

    # inserto en la tabla los datos del Usuario y sus datos de perfil
    user = User(    email="test@email.org",nombre_usuario="César", pelicula_favorita = "Star War", genero_favorito = "Acción")

    #inserto en la tabla el primer dato del historial de mensajaes
    message_content = f"Hola !! Soy Salfatix, un recomendador de películas. ¿En qué te puedo ayudar?"
 
    message = Message(content=message_content, author="assistant", user=user)

    db.session.add(user)
    db.session.add(message)
    db.session.commit()

    print("Usuario y Mensaje creado!")