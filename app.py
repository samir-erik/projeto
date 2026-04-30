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
    
    # Total de notícias e cliques para cálculos de %
    cursor.execute("SELECT COUNT(*), SUM(acessos) FROM noticias")
    total_noticias, total_acessos = cursor.fetchone()
    total_acessos = total_acessos or 0 # Evita erro se for zero
    
    # Quantidade e Porcentagem por categoria
    cursor.execute("SELECT categoria, COUNT(*) FROM noticias GROUP BY categoria")
    por_categoria = [
        {
            "categoria": d[0], 
            "quantidade": d[1],
            "percentual": round((d[1] / total_noticias) * 100, 1) if total_noticias > 0 else 0
        } for d in cursor.fetchall()
    ]
    
    # Top 5 Notícias mais acessadas
    cursor.execute("SELECT titulo, acessos, categoria FROM noticias WHERE acessos > 0 ORDER BY acessos DESC LIMIT 5")
    ranking = [{"titulo": d[0], "acessos": d[1], "categoria": d[2]} for d in cursor.fetchall()]
    
    conn.close()
    return jsonify({
        "estatisticas_gerais": {"total": total_noticias, "cliques_totais": total_acessos},
        "por_categoria": por_categoria,
        "ranking_top_5": ranking
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