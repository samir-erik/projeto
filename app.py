from flask import Flask, jsonify
import psycopg2
from flask_cors import CORS
import os
import threading
from bot_auto import buscar_e_salvar

app = Flask(__name__)
CORS(app)

# Link do Supabase
DB_URI = "postgresql://postgres.ruwagoepsujdemktrqno:C66236DBCc.@aws-1-us-east-1.pooler.supabase.com:5432/postgres"

def conectar():
    return psycopg2.connect(DB_URI)

@app.route("/noticias")
def noticias():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT titulo, descricao, url, imagem, categoria
        FROM noticias
        ORDER BY data_publicacao DESC
    """)
    dados = cursor.fetchall()
    conn.close()

    lista = [{"titulo": d[0], "descricao": d[1], "url": d[2], "imagem": d[3], "categoria": d[4]} for d in dados]
    return jsonify(lista)

@app.route("/categoria/<categoria>")
def categoria_rota(categoria):
    conn = conectar()
    cursor = conn.cursor()
    # Usamos ILIKE para o filtro ser mais flexível (ex: 'esportes' ou 'Esportes')
    cursor.execute("""
        SELECT titulo, descricao, url, imagem, categoria
        FROM noticias
        WHERE TRIM(categoria) ILIKE %s
        ORDER BY data_publicacao DESC
    """, (categoria,))
    dados = cursor.fetchall()
    conn.close()

    lista = [{"titulo": d[0], "descricao": d[1], "url": d[2], "imagem": d[3], "categoria": d[4]} for d in dados]
    return jsonify(lista)

@app.route("/buscar/<termo>")
def buscar(termo):
    conn = conectar()
    cursor = conn.cursor()
    query = """
        SELECT titulo, descricao, url, imagem, categoria
        FROM noticias
        WHERE titulo ILIKE %s OR descricao ILIKE %s
        ORDER BY data_publicacao DESC
    """
    valor = f"%{termo}%"
    cursor.execute(query, (valor, valor))
    dados = cursor.fetchall()
    conn.close()

    lista = [{"titulo": d[0], "descricao": d[1], "url": d[2], "imagem": d[3], "categoria": d[4]} for d in dados]
    return jsonify(lista)

def rodar_bot_em_background():
    # Chama a função de busca que já criamos
    buscar_e_salvar()

# Disparamos o bot em uma "thread" separada para não travar o site
threading.Thread(target=rodar_bot_em_background, daemon=True).start()

if __name__ == '__main__':
    # O Render fornece uma porta variável, por isso usamos os.environ.get
    porta = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=porta)