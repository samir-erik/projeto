from flask import Flask, jsonify
import psycopg2
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Link do Supabase sem os colchetes!
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

if __name__ == '__main__':
    app.run(debug=True)