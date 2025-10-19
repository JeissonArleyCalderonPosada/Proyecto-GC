from flask import Flask, render_template
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
 
app = Flask(__name__)

##CONFIGURACION BASE DE DATOS
app.config['SQLALCHEMY_DATABASE_URI'] = (
    "mssql+pyodbc://DESKTOP-PTOBCHL\\SQLEXPRESS/ml_project_aulaespejo?"
    "driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

##CLASE USUARIOS CON SUS ATRIBUTOS 
class Usuario(db.Model):
    __tablename__ = 'Usuarios'  

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    correo = db.Column(db.String(120), unique=True)

    def __repr__(self):
        return f'<Usuario {self.nombre}>'

@app.route('/')
def home():
    return "¡Hola, Flask está funcionando!"
 
if __name__ == '__main__':
    app.run(debug=True)

# Ruta principal (Index)
@app.route('/')
def index():
    return render_template('index.html', name='Flask Marketing App')

# Ruta para el login
@app.route('/login')
def login():
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)