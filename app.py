from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from flask_cors import CORS
import os
import json
#from datetime import datetime

app = Flask(__name__)

CORS(app)
CORS(app, allow_headers='*')
#CORS(app, allow_headers=['Content-Type', 'Authorization'])

# Obtén la ruta completa al directorio actual
basedir = os.path.abspath(os.path.dirname(__file__))

#Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db/HabitosDB.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialización de la extensión SQLAlchemy
db = SQLAlchemy(app)

#Modelos
class CategoriaHabitos(db.Model):
    __tablename__ = 'categoria_habitos'
    id_categoriahabitos = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(200))
    estado = db.Column(db.Boolean, default=True)
    color = db.Column(db.String(200))
    color_text = db.Column(db.String(200))
    esbueno = db.Column(db.Boolean, default=True)
    id_usuario = db.Column(db.Integer)

class Habitos(db.Model):
    id_habito = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(200))
    estado = db.Column(db.Boolean, default=True)
    color = db.Column(db.String(200))
    color_text = db.Column(db.String(200))
    id_categoriahabitos = db.Column(db.Integer, db.ForeignKey('CATEGORIA_HABITOS.ID_CATEGORIAHABITOS'))
    hora_inicio = db.Column(db.String(200))
    hora_fin = db.Column(db.String(200))

class SeguimientoHabitos(db.Model):
    __tablename__ = 'seguimientohabitos'
    id_seguimientohabitos = db.Column(db.Integer, primary_key=True)
    id_habito = db.Column(db.Integer, db.ForeignKey('HABITOS.ID_HABITO'))
    estado = db.Column(db.Boolean, default=True)
    color = db.Column(db.String(200))
    descripcion = db.Column(db.String(200))
    fecha_registro = db.Column(db.DateTime)

cod_resp = {
                "success": 200,
                "error": 400
            }

#Endpoints Categoria habitos
@app.route('/api/getListaCategorias/<id_usuario>', methods=['GET'])
def getListaCategorias(id_usuario):
    try:
        lista_categorias = CategoriaHabitos.query\
                            .filter(CategoriaHabitos.estado == True)\
                            .filter(CategoriaHabitos.id_usuario == id_usuario)\
                            .all()
        datosJson = [{'ID_CATEGORIAHABITOS': category.id_categoriahabitos, 'DESCRIPCION': category.descripcion, 'COLOR': category.color, 'ESBUENO': category.esbueno} for category in lista_categorias]
        return jsonify({'cod_resp': cod_resp["success"],'lista_categorias': datosJson})
    except SQLAlchemyError as e:
        return jsonify({'cod_resp': cod_resp["error"], 'message': e})
    except Exception as e:
        return jsonify({'cod_resp': cod_resp["error"], 'message': e})

@app.route('/api/saveCategoria', methods=['POST'])
def saveCategoria():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        try:
            category = CategoriaHabitos(
                descripcion = request.json['descripcion'],
                estado = request.json['estado'],
                color = request.json['color'],
                esbueno = request.json['esbueno'],
                id_usuario = request.json['id_usuario']
            )
            db.session.add(category)
            db.session.commit()
            return jsonify({'cod_resp': cod_resp["success"], 'message': 'Nueva categoria guardada exitosamente'})
        except SQLAlchemyError as e:
            db.session.rollback()  # Revertir cambios en caso de error
            return jsonify({'cod_resp': cod_resp["error"], 'message': e})
        except Exception as e:
            db.session.rollback()  # Revertir cambios en caso de error
            return jsonify({'cod_resp': cod_resp["error"], 'message': e})  
    else:
        error = 'Content-Type not supported!'
        return jsonify({'cod_resp': cod_resp["error"], 'message': error})
    
@app.route('/api/saveHistorialSeguimiento', methods=['POST'])
def saveHistorialSeguimiento():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        for item in request.json['lista_habitos']:
            try:
                seguimiento = SeguimientoHabitos(
                    id_habito = item['ID_HABITO'],
                    estado = True,
                    color = item['COLOR'],
                    fecha_registro = datetime.now()
                )
                db.session.add(seguimiento)
                db.session.commit()
            except SQLAlchemyError as e:
                db.session.rollback()  # Revertir cambios en caso de error
                return jsonify({'cod_resp': cod_resp["error"], 'message': e})
            except Exception as e:
                return jsonify({'cod_resp': cod_resp["error"], 'message': e})
        return jsonify({'cod_resp': cod_resp["success"], 'message': 'Registro de habitos cargados exitosamente'})

    

#Endpoints Habtios
@app.route('/api/getListaHabitos/<id_usuario>/<id_categoria>', methods=['GET'])
def getListaHabitos(id_usuario, id_categoria):
    try:
        page = request.args.get('page', 1, type=int) 
        per_page= request.args.get('per_page', 5, type=int)
        if id_categoria == "-1":
            print("Muestra todoso")
            habitosC = db.session.query(Habitos, CategoriaHabitos).select_from(Habitos)\
                            .join(CategoriaHabitos, Habitos.id_categoriahabitos == CategoriaHabitos.id_categoriahabitos)\
                            .filter(Habitos.estado == True)\
                            .filter(CategoriaHabitos.estado == True)\
                            .filter(CategoriaHabitos.id_usuario == id_usuario)\
                            .paginate(page=page, per_page=per_page)
        else:
            print("Muestra por categorias")
            habitosC = db.session.query(Habitos, CategoriaHabitos).select_from(Habitos)\
                            .join(CategoriaHabitos, Habitos.id_categoriahabitos == CategoriaHabitos.id_categoriahabitos)\
                            .filter(Habitos.estado == True)\
                            .filter(CategoriaHabitos.estado == True)\
                            .filter(CategoriaHabitos.id_usuario == id_usuario)\
                            .filter(CategoriaHabitos.id_categoriahabitos == id_categoria)\
                            .paginate(page=page, per_page=per_page)
             
        datosJson = []
        for habito, categoria in habitosC.items:
            datosJson.append({'ID_HABITO': habito.id_habito,
                            'CATEGORIA': categoria.descripcion,
                            'HABITO': habito.descripcion,
                            'COLOR': habito.color})
        meta = {
            "page": habitosC.page,
            "pages": habitosC.pages,
            "total_count": habitosC.total,
            "prev": habitosC.prev_num,
            "prev_page": habitosC.prev_num,
            "next_page": habitosC.next_num,
            "has_next": habitosC.has_next,
            "has_prev": habitosC.has_prev
        }
        return jsonify({'cod_resp': cod_resp["success"], 'lista_habitos': datosJson, 'meta': meta})
    except SQLAlchemyError as e:
        return jsonify({'cod_resp': cod_resp["error"], 'message': e})
    except Exception as e:
        return jsonify({'cod_resp': cod_resp["error"], 'message': e})

@app.route('/api/getListaHabitosFiltro/<id_usuario>/<categoria_id>/<descripcion>', methods=['GET'])
def getListaHabitosFiltro(id_usuario, categoria_id, descripcion):
    try:
        page = request.args.get('page', 1, type=int) 
        per_page= request.args.get('per_page', 5, type=int)
        if int(categoria_id) == -1: #Muestra todas las categorias
            habitosC = db.session.query(Habitos, CategoriaHabitos).select_from(Habitos)\
                            .join(CategoriaHabitos, Habitos.id_categoriahabitos == CategoriaHabitos.id_categoriahabitos)\
                            .filter(Habitos.estado == True)\
                            .filter(CategoriaHabitos.estado == True)\
                            .filter(CategoriaHabitos.id_usuario == id_usuario)\
                            .filter(Habitos.descripcion.like("%"+descripcion.strip()+"%"))\
                            .paginate(page=page, per_page=per_page)
        else:
             habitosC = db.session.query(Habitos, CategoriaHabitos).select_from(Habitos)\
                            .join(CategoriaHabitos, Habitos.id_categoriahabitos == CategoriaHabitos.id_categoriahabitos)\
                            .filter(Habitos.estado == True)\
                            .filter(CategoriaHabitos.estado == True)\
                            .filter(Habitos.id_categoriahabitos == categoria_id)\
                            .filter(CategoriaHabitos.id_usuario == id_usuario)\
                            .filter(Habitos.descripcion.like("%"+descripcion.strip()+"%"))\
                            .paginate(page=page, per_page=per_page)
                            

                        
        datosJson = []
        for habito, categoria in habitosC.items:
            datosJson.append({'ID_HABITO': habito.id_habito,
                            'CATEGORIA': categoria.descripcion,
                            'HABITO': habito.descripcion,
                            'COLOR': habito.color})
        meta = {
            "page": habitosC.page,
            "pages": habitosC.pages,
            "total_count": habitosC.total,
            "prev": habitosC.prev_num,
            "prev_page": habitosC.prev_num,
            "next_page": habitosC.next_num,
            "has_next": habitosC.has_next,
            "has_prev": habitosC.has_prev
        }
        return jsonify({'cod_resp': cod_resp["success"], 'lista_habitos': datosJson, 'meta': meta})
    except SQLAlchemyError as e:
        return jsonify({'cod_resp': cod_resp["error"], 'message': e})
    except Exception as e:
        return jsonify({'cod_resp': cod_resp["error"], 'message': e})

@app.route('/api/saveHabito', methods=['POST'])
def saveHabito():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        try:
            habito_new = Habitos(
                descripcion = request.json['descripcion'],
                estado = request.json['estado'],
                color = request.json['color'],
                color_text = request.json['color_text'],
                id_categoriahabitos = request.json['id_categoriahabitos'],
                hora_inicio = request.json['hora_inicio'],
                hora_fin = request.json['hora_fin']
            )
            db.session.add(habito_new)
            db.session.commit()
            return jsonify({'cod_resp': cod_resp["success"], 'message': 'Nuevo habito guardado exitosamente'})
        except SQLAlchemyError as e:
            db.session.rollback()  # Revertir cambios en caso de error
            return jsonify({'cod_resp': cod_resp["error"], 'message': e})
        except Exception as e:
            db.session.rollback()  # Revertir cambios en caso de error
            return jsonify({'cod_resp': cod_resp["error"], 'message': e}) 
    else:
        error = 'Content-Type not supported!'
        return jsonify({'cod_resp': cod_resp["error"], 'message': error})

#Registro habitos diarios
@app.route('/api/saveHabitoDiario', methods=['POST'])
def saveHabitoDiario():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        try:
            segHabitos_new = SeguimientoHabitos(
                id_habito = request.json['id_habito'],
                estado = request.json['estado'],
                color = request.json['color'],
                fecha_registro = datetime.now()
            )
            db.session.add(segHabitos_new)
            db.session.commit()
            return jsonify({'cod_resp': cod_resp["success"], 'message': 'Registro guardado exitosamente'})
        except SQLAlchemyError as e:
            db.session.rollback()  # Revertir cambios en caso de error
            return jsonify({'cod_resp': cod_resp["error"], 'message': e})
        except Exception as e:
            db.session.rollback()  # Revertir cambios en caso de error
            return jsonify({'cod_resp': cod_resp["error"], 'message': e}) 
    else:
        error = 'Content-Type not supported!'
        return jsonify({'err': error})

@app.route('/api/historicoHabitosDiarios', methods=['GET'])
def historicoHabitosDiarios():
    try:
        page = request.args.get('page', 1, type=int) 
        per_page= request.args.get('per_page', 5, type=int)

        print('page', page)
        print('per_page', per_page)

        historicoHabitosDiarios_query = db.session.query(SeguimientoHabitos, Habitos).select_from(SeguimientoHabitos)\
                        .join(Habitos, SeguimientoHabitos.id_habito == Habitos.id_habito)\
                        .filter(SeguimientoHabitos.estado == True)\
                        .order_by(SeguimientoHabitos.fecha_registro.desc(), Habitos.id_categoriahabitos.desc())\
                        .all()
                        
        datosJson = []
        fecha_pivot = historicoHabitosDiarios_query[0][0].fecha_registro
        habitos = []
        newHabitosObj = {}
        cont = 0
        page_pivot = 1
        for historicoHabitosDiarios, habito in historicoHabitosDiarios_query:
            if fecha_pivot.date() != historicoHabitosDiarios.fecha_registro.date():
                newHabitosObj = {
                    'FECHA_REGISTROS': fecha_pivot,
                    'HABITOS_ARRAY': json.dumps(habitos)
                }
                if cont < per_page:
                    if page == page_pivot:
                        datosJson.append(newHabitosObj)
                    cont = cont + 1
                else:
                    cont = 0
                    page_pivot = page_pivot + 1
                    
                fecha_pivot = historicoHabitosDiarios.fecha_registro
                newHabitosObj = {}
                habitos = []
            if fecha_pivot.date() == historicoHabitosDiarios.fecha_registro.date():
                habitos.append({"DESCRIPCION": habito.descripcion})
        
        return jsonify({'cod_resp': cod_resp["success"], 'lista_seguimiento': datosJson, 'meta': 'meta'})
    except SQLAlchemyError as e:
        return jsonify({'cod_resp': cod_resp["error"], 'message': e})
    except Exception as e:
        return jsonify({'cod_resp': cod_resp["error"], 'message': e})

if __name__ == '__main__':
    with app.app_context():
        # Crea las tablas en la base de datos antes de ejecutar la aplicación
        #db.create_all()
        db.reflect()
    app.run(host='0.0.0.0', port=5000,  debug=True)
