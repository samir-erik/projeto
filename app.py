import os
from flask import Flask, jsonify, request
import psycopg2
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configurações de conexão (Pooler do Supabase para estabilidade)
DB_URI = "postgresql://postgres.ruwagoepsujdemktrqno:C66236DBCc.@aws-1-us-east-1.pooler.supabase.com:6543/postgres"

def conectar():
    return psycopg2.connect(DB_URI)

# --- ROTAS DE NOTÍCIAS ---\n
@app.route("/noticias")
def noticias():
    conn = conectar()
    cursor = conn.cursor()
    # Filtrado para trazer apenas as 3 categorias desejadas na aba "Todas"
    cursor.execute("""
        SELECT titulo, descricao, url, imagem, categoria 
        FROM noticias 
        WHERE TRIM(categoria) IN ('Tecnologia', 'Esportes', 'Economia')
        ORDER BY data_publicacao DESC
    """)
    dados = cursor.fetchall()
    conn.close()
    return jsonify([{"titulo": d[0], "descricao": d[1], "url": d[2], "imagem": d[3], "categoria": d[4]} for d in dados])

@app.route("/categoria/<categoria>")
def categoria_rota(categoria):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT titulo, descricao, url, imagem, categoria FROM noticias WHERE TRIM(categoria) ILIKE %s ORDER BY data_publicacao DESC", (categoria,))
    dados = cursor.fetchall()
    conn.close()
    return jsonify([{"titulo": d[0], "descricao": d[1], "url": d[2], "imagem": d[3], "categoria": d[4]} for d in dados])

@app.route("/data/<data_sel>")
def buscar_por_data(data_sel):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT titulo, descricao, url, imagem, categoria FROM noticias WHERE DATE(data_publicacao) = %s AND TRIM(categoria) IN ('Tecnologia', 'Esportes', 'Economia') ORDER BY data_publicacao DESC", (data_sel,))
    dados = cursor.fetchall()
    conn.close()
    return jsonify([{"titulo": d[0], "descricao": d[1], "url": d[2], "imagem": d[3], "categoria": d[4]} for d in dados])

@app.route("/buscar/<termo>")
def buscar(termo):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT titulo, descricao, url, imagem, categoria FROM noticias WHERE (titulo ILIKE %s OR descricao ILIKE %s) AND TRIM(categoria) IN ('Tecnologia', 'Esportes', 'Economia') ORDER BY data_publicacao DESC", (f"%{termo}%", f"%{termo}%"))
    dados = cursor.fetchall()
    conn.close()
    return jsonify([{"titulo": d[0], "descricao": d[1], "url": d[2], "imagem": d[3], "categoria": d[4]} for d in dados])

@app.route("/datas_disponiveis")
def datas_disponiveis():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT DATE(data_publicacao) as dt FROM noticias WHERE TRIM(categoria) IN ('Tecnologia', 'Esportes', 'Economia') ORDER BY dt DESC")
    dados = cursor.fetchall()
    conn.close()
    return jsonify([str(d[0]) for d in dados])

@app.route("/contar_acesso/<path:url>", methods=["POST"])
def contar_acesso(url):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE noticias SET acessos = COALESCE(acessos, 0) + 1 WHERE url = %s", (url,))
    conn.commit()
    conn.close()
    return jsonify({"status": "sucesso"})

# --- ROTA DO DASHBOARD ---

@app.route("/dashboard")
def dashboard():
    categoria = request.args.get("categoria", "Todas")
    
    conn = conectar()
    cursor = conn.cursor()

    # Define o filtro correto baseado na seleção da categoria
    if categoria != "Todas":
        filtro_sql = "WHERE TRIM(categoria) ILIKE %s"
        params = (categoria,)
    else:
        filtro_sql = "WHERE TRIM(categoria) IN ('Tecnologia', 'Esportes', 'Economia')"
        params = ()

    # 1. Busca total de notícias e cliques filtrados pelas categorias corretas
    cursor.execute(f"SELECT COUNT(*), COALESCE(SUM(acessos), 0) FROM noticias {filtro_sql}", params)
    total_noticias, total_acessos = cursor.fetchone()

    if total_noticias == 0:
        conn.close()
        return jsonify({
            "total": 0, "cliques": 0, "media_titulo": 0, "frescor_medio": 0,
            "qualidade": {"img": 0, "desc": 0}, "sensacionalismo": 0,
            "sentimento": {"humor": "Sem dados 🚫", "cor": "#999", "score_pos": 0},
            "relogio": {"manha": 0, "tarde": 0, "noite": 0, "madrugada": 0},
            "fontes": [], "historico_delay": {"labels": [], "dados": []}
        })

    # 2. Média do tamanho dos títulos
    cursor.execute(f"SELECT AVG(LENGTH(titulo)) FROM noticias {filtro_sql}", params)
    media_titulo = round(float(cursor.fetchone()[0] or 0), 1)

    # 3. Métricas de qualidade (com imagem e com descrição)
    cursor.execute(f"SELECT COUNT(*) FROM noticias {filtro_sql} AND imagem IS NOT NULL AND imagem != ''", params)
    com_img = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM noticias {filtro_sql} AND descricao IS NOT NULL AND descricao != ''", params)
    com_desc = cursor.fetchone()[0]

    # 4. Análise de Sensacionalismo
    palavras_sensacionalistas = ['bomba', 'urgente', 'choque', 'revelado', 'escândalo', 'inacreditável', 'assusta', 'misterioso']
    or_clauses = " OR ".join(["titulo ILIKE %s" for _ in palavras_sensacionalistas])
    
    if categoria != "Todas":
        sql_sensa = f"SELECT COUNT(*) FROM noticias WHERE ({or_clauses}) AND TRIM(categoria) ILIKE %s"
        params_sensa = tuple(f"%{p}%" for p in palavras_sensacionalistas) + (categoria,)
    else:
        sql_sensa = f"SELECT COUNT(*) FROM noticias WHERE ({or_clauses}) AND TRIM(categoria) IN ('Tecnologia', 'Esportes', 'Economia')"
        params_sensa = tuple(f"%{p}%" for p in palavras_sensacionalistas)

    cursor.execute(sql_sensa, params_sensa)
    total_sensacionalista = cursor.fetchone()[0]

    # 5. Histórico de Delay (Últimas 20 notícias)
    cursor.execute(f"SELECT data_publicacao FROM noticias {filtro_sql} ORDER BY data_publicacao DESC LIMIT 20", params)
    recentes = cursor.fetchall()
    
    delays = []
    labels_delay = []
    for row in recentes:
        dt_pub = row[0]
        if dt_pub:
            diff = (datetime.utcnow() - dt_pub.replace(tzinfo=None)).total_seconds() / 3600
            delays.append(round(max(0, diff), 1))
            labels_delay.append(dt_pub.strftime("%H:%M"))

    frescor_medio = round(sum(delays)/len(delays), 1) if delays else 0
    historico_delay = {"labels": list(reversed(labels_delay)), "dados": list(reversed(delays))}

    # 6. Pico de Postagem (Relógio)
    cursor.execute(f"SELECT EXTRACT(HOUR FROM data_publicacao) FROM noticias {filtro_sql}", params)
    horas = [row[0] for row in cursor.fetchall()]
    
    relogio = {"manha": 0, "tarde": 0, "noite": 0, "madrugada": 0}
    for h in horas:
        if 6 <= h < 12: relogio["manha"] += 1
        elif 12 <= h < 18: relogio["tarde"] += 1
        elif 18 <= h < 24: relogio["noite"] += 1
        else: relogio["madrugada"] += 1

    # 7. Análise de Sentimento (Termômetro)
    palavras_pos = ['ganha', 'vence', 'lidera', 'sucesso', 'avanço', 'novo', 'cresce', 'tecnologia', 'ouro', 'campeão', 'lucro']
    palavras_neg = ['morre', 'crise', 'perde', 'queda', 'roubo', 'crime', 'inflação', 'alerta', 'perigo', 'cancela', 'derrota']
    
    or_pos = " OR ".join(["titulo ILIKE %s" for _ in palavras_pos])
    or_neg = " OR ".join(["titulo ILIKE %s" for _ in palavras_neg])
    
    if categoria != "Todas":
        cursor.execute(f"SELECT COUNT(*) FROM noticias WHERE ({or_pos}) AND TRIM(categoria) ILIKE %s", tuple(f"%{p}%" for p in palavras_pos) + (categoria,))
        pontos_pos = cursor.fetchone()[0]
        cursor.execute(f"SELECT COUNT(*) FROM noticias WHERE ({or_neg}) AND TRIM(categoria) ILIKE %s", tuple(f"%{p}%" for p in palavras_neg) + (categoria,))
        pontos_neg = cursor.fetchone()[0]
    else:
        cursor.execute(f"SELECT COUNT(*) FROM noticias WHERE ({or_pos}) AND TRIM(categoria) IN ('Tecnologia', 'Esportes', 'Economia')", tuple(f"%{p}%" for p in palavras_pos))
        pontos_pos = cursor.fetchone()[0]
        cursor.execute(f"SELECT COUNT(*) FROM noticias WHERE ({or_neg}) AND TRIM(categoria) IN ('Tecnologia', 'Esportes', 'Economia')", tuple(f"%{p}%" for p in palavras_neg))
        pontos_neg = cursor.fetchone()[0]

    total_sent = pontos_pos + pontos_neg
    score_pos = round((pontos_pos / total_sent * 100)) if total_sent > 0 else 50
    humor, cor = ("Positivo ☀️", "#4caf50") if score_pos >= 60 else (("Tenso ⛈️", "#f44336") if score_pos <= 40 else ("Misto ⛅", "#ff9800"))

    # 8. Top 5 Veículos (Fontes) - AQUI ESTAVA O ERRO DA SUA IMAGEM: Agora usando a variável filtro_sql declarada acima
    cursor.execute(f"SELECT fonte, COUNT(*) as qtd FROM noticias {filtro_sql} GROUP BY fonte ORDER BY qtd DESC LIMIT 5", params)
    top_fontes = [{"nome": row[0] or "Desconhecida", "quantidade": row[1]} for row in cursor.fetchall()]

    conn.close()
    
    return jsonify({
        "total": total_noticias,
        "cliques": int(total_acessos),
        "media_titulo": media_titulo,
        "frescor_medio": frescor_medio,
        "qualidade": {
            "img": round((com_img/total_noticias)*100, 1), 
            "desc": round((com_desc/total_noticias)*100, 1)
        },
        "sensacionalismo": round((total_sensacionalista/total_noticias)*100, 1),
        "sentimento": {"humor": humor, "cor": cor, "score_pos": score_pos},
        "relogio": relogio,
        "fontes": top_fontes,
        "historico_delay": historico_delay
    })

if __name__ == "__main__":
    app.run(debug=True)