# pip install streamlit
# pip install mysql-connector-python

import mysql.connector
import pandas as pd

def conexao(query): # query = consulta que vai fazer

    conection = mysql.connector.connect(
        host = "127.0.0.1",
        port = "3306",
        user = "root",
        password = "Senai@134",
        db = "db_coleta2"
    )

    dataframe = pd.read_sql(query, conection)   # Executar o SQL e armazenar o resultado no dataframe

    conection.close() # fecha a conexão
    return dataframe 