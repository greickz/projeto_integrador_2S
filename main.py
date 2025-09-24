from sqlalchemy import DateTime
from datetime import datetime
from flask import Flask, Response, request
from flask_sqlalchemy import SQLAlchemy
import json
app = Flask('coletas_cubos')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Senai%40134@127.0.0.1/db_coleta'
mydb = SQLAlchemy(app)

class Coleta(mydb.Model): 
    __tablename__ = 'tb_registros'
    id_registro = mydb.Column(mydb.Integer, primary_key = True)
    temperatura_c = mydb.Column(mydb.Numeric(10,2))
    pressao_pa = mydb.Column(mydb.Numeric(10,2))
    altitude_m = mydb.Column(mydb.Numeric(10,2))
    umidade_ur = mydb.Column(mydb.Numeric(10,2))
    co2_ppm = mydb.Column(mydb.Numeric(10,2))
    data_registro = mydb.Column(DateTime, default=datetime.utcnow)
    poeira1_mg_m3 = mydb.Column(mydb.Numeric(10,2))
    poeira2_mg_m3 = mydb.Column(mydb.Numeric(10,2))
    status_registro = mydb.Column(mydb.String(200))

    def to_json(self):
        return {
            "id_registro": self.id_registro,
            "temperatura_c": float(self.temperatura_c) if self.temperatura_c is not None else None,
            "pressao_pa": float(self.pressao_pa) if self.pressao_pa is not None else None,
            "altitude_m": float(self.altitude_m) if self.altitude_m is not None else None,
            "umidade_ur": float(self.umidade_ur) if self.umidade_ur is not None else None,
            "co2_ppm": float(self.co2_ppm) if self.co2_ppm is not None else None,
            "data_registro": self.data_registro.isoformat() if self.data_registro is not None else None,
            "poeira1_mg_m3": float(self.poeira1_mg_m3) if self.poeira1_mg_m3 is not None else None,
            "poeira2_mg_m3": float(self.poeira2_mg_m3) if self.poeira2_mg_m3 is not None else None,
            "status_registro": self.status_registro
        }
    

# GET

@app.route('/coletas_cubos', methods=['GET'])
def get_coletas():
    consulta_coleta = Coleta.query.all()
    coleta_json = [c.to_json() for c in consulta_coleta]
    return gera_resposta(200, "Dados", coleta_json, 'Dados encontrados!!!')
    

# POST

@app.route('/coletas_cubos', methods=['POST'])
def post_coletas():
    requisicao = request.get_json()
    try:
        dado = Coleta(
            id_registro = requisicao['id_registro'],
            temperatura_c = requisicao['temperatura_c'],
            pressao_pa = requisicao['pressao_pa'],
            altitude_m = requisicao['altitude_m'],
            umidade_ur = requisicao['umidade_ur'],
            co2_ppm = requisicao['co2_ppm'],
            data_registro = requisicao['data_registro'],
            poeira1_mg_m3 = requisicao['poeira1_mg_m3'],
            poeira2_mg_m3 = requisicao['poeira2_mg_m3'],
            status_registro = requisicao['status_registro']
        )

        mydb.session.add(dado)
        mydb.session.commit()

        return gera_resposta(201, "Dados ", dado.to_json(), 'Criado com sucesso!!!')

    except Exception as e:
        print('ERRO', e)
        return gera_resposta(400, "Dados ", {}, "Erro ao cadastrar!!!")
    

# DELETE

@app.route('/coletas_cubos/<id_registro>', methods=['DELETE'])
def delete_coletas(id_registro):
    registro = Coleta.query.filter_by(id_registro = id_registro).first()
    try:
        mydb.session.delete(registro)
        mydb.session.commit()
        return gera_resposta(200, "Dados",registro.to_json(), "Deletado com sucesso!!")
    
    except Exception as e:
        print('ERRO')
        return gera_resposta(400, "Dados", {}, "Falha ao deletar")


# PUT

@app.route('/coletas_cubos/<id_registro>', methods=['PUT'])
def atualiza_coletas(id_registro):
    registro = Coleta.query.filter_by(id_registro = id_registro).first()
    requisicao = request.get_json()

    try:
        if ('temperatura_c' in requisicao):
            registro.temperatura_c = requisicao['temperatura_c']
        if ('pressao_pa' in requisicao):
            registro.pressao_pa = requisicao['pressao_pa']
        if ('altitude_m' in requisicao):
            registro.altitude_m = requisicao['altitude_m']
        if ('umidade_ur' in requisicao):
            registro.umidade_ur = requisicao['umidade_ur']
        if ('co2_ppm' in requisicao):
            registro.co2_ppm = requisicao['co2_ppm']
        if ('data_registro' in requisicao):
            registro.data_registro = requisicao['data_registro']
        if ('poeira1_mg_m3' in requisicao):
            registro.poeira1_mg_m3 = requisicao['poeira1_mg_m3']
        if ('poeira2_mg_m3' in requisicao):
            registro.poeira2_mg_m3 = requisicao['poeira2_mg_m3']
        if ('status_registro' in requisicao):
            registro.status_registro = requisicao['status_registro']

        mydb.session.add(registro)
        mydb.session.commit()
        return gera_resposta(200, "Dados",registro.to_json(), "Dado atualizado com sucesso")
    
    except Exception as e:
        print('ERRO')
        return gera_resposta(400, "Dados", {}, "Erro ao atualizar")

def gera_resposta(status, nome_conteudo, conteudo, mensagem = False):
    body = {}
    body[nome_conteudo] = conteudo
    if(mensagem):
        body['mensagem'] = mensagem
    return Response(json.dumps(body), status= status, mimetype='aplication/json')
    
app.run(port=5000, host='localhost', debug=True)