from flask import Flask, jsonify
import psycopg2
from flask_cors import CORS
import os
from collections import Counter
import re

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
    
    # 1. Estatísticas Gerais
    cursor.execute("SELECT COUNT(*), SUM(COALESCE(acessos, 0)) FROM noticias")
    total_noticias, total_acessos = cursor.fetchone()
    
    # 2. Volume por Categoria
    cursor.execute("SELECT categoria, COUNT(*) FROM noticias GROUP BY categoria")
    por_categoria = [
        {
            "categoria": d[0], 
            "quantidade": d[1],
            "percentual": round((d[1] / total_noticias) * 100, 1) if total_noticias > 0 else 0
        } for d in cursor.fetchall()
    ]
    
    # 3. Nuvem de Palavras
    cursor.execute("SELECT titulo FROM noticias")
    titulos = cursor.fetchall()
    stop_words = set(["o", "a", "os", "as", "de", "do", "da", "em", "um", "uma", "para", "com", "no", "na", "e", "é", "por", "mais", "que", "se", "foi", "ao", "das", "dos", "como", "sobre"])
    todas_palavras = []
    for (titulo,) in titulos:
        palavras = re.findall(r'\w+', titulo.lower())
        todas_palavras.extend([p for p in palavras if p not in stop_words and len(p) > 3])
    nuvem_frequencia = Counter(todas_palavras).most_common(15)
    nuvem_formatada = [{"palavra": p[0], "peso": p[1]} for p in nuvem_frequencia]
    
    # 4. Ranking Top 5
    cursor.execute("SELECT titulo, COALESCE(acessos, 0) as Cliques FROM noticias WHERE acessos > 0 ORDER BY acessos DESC LIMIT 5")
    ranking = [{"titulo": d[0], "acessos": d[1]} for d in cursor.fetchall()]

    # 5. Principais Fontes
    cursor.execute("SELECT fonte, COUNT(*) FROM noticias GROUP BY fonte ORDER BY COUNT(*) DESC LIMIT 6")
    por_fonte = [{"fonte": d[0], "quantidade": d[1]} for d in cursor.fetchall()]

    # 🚀 6. Perfil Jornalístico (Tamanho Médio do Título)
    cursor.execute("SELECT categoria, ROUND(AVG(LENGTH(titulo)), 0) FROM noticias GROUP BY categoria ORDER BY AVG(LENGTH(titulo)) DESC")
    tamanho_titulos = [{"categoria": d[0], "media_caracteres": int(d[1] or 0)} for d in cursor.fetchall()]

    # 🚀 7. Qualidade dos Dados da API (Completude)
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN imagem IS NULL OR imagem = 'None' OR imagem = '' THEN 1 ELSE 0 END) as sem_imagem,
            SUM(CASE WHEN descricao IS NULL OR descricao = 'None' OR descricao = '' THEN 1 ELSE 0 END) as sem_descricao
        FROM noticias
    """)
    q_total, sem_img, sem_desc = cursor.fetchone()
    
    pct_com_img = round(((q_total - (sem_img or 0)) / q_total) * 100, 1) if q_total > 0 else 0
    pct_com_desc = round(((q_total - (sem_desc or 0)) / q_total) * 100, 1) if q_total > 0 else 0
    
    qualidade_dados = {
        "com_imagem": pct_com_img,
        "com_descricao": pct_com_desc
    }

    # 🚀 8. Análise de Sentimento (Termômetro)
    palavras_positivas = ["cresce", "alta", "cura", "vitória", "avanço", "sucesso", "ganha", "aumenta", "recuperação", "esperança", "inovação", "lucro", "melhora", "investimento", "acordo", "paz"]
    palavras_negativas = ["crise", "queda", "morte", "alerta", "risco", "perde", "cai", "tensão", "guerra", "prejuízo", "crime", "violência", "medo", "inflação", "acidente", "erro", "ataque"]

    pontos_positivos = 0
    pontos_negativos = 0

    for (titulo,) in titulos: # Usa a mesma variável de títulos da Nuvem de Palavras
        titulo_min = titulo.lower()
        # Conta quantas palavras positivas e negativas aparecem
        for p in palavras_positivas:
            if p in titulo_min: pontos_positivos += 1
        for n in palavras_negativas:
            if n in titulo_min: pontos_negativos += 1

    total_sentimento = pontos_positivos + pontos_negativos
    if total_sentimento == 0:
        humor, cor, score_pos = "Neutro ⚖️", "#9e9e9e", 50
    else:
        score_pos = round((pontos_positivos / total_sentimento) * 100)
        if score_pos >= 60:
            humor, cor = "Positivo ☀️", "#4caf50"
        elif score_pos <= 40:
            humor, cor = "Tenso / Negativo ⛈️", "#f44336"
        else:
            humor, cor = "Misto ⛅", "#ff9800"

    sentimento = {
        "humor": humor, "cor": cor, "score_pos": score_pos, 
        "positivos": pontos_positivos, "negativos": pontos_negativos
    }

    # 🚀 9. Relógio das Notícias (Análise Temporal)
    cursor.execute("""
        SELECT EXTRACT(HOUR FROM data_publicacao), COUNT(*) 
        FROM noticias 
        GROUP BY EXTRACT(HOUR FROM data_publicacao)
    """)
    horas_dados = cursor.fetchall()

    periodos = {"Madrugada (00h-06h)": 0, "Manhã (06h-12h)": 0, "Tarde (12h-18h)": 0, "Noite (18h-00h)": 0}
    total_com_hora = 0
    
    for hora, qtd in horas_dados:
        if hora is None: continue
        h = int(hora)
        if 0 <= h < 6: periodos["Madrugada (00h-06h)"] += qtd
        elif 6 <= h < 12: periodos["Manhã (06h-12h)"] += qtd
        elif 12 <= h < 18: periodos["Tarde (12h-18h)"] += qtd
        else: periodos["Noite (18h-00h)"] += qtd
        total_com_hora += qtd

    relogio = [
        {"periodo": p, "quantidade": q, "percentual": round((q / total_com_hora) * 100) if total_com_hora > 0 else 0} 
        for p, q in periodos.items()
    ]

    # 🚀 10. Índice de Sensacionalismo (Clickbait Score)
    cursor.execute("SELECT titulo, categoria FROM noticias")
    titulos_categorias = cursor.fetchall()

    total_titulos_click = len(titulos_categorias)
    clickbait_count = 0
    cat_sensacionalista = {}

    for titulo, cat in titulos_categorias:
        if cat not in cat_sensacionalista:
            cat_sensacionalista[cat] = 0
            
        # Regra do Sensacionalismo: Tem "!" ou "?" ou uma palavra GRANDE TODA EM MAIÚSCULO
        tem_caixa_alta = any(palavra.isupper() and len(palavra) > 4 for palavra in titulo.split())
        
        if '!' in titulo or '?' in titulo or tem_caixa_alta:
            clickbait_count += 1
            cat_sensacionalista[cat] += 1

    pct_clickbait = round((clickbait_count / total_titulos_click) * 100, 1) if total_titulos_click > 0 else 0
    cat_campea = max(cat_sensacionalista, key=cat_sensacionalista.get) if clickbait_count > 0 else "N/A"

    sensacionalismo = {
        "percentual": pct_clickbait,
        "total_clickbait": clickbait_count,
        "categoria_lider": cat_campea
    }

    # 🚀 11. Latência do Robô (Frescor da Informação)
    # Calcula a idade média da notícia (diferença em horas entre a publicação original e agora)
    try:
        cursor.execute("SELECT ROUND(AVG(EXTRACT(EPOCH FROM (NOW() - data_publicacao))/3600), 1) FROM noticias WHERE data_publicacao IS NOT NULL")
        frescor_resultado = cursor.fetchone()[0]
        frescor_horas = float(frescor_resultado) if frescor_resultado else 0
    except:
        frescor_horas = 0 # Caso haja algum erro no formato da data
    
    conn.close()
    
    # Atualizando o retorno do JSON para incluir todas as métricas, incluindo o sentimento
    # Atualizando o retorno do JSON para incluir as novas métricas
    return jsonify({
        "estatisticas_gerais": {"total": total_noticias, "cliques_totais": int(total_acessos or 0)},
        "por_categoria": por_categoria,
        "ranking_top_5": ranking,
        "por_fonte": por_fonte,
        "tamanho_titulos": tamanho_titulos,
        "qualidade_dados": qualidade_dados,
        "sentimento": sentimento,
        "relogio": relogio,
        "sensacionalismo": sensacionalismo, # <-- NOVA
        "frescor_horas": frescor_horas      # <-- NOVA
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