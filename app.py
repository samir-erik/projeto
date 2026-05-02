from flask import Flask, jsonify
import psycopg2
from flask_cors import CORS
import os
import re

app = Flask(__name__)
CORS(app)

# Configurações de conexão (Centralizei aqui para facilitar a manutenção)
# Nota: Estou usando a porta 6543 para o Pooler do Supabase para evitar erros de conexão
DB_URI = "postgresql://postgres.ruwagoepsujdemktrqno:C66236DBCc.@aws-1-us-east-1.pooler.supabase.com:6543/postgres"

def conectar():
    """Cria uma nova conexão com o banco de dados PostgreSQL."""
    return psycopg2.connect(DB_URI)

# --- ROTAS DE NOTÍCIAS ---

@app.route("/noticias")
def noticias():
    """Retorna todas as notícias ordenadas pelas mais recentes."""
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
    """Filtra as notícias por categoria usando ILIKE para evitar problemas de case-sensitive."""
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

@app.route("/buscar/<termo>")
def buscar(termo):
    """Realiza a busca de termos nos títulos e descrições das notícias."""
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

@app.route("/contar_acesso/<path:url>", methods=["POST"])
def contar_acesso(url):
    """Incrementa o contador de cliques de uma notícia específica."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        # COALESCE evita erro caso o valor inicial seja NULL
        cursor.execute("UPDATE noticias SET acessos = COALESCE(acessos, 0) + 1 WHERE url = %s", (url,))
        conn.commit()
        conn.close()
        return jsonify({"status": "sucesso"})
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

# --- ROTA DE INTELIGÊNCIA DE DADOS (DASHBOARD) ---

@app.route("/dashboard")
def dashboard():
    """Gera todas as métricas analíticas do portal em uma única requisição."""
    conn = conectar()
    cursor = conn.cursor()
    
    # 1. Totais Gerais
    cursor.execute("SELECT COUNT(*), SUM(COALESCE(acessos, 0)) FROM noticias")
    total_noticias, total_acessos = cursor.fetchone()
    
    # 2. Ranking de Fontes (Portais que mais publicam)
    cursor.execute("SELECT fonte, COUNT(*) FROM noticias GROUP BY fonte ORDER BY COUNT(*) DESC LIMIT 6")
    por_fonte = [{"fonte": d[0], "quantidade": d[1]} for d in cursor.fetchall()]

    # 3. Análise Temporal (Relógio das Notícias)
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
    
    relogio = [
        {"periodo": p, "quantidade": q, "percentual": round((q/total_noticias)*100) if total_noticias > 0 else 0} 
        for p, q in periodos.items()
    ]

    # 4. Análise de Sentimento e Clickbait (Processamento de Texto)
    cursor.execute("SELECT titulo, categoria FROM noticias")
    titulos_raw = cursor.fetchall()
    
    # Dicionários de palavras para NLP simples
    p_pos = ["cresce", "alta", "vitoria", "avanco", "sucesso", "ganha", "paz", "cura", "melhora"]
    p_neg = ["crise", "queda", "morte", "alerta", "risco", "guerra", "ataque", "tenso", "perda"]
    
    s_pos, s_neg, click_count = 0, 0, 0
    cat_click = {}

    for tit, cat in titulos_raw:
        t_low = tit.lower()
        # Verificação de sentimento
        for p in p_pos: 
            if p in t_low: s_pos += 1
        for n in p_neg: 
            if n in t_low: s_neg += 1
        
        # Lógica de Sensacionalismo (Clickbait): Pontos de exclamação ou caixa alta
        tem_caixa_alta = any(w.isupper() and len(w) > 4 for w in tit.split())
        if '!' in tit or '?' in tit or tem_caixa_alta:
            click_count += 1
            cat_click[cat] = cat_click.get(cat, 0) + 1

    # Cálculo do Humor do Portal
    total_s = s_pos + s_neg
    score = round((s_pos / total_s) * 100) if total_s > 0 else 50
    humor = "Positivo ☀️" if score >= 60 else ("Negativo ⛈️" if score <= 40 else "Misto ⛅")
    cor = "#4caf50" if score >= 60 else ("#f44336" if score <= 40 else "#ff9800")

    # 5. Desempenho do Robô (Frescor da Informação)
    cursor.execute("SELECT ROUND(AVG(EXTRACT(EPOCH FROM (NOW() - data_publicacao))/3600), 1) FROM noticias")
    frescor = float(cursor.fetchone()[0] or 0)
    
    # 6. Top 5 Notícias (Ranking de Cliques)
    cursor.execute("SELECT titulo, COALESCE(acessos, 0) FROM noticias ORDER BY acessos DESC LIMIT 5")
    ranking = [{"titulo": d[0], "acessos": d[1]} for d in cursor.fetchall()]

    conn.close()

    # Resposta consolidada para o Front-end
    return jsonify({
        "estatisticas_gerais": {"total": total_noticias, "cliques_totais": int(total_acessos or 0)},
        "por_fonte": por_fonte,
        "relogio": relogio,
        "frescor_horas": frescor,
        "ranking_top_5": ranking,
        "sentimento": {
            "humor": humor, 
            "cor": cor, 
            "score_pos": score, 
            "positivos": s_pos, 
            "negativos": s_neg
        },
        "sensacionalismo": {
            "percentual": round((click_count/total_noticias)*100, 1) if total_noticias > 0 else 0,
            "categoria_lider": max(cat_click, key=cat_click.get) if cat_click else "N/A"
        }
    })

if __name__ == '__main__':
    # Configuração da porta para rodar no Render ou Localmente
    porta = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=porta)