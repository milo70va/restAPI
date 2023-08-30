# Importa las librerías y módulos necesarios
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow.fields import String
from marshmallow import ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from flask_cors import CORS
import os

# Crea una instancia de la aplicación Flask
app = Flask(__name__)

# Configura la URL de la base de datos SQLite en el directorio actual
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

# Crea una instancia de la base de datos SQLAlchemy y de Marshmallow
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Configura CORS para permitir solicitudes desde cualquier origen
CORS(app)

# Define la clase de la entidad "Persona" en la base de datos
class Persona(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)  # Columna de nombre
    delito = db.Column(db.String(250), nullable=False)  # Columna de delito

# Define el esquema de Marshmallow para la clase "Persona"
class PersonaSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Persona

    id = ma.auto_field(dump_only=True)  # Campo de ID
    nombre = String(required=True, validate=lambda value: len(value) >= 3)  # Campo de nombre con validación
    delito = String(required=True, validate=lambda value: len(value) >= 10)  # Campo de delito con validación

# Define una ruta para obtener todas las personas
@app.route('/personas', methods=['GET'])
def get_personas():
    # Consulta todas las personas de la base de datos
    personas = Persona.query.all()
    # Crea una instancia del esquema de Marshmallow para varias personas
    personas_schema = PersonaSchema(many=True)
    # Devuelve la lista de personas en formato JSON
    return jsonify(personas_schema.dump(personas))

# Define una ruta para obtener una persona por su ID
@app.route('/personas/<int:id>', methods=['GET'])
def get_persona(id):
    # Consulta una persona por su ID en la base de datos
    persona = Persona.query.get(id)
    if persona:
        # Crea una instancia del esquema de Marshmallow para una persona
        persona_schema = PersonaSchema()
        # Devuelve los detalles de la persona en formato JSON
        return jsonify(persona_schema.dump(persona))
    # Si no se encuentra la persona, devuelve un mensaje de error y código 404
    return jsonify({"mensaje": "Persona no encontrada"}), 404

# Define una ruta para agregar una nueva persona
@app.route('/personas', methods=['POST'])
def add_persona():
    try:
        # Crea una instancia del esquema de Marshmallow para validar la solicitud JSON
        persona_schema = PersonaSchema()
        # Carga los datos de la solicitud JSON en una instancia de la clase Persona
        persona = persona_schema.load(request.json)
        # Agrega la persona a la sesión de la base de datos y la guarda
        db.session.add(persona)
        db.session.commit()
        # Devuelve un mensaje de éxito y código 201
        return jsonify({"mensaje": "Persona agregada exitosamente"}), 201
    except ValidationError as error:
        # Si hay errores de validación, devuelve los mensajes de error y código 400
        return jsonify(error.messages), 400

# Define una ruta para actualizar los datos de una persona
@app.route('/personas/<int:id>', methods=['PUT'])
def update_persona(id):
    persona = Persona.query.get(id)
    if not persona:
        # Si la persona no se encuentra, devuelve un mensaje de error y código 404
        return jsonify({"mensaje": "Persona no encontrada"}), 404

    try:
        persona_schema = PersonaSchema()
        # Carga los datos de la solicitud JSON en una instancia de la clase Persona existente
        updated_persona = persona_schema.load(request.json, instance=persona, partial=True)
        # Actualiza los atributos de la persona con los valores del objeto updated_persona
        persona.nombre = updated_persona.nombre
        persona.delito = updated_persona.delito
        # Guarda los cambios en la base de datos
        db.session.commit()
        # Devuelve un mensaje de éxito
        return jsonify({"mensaje": "Persona actualizada exitosamente"})
    except ValidationError as error:
        # Si hay errores de validación, devuelve los mensajes de error y código 400
        return jsonify(error.messages), 400

# Define una ruta para eliminar una persona por su ID
@app.route('/personas/<int:id>', methods=['DELETE'])
def delete_persona(id):
    persona = Persona.query.get(id)
    if not persona:
        # Si la persona no se encuentra, devuelve un mensaje de error y código 404
        return jsonify({"mensaje": "Persona no encontrada"}), 404

    # Elimina la persona de la base de datos y guarda los cambios
    db.session.delete(persona)
    db.session.commit()
    # Devuelve un mensaje de éxito
    return jsonify({"mensaje": "Persona eliminada exitosamente"})

# Crea las tablas en el contexto de la aplicación Flask
with app.app_context():
    db.create_all()

# Ejecuta la aplicación Flask en modo de depuración
if __name__ == '__main__':
    app.run(debug=True)
