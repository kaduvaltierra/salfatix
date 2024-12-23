from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/bye')
def bye():
    return "Goodbye!"

@app.route('/iniciar-sesion')
def login():
    return "Iniciar sesión"

@app.route('/users/<username>')
def users(username):
    return "Perfil de usuario: " + username