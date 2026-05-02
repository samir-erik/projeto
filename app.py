from flask import Flask, jsonify, request
import psycopg2
from flask_cors import CORS
import os
import re

app = Flask(__name__)
CORS(app)

DB_URI = "postgresql://postgres.ruwagoepsujdemktrqno:C66236DBCc.@aws-1-us-east-1.pooler.supabase.com:6543/postgres"

def conectar():
    return psycopg2.connect(DB_URI)

# --- ROTAS DE NOTÍCIAS (Mantenha como estão) ---
@app.route("/noticias")
def noticias():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT titulo, descricao, url, imagem, categoria FROM noticias ORDER BY data_publicacao DESC")
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

# --- ROTA DE INTELIGÊNCIA DE DADOS (DASHBOARD ATUALIZADA) ---
@app.route("/dashboard")
def dashboard():
    # Captura a categoria do filtro (se não vier nada, usamos 'Todas') [cite: 557]
    categoria_filtro = request.args.get('categoria', 'Todas')
    
    conn = conectar()
    cursor = conn.cursor()
    
    # Base da Query: Filtro Dinâmico [cite: 557]
    if categoria_filtro == 'Todas':
        filtro_sql = ""
        params = ()
    else:
        filtro_sql = " WHERE TRIM(categoria) ILIKE %s "
        params = (categoria_filtro,)

    # 1. Estatísticas Gerais (Filtradas)
    cursor.execute(f"SELECT COUNT(*), SUM(COALESCE(acessos, 0)) FROM noticias {filtro_sql}", params)
    total_noticias, total_acessos = cursor.fetchone()

    # 2. Perfil Jornalístico (Tamanho Médio) [cite: 194]
    cursor.execute(f"SELECT ROUND(AVG(LENGTH(titulo)), 0) FROM noticias {filtro_sql}", params)
    media_titulo = int(cursor.fetchone()[0] or 0)

    # 3. Qualidade dos Dados (Completude) [cite: 196, 271]
    cursor.execute(f"""
        SELECT 
            SUM(CASE WHEN imagem IS NOT NULL AND imagem != '' THEN 1 ELSE 0 END),
            SUM(CASE WHEN descricao IS NOT NULL AND descricao != '' THEN 1 ELSE 0 END)
        FROM noticias {filtro_sql}
    """, params)
    com_img, com_desc = cursor.fetchone()
    pct_img = round((com_img / total_noticias * 100), 1) if total_noticias > 0 else 0
    pct_desc = round((com_desc / total_noticias * 100), 1) if total_noticias > 0 else 0

    # 4. AGILIDADE (Média Simplificada em Horas) [cite: 557, 561]
    cursor.execute(f"SELECT ROUND(AVG(EXTRACT(EPOCH FROM (NOW() - data_publicacao)) / 3600), 1) FROM noticias {filtro_sql}", params)
    frescor_medio = cursor.fetchone()[0] or 0

    # 5. SENSACIONALISMO (Análise de pontuação) [cite: 435, 437]
    cursor.execute(f"SELECT titulo FROM noticias {filtro_sql}", params)
    titulos = cursor.fetchall()
    total_sensacionalista = 0
    for (t,) in titulos:
        if "!" in t or "?" in t or t.isupper():
            total_sensacionalista += 1
    pct_sensacionalismo = round((total_sensacionalista / total_noticias * 100), 1) if total_noticias > 0 else 0

    # 6. ANÁLISE DE SENTIMENTO (Restaurando a lógica do Termômetro) [cite: 260, 261, 262]
    palavras_positivas = ["cresce", "alta", "cura", "vitória", "avanço", "sucesso", "ganha", "lucro", "paz"]
    palavras_negativas = ["crise", "queda", "morte", "alerta", "risco", "perde", "guerra", "medo", "inflação"]
    
    pontos_pos = 0
    pontos_neg = 0
    for (titulo,) in titulos:
        t_lower = titulo.lower()
        for p in palavras_positivas:
            if p in t_lower: pontos_pos += 1
        for n in palavras_negativas:
            if n in t_lower: pontos_neg += 1
    
    total_sent = pontos_pos + pontos_neg
    if total_sent == 0:
        humor, cor, score_pos = "Neutro ⚖️", "#9e9e9e", 50
    else:
        score_pos = round((pontos_pos / total_sent) * 100)
        if score_pos >= 60: humor, cor = "Positivo ☀️", "#4caf50"
        elif score_pos <= 40: humor, cor = "Tenso ⛈️", "#f44336"
        else: humor, cor = "Misto ⛅", "#ff9800"

    sentimento = {"humor": humor, "cor": cor, "score_pos": score_pos}

    conn.close()

    # Retorno unificado para o Dashboard [cite: 551]
    return jsonify({
        "total": total_noticias,
        "cliques": int(total_acessos or 0),
        "media_titulo": media_titulo,
        "frescor_medio": frescor_medio,
        "qualidade": {"img": pct_img, "desc": pct_desc},
        "sensacionalismo": pct_sensacionalismo,
        "sentimento": sentimento
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))