import requests
import psycopg2

# 🔑 SUA API (pode usar GNews ou outra)
API_KEY = "01634258ed9ced032658a8ed5bdc5de1"

# 🔥 COLOCA AQUI (logo no topo)
categorias_api = {
    "Tecnologia": "technology",
    "Esportes": "sports",
    "Economia": "business",
    "Geral": "general"
}   

conn = psycopg2.connect("postgresql://postgres.ruwagoepsujdemktrqno:C66236DBCc.@aws-1-us-east-1.pooler.supabase.com:5432/postgres")
cursor = conn.cursor()

# 📡 BUSCAR NOTÍCIAS
for nome_categoria, api_categoria in categorias_api.items():

    print(f"🔄 Buscando {nome_categoria}...")

    url = f"https://gnews.io/api/v4/top-headlines?category={api_categoria}&lang=pt&max=10&token={API_KEY}"

    res = requests.get(url)
    data = res.json()

    for noticia in data["articles"]:
        try:
            cursor.execute("""
                INSERT INTO noticias (titulo, descricao, url, imagem, fonte, data_publicacao, categoria)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING
            """, (
                noticia["title"],
                noticia["description"],
                noticia["url"],
                noticia["image"],
                noticia["source"]["name"],
                noticia["publishedAt"],
                nome_categoria
            ))
        except:
            pass

conn.commit()
conn.close()

print("✅ Notícias salvas com sucesso!")