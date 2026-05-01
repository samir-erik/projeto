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
    
    conn.close()
    
    # Atualizando o retorno do JSON para incluir as novas métricas
    return jsonify({
        "estatisticas_gerais": {"total": total_noticias, "cliques_totais": int(total_acessos or 0)},
        "por_categoria": por_categoria,
        "nuvem_palavras": nuvem_formatada,
        "ranking_top_5": ranking,
        "por_fonte": por_fonte,
        "tamanho_titulos": tamanho_titulos,
        "qualidade_dados": qualidade_dados
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