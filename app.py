from flask import Flask, jsonify
import psycopg2
from flask_cors import CORS
import os
import threading
from bot_auto import buscar_e_salvar

app = Flask(__name__)
CORS(app)

# Link do Supabase
DB_URI = "postgresql://postgres.ruwagoepsujdemktrqno:C66236DBCc.@aws-1-us-east-1.pooler.supabase.com:6543/postgres"

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

@app.route("/contar_acesso/<path:url>", methods=["POST"])
def contar_acesso(url):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE noticias SET acessos = acessos + 1 WHERE url = %s", (url,))
    conn.commit()
    conn.close()
    return jsonify({"status": "sucesso"})

@app.route("/dashboard")
def dashboard():
    conn = conectar()
    cursor = conn.cursor()
    
    # Quantidade por categoria
    cursor.execute("SELECT categoria, COUNT(*) FROM noticias GROUP BY categoria")
    por_categoria = [{"categoria": d[0], "quantidade": d[1]} for d in cursor.fetchall()]
    
    # Notícia mais acessada
    cursor.execute("SELECT titulo, acessos FROM noticias ORDER BY acessos DESC LIMIT 1")
    mais_acessada = cursor.fetchone()
    
    conn.close()
    return jsonify({
        "por_categoria": por_categoria,
        "mais_acessada": {"titulo": mais_acessada[0], "acessos": mais_acessada[1]} if mais_acessada else None
    })
 

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
# threading.Thread(target=rodar_bot_em_background, daemon=True).start()

if __name__ == '__main__':
    # O Render fornece uma porta variável, por isso usamos os.environ.get
    porta = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=porta)