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
    """Cria uma nova conexão com o banco de dados PostgreSQL."""
    return psycopg2.connect(DB_URI)

# --- ROTAS DE NOTÍCIAS ---

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

@app.route("/buscar/<termo>")
def buscar(termo):
    conn = conectar()
    cursor = conn.cursor()
    valor = f"%{termo}%"
    cursor.execute("SELECT titulo, descricao, url, imagem, categoria FROM noticias WHERE titulo ILIKE %s OR descricao ILIKE %s ORDER BY data_publicacao DESC", (valor, valor))
    dados = cursor.fetchall()
    conn.close()
    return jsonify([{"titulo": d[0], "descricao": d[1], "url": d[2], "imagem": d[3], "categoria": d[4]} for d in dados])

@app.route("/contar_acesso/<path:url>", methods=["POST"])
def contar_acesso(url):
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("UPDATE noticias SET acessos = COALESCE(acessos, 0) + 1 WHERE url = %s", (url,))
        conn.commit()
        conn.close()
        return jsonify({"status": "sucesso"})
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

# --- ROTA DE INTELIGÊNCIA DE DADOS (DASHBOARD) ---

@app.route("/dashboard")
def dashboard():
    categoria_filtro = request.args.get('categoria', 'Todas')
    conn = conectar()
    cursor = conn.cursor()
    
    # Filtro Dinâmico
    if categoria_filtro == 'Todas':
        filtro_sql = ""
        params = ()
    else:
        filtro_sql = " WHERE TRIM(categoria) ILIKE %s "
        params = (categoria_filtro,)

    # 1. Estatísticas Gerais
    cursor.execute(f"SELECT COUNT(*), SUM(COALESCE(acessos, 0)) FROM noticias {filtro_sql}", params)
    resultado_geral = cursor.fetchone()
    total_noticias = resultado_geral[0] or 0
    total_acessos = resultado_geral[1] or 0

    # Se não houver notícias (banco vazio para a categoria), retorna dados zerados
    if total_noticias == 0:
        conn.close()
        return jsonify({
            "total": 0, "cliques": 0, "media_titulo": 0, "frescor_medio": 0,
            "qualidade": {"img": 0, "desc": 0}, "sensacionalismo": 0,
            "sentimento": {"humor": "Sem Dados", "cor": "#9e9e9e", "score_pos": 50},
            "relogio": {"manha": 0, "tarde": 0, "noite": 0, "madrugada": 0}
        })

    # 2. Cálculos de Médias Seguros
    cursor.execute(f"SELECT ROUND(AVG(LENGTH(titulo)), 0) FROM noticias {filtro_sql}", params)
    media_titulo = int(cursor.fetchone()[0] or 0)

    cursor.execute(f"SELECT ROUND(AVG(EXTRACT(EPOCH FROM (NOW() - data_publicacao)) / 3600), 1) FROM noticias {filtro_sql}", params)
    frescor_medio = cursor.fetchone()[0] or 0

    # 3. Processamento de Texto e Datas
    cursor.execute(f"SELECT titulo, data_publicacao, imagem, descricao FROM noticias {filtro_sql}", params)
    rows = cursor.fetchall()

    total_sensacionalista = 0
    pontos_pos = pontos_neg = manha = tarde = noite = madruga = com_img = com_desc = 0
    palavras_pos = ["cresce", "alta", "cura", "vitória", "avanço", "sucesso", "ganha", "lucro", "paz"]
    palavras_neg = ["crise", "queda", "morte", "alerta", "risco", "perde", "guerra", "medo", "inflação"]

    for titulo, data, img, desc in rows:
        # Qualidade
        if img: com_img += 1
        if desc: com_desc += 1
        
        # Sensacionalismo e Sentimento (Apenas se houver título)
        if titulo:
            if "!" in titulo or "?" in titulo or titulo.isupper(): 
                total_sensacionalista += 1
                
            t_low = titulo.lower()
            for p in palavras_pos: 
                if p in t_low: pontos_pos += 1
            for n in palavras_neg: 
                if n in t_low: pontos_neg += 1
                
        # Relógio (Garante que a extração da hora funcione)
        if data:
            try:
                hr = data.hour
            except AttributeError:
                # Fallback caso venha como string
                try:
                    hr = int(str(data)[11:13])
                except:
                    hr = 12
            
            if 6 <= hr < 12: manha += 1
            elif 12 <= hr < 18: tarde += 1
            elif 18 <= hr < 24: noite += 1
            else: madruga += 1

    # Cálculos finais
    total_sent = pontos_pos + pontos_neg
    score_pos = round((pontos_pos / total_sent * 100)) if total_sent > 0 else 50
    humor, cor = ("Positivo ☀️", "#4caf50") if score_pos >= 60 else (("Tenso ⛈️", "#f44336") if score_pos <= 40 else ("Misto ⛅", "#ff9800"))

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
        "relogio": {
            "manha": round((manha/total_noticias)*100, 1), 
            "tarde": round((tarde/total_noticias)*100, 1),
            "noite": round((noite/total_noticias)*100, 1), 
            "madrugada": round((madruga/total_noticias)*100, 1)
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))