from flask import Flask, jsonify
import psycopg2
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def conectar():
    return psycopg2.connect(
        host="localhost",
        database="noticias_db",
        user="postgres",
        password="1234"
    )

# 📰 TODAS AS NOTÍCIAS
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

    lista = []
    for d in dados:
        lista.append({
            "titulo": d[0],
            "descricao": d[1],
            "url": d[2],
            "imagem": d[3],
            "categoria": d[4]
        })

    return jsonify(lista)

# 🔎 FILTRAR POR CATEGORIA
@app.route("/categoria/<categoria>")
def categoria(categoria):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT titulo, descricao, url, imagem, categoria
        FROM noticias
        WHERE categoria = %s
        ORDER BY data_publicacao DESC
    """, (categoria,))

    # 🔎 BUSCA TEXTUAL (TÍTULO OU DESCRIÇÃO)
@app.route("/buscar/<termo>")
def buscar(termo):
    conn = conectar()
    cursor = conn.cursor()

    # O ILIKE busca ignorando maiúsculas e o % permite busca parcial
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

    lista = []
    for d in dados:
        lista.append({
            "titulo": d[0],
            "descricao": d[1],
            "url": d[2],
            "imagem": d[3],
            "categoria": d[4]
        })

    return jsonify(lista)

    dados = cursor.fetchall()
    conn.close()

    lista = []
    for d in dados:
        lista.append({
            "titulo": d[0],
            "descricao": d[1],
            "url": d[2],
            "imagem": d[3],
            "categoria": d[4]
        })

    return jsonify(lista)

app.run(debug=True)