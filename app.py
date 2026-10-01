# ==========================================
# IMPORTACIÓN DE LIBRERÍAS
# ==========================================

from flask import Flask, jsonify, request
# Flask: crea el servidor backend
# jsonify: convierte respuestas a formato JSON
# request: permite recibir datos del cliente (POST, PUT)

from flask_cors import CORS
# Permite que el frontend (otro puerto) pueda consumir esta API

import pymysql
# Librería para conectarse a MySQL

import bcrypt
# Librería para encriptar contraseñas

from flasgger import Swagger
# Genera documentación automática tipo Swagger UI


# ==========================================
# INICIALIZACIÓN DE LA APP
# ==========================================

app = Flask(__name__)
# Se crea la aplicación Flask

CORS(app)
# Se habilita CORS en toda la app

swagger = Swagger(app)
# Activa Swagger en la ruta /apidocs


# ==========================================
# CONEXIÓN A LA BASE DE DATOS
# ==========================================

def conectar(vhost, vuser, vpass, vdb):
    # Función que crea una conexión a MySQL con los datos enviados

    conn = pymysql.connect(
        host=vhost,        # Dirección del servidor (localhost)
        user=vuser,        # Usuario de MySQL
        passwd=vpass,      # Contraseña de MySQL
        db=vdb,            # Base de datos a usar
        charset='utf8mb4'  # Codificación (soporta emojis y caracteres especiales)
    )

    return conn
    # Retorna la conexión abierta


# ==========================================
# RUTA: CONSULTA GENERAL (GET)
# ==========================================

@app.route("/", methods=['GET'])
# Define endpoint GET: /
def consulta_general():
    """
    Consulta general del baúl de contraseñas
    ---
    responses:
      200:
        description: Lista de registros
    """
    try:
         # Se conecta a la BD
       
       
        conn = conectar('localhost', 'root', '1234', 'gestor_contrasena')
        # Se conecta a la base de datos

        cur = conn.cursor()
        # Crea un cursor para ejecutar consultas SQL

        cur.execute("SELECT * FROM baul")
        # Ejecuta la consulta para traer todos los registros

        datos = cur.fetchall()
        # Obtiene todos los resultados de la consulta

        data = []
        # Lista vacía que almacenará los registros como diccionarios

        for row in datos:
            # Itera sobre cada fila del resultado
            dato = {
                'id_baul': row[0],      # Columna 0 → ID del registro
                'plataforma': row[1],   # Columna 1 → Nombre de la plataforma
                'usuario': row[2],      # Columna 2 → Nombre de usuario o correo
                'clave': row[3]         # Columna 3 → Contraseña (almacenada encriptada)
            }
            data.append(dato)
            # Agrega el diccionario del registro a la lista

        cur.close()
        # Cierra el cursor para liberar recursos

        conn.close()
        # Cierra la conexión a la base de datos

        return jsonify({'baul': data, 'mensaje': 'Baul de contrasenas'})
        # Retorna los datos en formato JSON

    except Exception as ex:
        print(ex)
        # Imprime el error en consola para depuración
        return jsonify({'mensaje': 'Error'})
        # Devuelve un JSON con mensaje de error al cliente


# ==========================================
# RUTA: CONSULTA INDIVIDUAL (GET)
# ==========================================

@app.route("/consulta_individual/<codigo>", methods=['GET'])
# Endpoint GET con parámetro dinámico "codigo" (el ID del registro)
def consulta_individual(codigo):
    """
    Consulta individual por ID
    ---
    parameters:
      - name: codigo
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Registro encontrado
    """
    try:
        conn = conectar('localhost', 'root', '1234', 'gestor_contrasena')
        # Se conecta a la base de datos

        cur = conn.cursor()
        # Crea el cursor

        cur.execute("SELECT * FROM baul WHERE id_baul = %s", (codigo,))
        # Busca solo el registro cuyo id_baul coincide con "codigo"
        # El %s previene inyección SQL

        datos = cur.fetchone()
        # Obtiene únicamente el primer resultado, o None si no existe

        cur.close()
        # Cierra el cursor

        conn.close()
        # Cierra la conexión

        if datos:
            # Si se encontró un registro (datos no es None)
            dato = {
                'id_baul': datos[0],      # Columna 0 → ID del registro
                'plataforma': datos[1],   # Columna 1 → Nombre de la plataforma
                'usuario': datos[2],      # Columna 2 → Nombre de usuario o correo
                'clave': datos[3]         # Columna 3 → Contraseña encriptada
            }
            return jsonify({'baul': dato, 'mensaje': 'Registro encontrado'})
            # Devuelve el registro encontrado en JSON
        else:
            return jsonify({'mensaje': 'Registro no encontrado'})
            # Informa que no existe ningún registro con ese ID

    except Exception as ex:
        print(ex)
        # Imprime el error en consola para depuración
        return jsonify({'mensaje': 'Error'})


# ==========================================
# RUTA: REGISTRO (POST)
# ==========================================

@app.route("/registro/", methods=['POST'])
# Endpoint para insertar datos
def registro():
    """
    Registrar nueva contraseña
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            plataforma:
              type: string
            usuario:
              type: string
            clave:
              type: string
    responses:
      200:
        description: Registro agregado
    """
    try:
        data = request.get_json()
        # Recibe los datos enviados en formato JSON

        plataforma = data['plataforma']
        # Extrae el nombre de la plataforma del JSON recibido

        usuario = data['usuario']
        # Extrae el nombre de usuario del JSON recibido

        # ENCRIPTAR CONTRASEÑA
        clave = bcrypt.hashpw(data['clave'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        # data['clave'].encode('utf-8') → convierte la contraseña a bytes (bcrypt lo requiere)
        # bcrypt.gensalt()              → genera una "sal" aleatoria para hacer el hash único
        # .decode('utf-8')              → convierte el hash resultante a string para guardarlo en la BD

        conn = conectar('localhost', 'root', '1234', 'gestor_contrasena')
        # Conecta a la base de datos

        cur = conn.cursor()
        # Crea el cursor

        cur.execute(
            "INSERT INTO baul (plataforma, usuario, clave) VALUES (%s, %s, %s)",
            (plataforma, usuario, clave)
        )
        # Inserta los datos en la tabla
        # Los valores se pasan como parámetros separados para evitar inyección SQL

   # Guarda cambios
        conn.commit()
        # Confirma y guarda los cambios en la BD (sin esto el INSERT no persiste)

        cur.close()
        # Cierra el cursor

        conn.close()
        # Cierra la conexión

        return jsonify({'mensaje': 'Registro agregado'})
        # Respuesta de confirmación al cliente

    except Exception as ex:
        print(ex)
        return jsonify({'mensaje': 'Error'})


# ==========================================
# RUTA: ELIMINAR (DELETE)
# ==========================================

@app.route("/eliminar/<codigo>", methods=['DELETE'])
# Endpoint para eliminar por ID
def eliminar(codigo):
    """
    Eliminar registro por ID
    ---
    parameters:
      - name: codigo
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Registro eliminado
    """
    try:
        conn = conectar('localhost', 'root', '1234', 'gestor_contrasena')
        # Abre la conexión a la BD

        cur = conn.cursor()
        # Crea el cursor

        cur.execute("DELETE FROM baul WHERE id_baul = %s", (codigo,))
        # Elimina el registro cuyo id_baul coincide con "codigo"

        conn.commit()
        # Guarda cambios

        cur.close()
        # Cierra el cursor

        conn.close()
        # Cierra la conexión

        return jsonify({'mensaje': 'Registro eliminado'})
        # Informa al cliente que el registro fue borrado

    except Exception as ex:
        print(ex)
        return jsonify({'mensaje': 'Error'})


# ==========================================
# RUTA: ACTUALIZAR (PUT)
# ==========================================

@app.route("/actualizar/<codigo>", methods=['PUT'])
# Endpoint para actualizar por ID
def actualizar(codigo):
    """
    Actualizar registro por ID
    ---
    parameters:
      - name: codigo
        in: path
        required: true
        type: integer
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            plataforma:
              type: string
            usuario:
              type: string
            clave:
              type: string
    responses:
      200:
        description: Registro actualizado
    """
    try:
        data = request.get_json()
        # Recibe los datos nuevos en formato JSON

        plataforma = data['plataforma']
        # Nuevo valor para la plataforma

        usuario = data['usuario']
        # Nuevo valor para el usuario

        # ENCRIPTAR CONTRASEÑA
        clave = bcrypt.hashpw(data['clave'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        # Convierte la nueva contraseña a bytes, genera nueva sal y convierte el hash a string
        # El hash será diferente aunque la clave sea igual (por la sal aleatoria)

        conn = conectar('localhost', 'root', '1234', 'gestor_contrasena')
        # Abre la conexión a la BD

        cur = conn.cursor()
        # Crea el cursor

        cur.execute(
            "UPDATE baul SET plataforma = %s, usuario = %s, clave = %s WHERE id_baul = %s",
            (plataforma, usuario, clave, codigo)
        )
        # Actualiza los tres campos del registro indicado por "codigo"
        # Los valores se pasan como parámetros para evitar inyección SQL

        conn.commit()
        # Confirma los cambios en la BD

        cur.close()
        # Cierra el cursor

        conn.close()
        # Cierra la conexión

        return jsonify({'mensaje': 'Registro actualizado'})
        # Confirma al cliente que la actualización fue exitosa

    except Exception as ex:
        print(ex)
        return jsonify({'mensaje': 'Error'})


# ==========================================
# EJECUCIÓN
# ==========================================

if __name__ == '__main__':
    app.run(debug=True)
    # Ejecuta el servidor en modo desarrollo (recarga automática al guardar cambios)