from datetime import datetime, timezone
from flask import Flask, Response, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import json
import paho.mqtt.client as mqtt

# ********************* CONEXÃO BANCO DE DADOS *********************************

app = Flask('registro')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Senai%40134@127.0.0.1/db_coleta2'
app.config['SQLALCHEMY_ECHO'] = True  

mybd = SQLAlchemy(app)

# ********************* CONEXÃO SENSORES *********************************

mqtt_data = {}

def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected with result code " + str(rc))
    client.subscribe("projeto_integrado/SENAI134/Cienciadedados/grupo1")

def on_message(client, userdata, msg):
    global mqtt_data
    payload = msg.payload.decode('utf-8')
    mqtt_data = json.loads(payload)
    print(f"Received message: {mqtt_data}")

    with app.app_context():
        try:
            temperatura = mqtt_data.get('temperature')
            pressao = mqtt_data.get('pressure')
            altitude = mqtt_data.get('altitude')
            umidade = mqtt_data.get('humidity')
            co2 = mqtt_data.get('CO2')
            poeira1 = mqtt_data.get('poeira1')
            poeira2 = mqtt_data.get('poeira2')
            status = mqtt_data.get('status')

            timestamp_unix = mqtt_data.get('timestamp')
            if timestamp_unix is None:
                print("Timestamp não encontrado no payload")
                return

            try:
                timestamp = datetime.fromtimestamp(int(timestamp_unix), tz=timezone.utc)
            except (ValueError, TypeError) as e:
                print(f"Erro ao converter timestamp: {str(e)}")
                return

            new_data = Registro(
                temperatura_c=temperatura,
                pressao_pa=pressao,
                altitude_m=altitude,
                umidade_ur=umidade,
                co2_ppm=co2,
                data_registro=timestamp,
                poeira1_mg_m3=poeira1,
                poeira2_mg_m3=poeira2,
                status_registro=status
            )

            mybd.session.add(new_data)
            mybd.session.commit()
            print("Dados inseridos no banco de dados com sucesso")

        except Exception as e:
            print(f"Erro ao processar os dados do MQTT: {str(e)}")
            mybd.session.rollback()

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect("test.mosquitto.org", 1883, 60)

def start_mqtt():
    mqtt_client.loop_start()

# ********************************************************************************************************

@app.route('/data', methods=['POST'])
def post_data():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Nenhum dado fornecido"}), 400

        print(f"Dados recebidos: {data}")

        temperatura = data.get('temperatura_c')
        pressao = data.get('pressao_pa')
        altitude = data.get('altitude_m')
        umidade = data.get('umidade_ur')
        co2 = data.get('co2_ppm')
        poeira1 = data.get('poeira1_mg_m3')
        poeira2 = data.get('poeira2_mg_m3')
        status = data.get('status_registro')
        timestamp_unix = data.get('data_registro')

        try:
            timestamp = datetime.fromtimestamp(int(timestamp_unix), tz=timezone.utc)
        except ValueError as e:
            print(f"Erro no timestamp: {str(e)}")
            return jsonify({"error": "Timestamp inválido"}), 400

        new_data = Registro(
            temperatura_c=temperatura,
            pressao_pa=pressao,
            altitude_m=altitude,
            umidade_ur=umidade,
            co2_ppm=co2,
            data_registro=timestamp,
            poeira1_mg_m3=poeira1,
            poeira2_mg_m3=poeira2,
            status_registro=status
        )

        mybd.session.add(new_data)
        mybd.session.commit()
        print("Dados inseridos no banco de dados com sucesso")

        return jsonify({"message": "Data received successfully"}), 201

    except Exception as e:
        print(f"Erro ao processar a solicitação: {str(e)}")
        mybd.session.rollback()
        return jsonify({"error": "Falha ao processar os dados"}), 500

@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(mqtt_data)

# ********************* MODELO BANCO DE DADOS *********************************

class Registro(mybd.Model):
    __tablename__ = 'tb_registros_teste'
    id_registro = mybd.Column(mybd.Integer, primary_key=True, autoincrement=True)
    temperatura_c = mybd.Column(mybd.Numeric(10, 2))
    pressao_pa = mybd.Column(mybd.Numeric(10, 2))
    altitude_m = mybd.Column(mybd.Numeric(10, 2))
    umidade_ur = mybd.Column(mybd.Numeric(10, 2))
    co2_ppm = mybd.Column(mybd.Numeric(10, 2))
    data_registro = mybd.Column(mybd.DateTime)
    poeira1_mg_m3 = mybd.Column(mybd.Numeric(10, 2))
    poeira2_mg_m3 = mybd.Column(mybd.Numeric(10, 2))
    status_registro = mybd.Column(mybd.String(200))

    def to_json(self):
        return {
            "id_registro": self.id_registro,
            "temperatura_c": float(self.temperatura_c) if self.temperatura_c else None,
            "pressao_pa": float(self.pressao_pa) if self.pressao_pa else None,
            "altitude_m": float(self.altitude_m) if self.altitude_m else None,
            "umidade_ur": float(self.umidade_ur) if self.umidade_ur else None,
            "co2_ppm": float(self.co2_ppm) if self.co2_ppm else None,
            "data_registro": self.data_registro.strftime('%Y-%m-%d %H:%M:%S') if self.data_registro else None,
            "poeira1_mg_m3": float(self.poeira1_mg_m3) if self.poeira1_mg_m3 else None,
            "poeira2_mg_m3": float(self.poeira2_mg_m3) if self.poeira2_mg_m3 else None,
            "status_registro": self.status_registro
        }

# *************************************************************************************

@app.route("/registro", methods=["GET"])
def seleciona_registro():
    registro_objetos = Registro.query.all()
    registro_json = [registro.to_json() for registro in registro_objetos]
    return gera_response(200, "registro", registro_json)

@app.route("/registro/<id>", methods=["GET"])
def seleciona_registro_id(id):
    registro_objetos = Registro.query.filter_by(id_registro=id).first()
    if registro_objetos:
        return gera_response(200, "registro", registro_objetos.to_json())
    else:
        return gera_response(404, "registro", {}, "Registro não encontrado")

@app.route("/registro/<id>", methods=["DELETE"])
def deleta_registro(id):
    registro_objetos = Registro.query.filter_by(id_registro=id).first()
    if registro_objetos:
        try:
            mybd.session.delete(registro_objetos)
            mybd.session.commit()
            return gera_response(200, "registro", registro_objetos.to_json(), "Deletado com sucesso")
        except Exception as e:
            print('Erro', e)
            mybd.session.rollback()
            return gera_response(400, "registro", {}, "Erro ao deletar")
    else:
        return gera_response(404, "registro", {}, "Registro não encontrado")

def gera_response(status, nome_do_conteudo, conteudo, mensagem=False):
    body = {}
    body[nome_do_conteudo] = conteudo
    if mensagem:
        body["mensagem"] = mensagem
    return Response(json.dumps(body), status=status, mimetype="application/json")

if __name__ == '__main__':
    with app.app_context():
        mybd.create_all()
    start_mqtt()
    app.run(port=5000, host='localhost', debug=True)
