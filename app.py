from flask import Flask, jsonify
import psycopg2
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# URI centralizada - Use a porta 6543 para o Pooler do Supabase
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
    return jsonify([{"titulo": d[0], "descricao": d[1], "url": d[2], "imagem": d[3], "categoria": d[4]} for d in dados])

@app.route("/categoria/<categoria>")
def categoria_rota(categoria):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT titulo, descricao, url, imagem, categoria 
        FROM noticias 
        WHERE TRIM(categoria) ILIKE %s 
        ORDER BY data_publicacao DESC
    """, (categoria,))
    dados = cursor.fetchall()
    conn.close()
    return jsonify([{"titulo": d[0], "descricao": d[1], "url": d[2], "imagem": d[3], "categoria": d[4]} for d in dados])

@app.route("/contar_acesso/<path:url>", methods=["POST"])
def contar_acesso(url):
    try:
        conn = conectar()
        cursor = conn.cursor()
        # COALESCE garante que se o acesso for NULL, ele vire 0 antes de somar
        cursor.execute("UPDATE noticias SET acessos = COALESCE(acessos, 0) + 1 WHERE url = %s", (url,))
        conn.commit()
        conn.close()
        return jsonify({"status": "sucesso"})
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

@app.route("/dashboard")
def dashboard():
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*), SUM(COALESCE(acessos, 0)) FROM noticias")
    total_noticias, total_acessos = cursor.fetchone()
    
    cursor.execute("SELECT categoria, COUNT(*) FROM noticias GROUP BY categoria")
    por_categoria = [
        {
            "categoria": d[0], 
            "quantidade": d[1],
            "percentual": round((d[1] / total_noticias) * 100, 1) if total_noticias > 0 else 0
        } for d in cursor.fetchall()
    ]
    
    cursor.execute("SELECT titulo, COALESCE(acessos, 0) as Cliques FROM noticias WHERE acessos > 0 ORDER BY acessos DESC LIMIT 5")
    ranking = [{"titulo": d[0], "acessos": d[1]} for d in cursor.fetchall()]
    
    conn.close()
    return jsonify({
        "estatisticas_gerais": {"total": total_noticias, "cliques_totais": int(total_acessos or 0)},
        "por_categoria": por_categoria,
        "ranking_top_5": ranking
    })

@app.route("/buscar/<termo>")
def buscar(termo):
    conn = conectar()
    cursor = conn.cursor()
    valor = f"%{termo}%"
    cursor.execute("""
        SELECT titulo, descricao, url, imagem, categoria 
        FROM noticias 
        WHERE titulo ILIKE %s OR descricao ILIKE %s 
        ORDER BY data_publicacao DESC
    """, (valor, valor))
    dados = cursor.fetchall()
    conn.close()
    return jsonify([{"titulo": d[0], "descricao": d[1], "url": d[2], "imagem": d[3], "categoria": d[4]} for d in dados])

if __name__ == '__main__':
    porta = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=porta)