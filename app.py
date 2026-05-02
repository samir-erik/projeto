from flask import Flask, jsonify
import psycopg2
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Configurações de conexão (Pooler do Supabase para estabilidade)[cite: 10]
DB_URI = "postgresql://postgres.ruwagoepsujdemktrqno:C66236DBCc.@aws-1-us-east-1.pooler.supabase.com:6543/postgres"

def conectar():
    """Cria uma nova conexão com o banco de dados PostgreSQL."""
    return psycopg2.connect(DB_URI)

# --- ROTAS DE NOTÍCIAS ---[cite: 1, 10]

@app.route("/noticias")
def noticias():
    """Retorna as notícias ordenadas pelas mais recentes."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT titulo, descricao, url, imagem, categoria FROM noticias ORDER BY data_publicacao DESC")
    dados = cursor.fetchall()
    conn.close()
    return jsonify([{"titulo": d[0], "descricao": d[1], "url": d[2], "imagem": d[3], "categoria": d[4]} for d in dados])

@app.route("/categoria/<categoria>")
def categoria_rota(categoria):
    """Filtra as notícias por categoria."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT titulo, descricao, url, imagem, categoria FROM noticias WHERE TRIM(categoria) ILIKE %s ORDER BY data_publicacao DESC", (categoria,))
    dados = cursor.fetchall()
    conn.close()
    return jsonify([{"titulo": d[0], "descricao": d[1], "url": d[2], "imagem": d[3], "categoria": d[4]} for d in dados])

@app.route("/buscar/<termo>")
def buscar(termo):
    """Busca termos nos títulos e descrições."""
    conn = conectar()
    cursor = conn.cursor()
    valor = f"%{termo}%"
    cursor.execute("SELECT titulo, descricao, url, imagem, categoria FROM noticias WHERE titulo ILIKE %s OR descricao ILIKE %s ORDER BY data_publicacao DESC", (valor, valor))
    dados = cursor.fetchall()
    conn.close()
    return jsonify([{"titulo": d[0], "descricao": d[1], "url": d[2], "imagem": d[3], "categoria": d[4]} for d in dados])

@app.route("/contar_acesso/<path:url>", methods=["POST"])
def contar_acesso(url):
    """Incrementa o contador de cliques."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("UPDATE noticias SET acessos = COALESCE(acessos, 0) + 1 WHERE url = %s", (url,))
        conn.commit()
        conn.close()
        return jsonify({"status": "sucesso"})
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

# --- ROTA DE INTELIGÊNCIA DE DADOS (DASHBOARD) ---[cite: 1, 10]

@app.route("/dashboard")
def dashboard():
    """Gera todas as métricas analíticas em uma única requisição."""
    conn = conectar()
    cursor = conn.cursor()
    
    # 1. Totais Gerais[cite: 10]
    cursor.execute("SELECT COUNT(*), SUM(COALESCE(acessos, 0)) FROM noticias")
    total_noticias, total_acessos = cursor.fetchone()
    
    # 2. Ranking de Fontes[cite: 10]
    cursor.execute("SELECT fonte, COUNT(*) FROM noticias GROUP BY fonte ORDER BY COUNT(*) DESC LIMIT 6")
    por_fonte = [{"fonte": d[0], "quantidade": d[1]} for d in cursor.fetchall()]

    # 3. Análise Temporal (Relógio)[cite: 10]
    cursor.execute("SELECT EXTRACT(HOUR FROM data_publicacao), COUNT(*) FROM noticias GROUP BY 1")
    horas_dados = cursor.fetchall()
    periodos = {"Madrugada (00h-06h)": 0, "Manhã (06h-12h)": 0, "Tarde (12h-18h)": 0, "Noite (18h-00h)": 0}
    for h_raw, qtd in horas_dados:
        if h_raw is None: continue
        h = int(h_raw)
        if 0 <= h < 6: periodos["Madrugada (00h-06h)"] += qtd
        elif 6 <= h < 12: periodos["Manhã (06h-12h)"] += qtd
        elif 12 <= h < 18: periodos["Tarde (12h-18h)"] += qtd
        else: periodos["Noite (18h-00h)"] += qtd
    relogio = [{"periodo": p, "percentual": round((q/total_noticias)*100) if total_noticias > 0 else 0} for p, q in periodos.items()]

    # 4. Sentimento e Clickbait (NLP simples)[cite: 10]
    cursor.execute("SELECT titulo, categoria FROM noticias")
    titulos_raw = cursor.fetchall()
    p_pos, p_neg = ["alta", "vitoria", "sucesso", "ganha"], ["crise", "queda", "alerta", "risco"]
    s_pos, s_neg, click_count, cat_click = 0, 0, 0, {}

    for tit, cat in titulos_raw:
        t_low = tit.lower()
        for p in p_pos: s_pos += 1 if p in t_low else 0
        for n in p_neg: s_neg += 1 if n in t_low else 0
        if '!' in tit or '?' in tit or any(w.isupper() and len(w) > 4 for w in tit.split()):
            click_count += 1
            cat_click[cat] = cat_click.get(cat, 0) + 1

    score = round((s_pos / (s_pos + s_neg)) * 100) if (s_pos + s_neg) > 0 else 50
    humor = "Positivo ☀️" if score >= 60 else ("Negativo ⛈️" if score <= 40 else "Misto ⛅")
    cor = "#4caf50" if score >= 60 else ("#f44336" if score <= 40 else "#ff9800")

    # 5. Ranking e Frescor[cite: 10]
    cursor.execute("SELECT ROUND(AVG(EXTRACT(EPOCH FROM (NOW() - data_publicacao))/3600), 1) FROM noticias")
    frescor = float(cursor.fetchone()[0] or 0)
    cursor.execute("SELECT titulo, COALESCE(acessos, 0) FROM noticias ORDER BY acessos DESC LIMIT 5")
    ranking = [{"titulo": d[0], "acessos": d[1]} for d in cursor.fetchall()]

    # 🚀 6. Algoritmo de Relevância (Escolha da IA)[cite: 1, 10]
    cursor.execute("""
        SELECT titulo, url, categoria, COALESCE(acessos, 0), 
               (COALESCE(acessos, 0) * 1.5) + (CASE WHEN titulo ILIKE '%!%' OR titulo ILIKE '%?%' THEN 50 ELSE 0 END) as score
        FROM noticias ORDER BY score DESC LIMIT 1
    """)
    d = cursor.fetchone()
    noticia_destaque = {"titulo": d[0], "url": d[1], "motivo": "Alto engajamento e apelo visual."} if d else {}

    # 🚀 7. Eficiência e Velocidade[cite: 10]
    cursor.execute("SELECT categoria, ROUND(AVG(COALESCE(acessos, 0)), 1) FROM noticias GROUP BY categoria ORDER BY 2 DESC")
    eficiencia = [{"categoria": d[0], "media": float(d[1])} for d in cursor.fetchall()]
    cursor.execute("SELECT fonte, ROUND(AVG(EXTRACT(EPOCH FROM (NOW() - data_publicacao))/3600), 1) FROM noticias GROUP BY fonte ORDER BY 2 ASC")
    velocidade = [{"fonte": d[0], "latencia": float(d[1])} for d in cursor.fetchall()]

    conn.close()
    return jsonify({
        "estatisticas_gerais": {"total": total_noticias, "cliques_totais": int(total_acessos or 0)},
        "por_fonte": por_fonte, "relogio": relogio, "frescor_horas": frescor, "ranking_top_5": ranking,
        "noticia_destaque": noticia_destaque, "eficiencia_categoria": eficiencia, "velocidade_fontes": velocidade,
        "sentimento": {"humor": humor, "cor": cor, "score_pos": score},
        "sensacionalismo": {"percentual": round((click_count/total_noticias)*100, 1) if total_noticias > 0 else 0, "categoria_lider": max(cat_click, key=cat_click.get) if cat_click else "N/A"}
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))