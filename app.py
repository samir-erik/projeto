import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from contextlib import contextmanager

app = Flask(__name__)
CORS(app)

# String de conexão centralizada (Pooler do Supabase)
DB_URI = "postgresql://postgres.ruwagoepsujdemktrqno:C66236DBCc.@aws-1-us-east-1.pooler.supabase.com:6543/postgres"

@contextmanager
def obter_conexao():
    """Gerenciador de contexto para garantir que a conexão sempre feche."""
    conn = psycopg2.connect(DB_URI)
    try:
        yield conn
    finally:
        conn.close()

def executar_query(query, params=(), fechar_apos_ler=True):
    """Função utilitária para reduzir a repetição de blocos try/except/fetch nas rotas."""
    with obter_conexao() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            if fechar_apos_ler:
                return cursor.fetchall()
            conn.commit()

# --- ROTAS DE COMPORTAMENTO DO PORTAL ---

@app.route("/noticias")
def listar_todas_noticias():
    sql = "SELECT titulo, descricao, url, imagem, categoria FROM noticias ORDER BY data_publicacao DESC"
    dados = executar_query(sql)
    return jsonify([{"titulo": d[0], "descricao": d[1], "url": d[2], "imagem": d[3], "categoria": d[4]} for d in dados])

@app.route("/categoria/<categoria>")
def listar_por_categoria(categoria):
    sql = "SELECT titulo, descricao, url, imagem, categoria FROM noticias WHERE TRIM(categoria) ILIKE %s ORDER BY data_publicacao DESC"
    dados = executar_query(sql, (categoria,))
    return jsonify([{"titulo": d[0], "descricao": d[1], "url": d[2], "imagem": d[3], "categoria": d[4]} for d in dados])

@app.route("/buscar/<termo>")
def buscar_por_termo(termo):
    sql = "SELECT titulo, descricao, url, imagem, categoria FROM noticias WHERE titulo ILIKE %s OR descricao ILIKE %s ORDER BY data_publicacao DESC"
    termo_match = f"%{termo}%"
    dados = executar_query(sql, (termo_match, termo_match))
    return jsonify([{"titulo": d[0], "descricao": d[1], "url": d[2], "imagem": d[3], "categoria": d[4]} for d in dados])

@app.route("/data/<data_selecionada>")
def filtrar_por_data(data_selecionada):
    sql = "SELECT titulo, descricao, url, imagem, categoria FROM noticias WHERE DATE(data_publicacao) = %s ORDER BY data_publicacao DESC"
    dados = executar_query(sql, (data_selecionada,))
    return jsonify([{"titulo": d[0], "descricao": d[1], "url": d[2], "imagem": d[3], "categoria": d[4]} for d in dados])

@app.route("/datas_disponiveis")
def obter_datas_disponiveis():
    sql = "SELECT DISTINCT DATE(data_publicacao) FROM noticias ORDER BY DATE(data_publicacao) DESC"
    datas = [d[0].strftime("%Y-%m-%d") for d in executar_query(sql)]
    return jsonify(datas)

@app.route("/contar_acesso/<path:url>", methods=["POST"])
def registrar_clique_noticia(url):
    sql = "UPDATE noticias SET acessos = COALESCE(acessos, 0) + 1 WHERE url = %s"
    executar_query(sql, (url,), fechar_apos_ler=False)
    return jsonify({"status": "sucesso"})

# --- ROTA DE INTELIGÊNCIA DE DADOS (DASHBOARD) ---

@app.route("/dashboard")
def carregar_dados_dashboard():
    categoria_filtro = request.args.get('categoria', 'Todas')
    filtro_sql = "" if categoria_filtro == 'Todas' else " WHERE TRIM(categoria) ILIKE %s "
    params = () if categoria_filtro == 'Todas' else (categoria_filtro,)

    with obter_conexao() as conn:
        with conn.cursor() as cursor:
            # 1. Métricas Gerais
            cursor.execute(f"SELECT COUNT(*), SUM(COALESCE(acessos, 0)), ROUND(AVG(LENGTH(titulo)), 0) FROM noticias {filtro_sql}", params)
            total_noticias, total_acessos, media_titulo = cursor.fetchone()
            total_noticias = total_noticias or 0

            if total_noticias == 0:
                return jsonify({"total": 0, "fontes": [], "relogio": {}, "sentimento": {"humor": "Sem dados", "score_pos": 50}, "historico_delay": {"labels":[], "dados":[]}})

            # 2. Frescor Médio (Delay em horas)
            cursor.execute(f"SELECT ROUND(AVG(EXTRACT(EPOCH FROM (NOW() - data_publicacao)) / 3600), 1) FROM noticias {filtro_sql}", params)
            frescor_medio = cursor.fetchone()[0] or 0

            # 3. Análise Detalhada de Histórico, Sentimentos e Horários
            cursor.execute(f"SELECT titulo, data_publicacao, imagem, descricao, EXTRACT(EPOCH FROM (NOW() - data_publicacao)) / 3600 FROM noticias {filtro_sql} ORDER BY data_publicacao DESC", params)
            linhas = cursor.fetchall()

            # 4. Top 5 Veículos / Fontes
            cursor.execute(f"SELECT fonte, COUNT(*) as qtd FROM noticias {filtro_sql} GROUP BY fonte ORDER BY qtd DESC LIMIT 5", params)
            top_fontes = [{"nome": r[0] or "Desconhecida", "quantidade": r[1]} for r in cursor.fetchall()]

    # Processamento Inteligente dos Dados
    com_img = com_desc = total_sensacionalista = pontos_pos = pontos_neg = 0
    manha = tarde = noite = madruga = 0
    labels_delay, dados_delay = [], []

    palavras_pos = ["cresce", "alta", "cura", "vitória", "avanço", "sucesso", "ganha", "lucro", "paz"]
    palavras_neg = ["crise", "queda", "morte", "alerta", "risco", "perde", "guerra", "medo", "inflação"]

    for titulo, data, img, desc, delay in linhas:
        if img: com_img += 1
        if desc: com_desc += 1
        
        if titulo:
            if "!" in titulo or "?" in titulo or titulo.isupper():
                total_sensacionalista += 1
            
            t_low = titulo.lower()
            pontos_pos += sum(1 for p in palavras_pos if p in t_low)
            pontos_neg += sum(1 for n in palavras_neg if n in t_low)

            if delay is not None and len(dados_delay) < 30:
                labels_delay.append(titulo[:15] + "...")
                dados_delay.append(round(delay, 1))

        if data:
            hr = data.hour
            if 6 <= hr < 12: manha += 1
            elif 12 <= hr < 18: tarde += 1
            elif 18 <= hr < 24: noite += 1
            else: madruga += 1

    # Inversão para o gráfico ler cronologicamente da esquerda para a direita
    labels_delay.reverse()
    dados_delay.reverse()

    # Cálculo do Termômetro de Sentimento
    total_sent = pontos_pos + pontos_neg
    score_pos = round((pontos_pos / total_sent * 100)) if total_sent > 0 else 50
    
    if score_pos >= 60: humor, cor = "Positivo ☀️", "#4caf50"
    elif score_pos <= 40: humor, cor = "Tenso ⛈️", "#f44336"
    else: humor, cor = "Misto ⛅", "#ff9800"

    return jsonify({
        "total": total_noticias,
        "cliques": int(total_acessos or 0),
        "media_titulo": int(media_titulo or 0),
        "frescor_medio": frescor_medio,
        "qualidade": {"img": round((com_img/total_noticias)*100, 1), "desc": round((com_desc/total_noticias)*100, 1)},
        "sensacionalismo": round((total_sensacionalista/total_noticias)*100, 1),
        "sentimento": {"humor": humor, "cor": cor, "score_pos": score_pos},
        "relogio": {
            "manha": round((manha/total_noticias)*100, 1), "tarde": round((tarde/total_noticias)*100, 1),
            "noite": round((noite/total_noticias)*100, 1), "madrugada": round((madruga/total_noticias)*100, 1)
        },
        "fontes": top_fontes,
        "historico_delay": {"labels": labels_delay, "dados": dados_delay}
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))