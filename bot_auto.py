import requests
import psycopg2
from apscheduler.schedulers.blocking import BlockingScheduler

API_KEY = "4790c1898eba8d3924a5d675cbd54e06"
DB_URI = "postgresql://postgres.ruwagoepsujdemktrqno:C66236DBCc.@aws-1-us-east-1.pooler.supabase.com:6543/postgres"

categorias_api = {
    "Tecnologia": "technology",
    "Esportes": "sports",
    "Economia": "business",
    "Geral": "general",
    "Saúde": "health",
    "Ciência": "science",
    "Entretenimento": "entertainment",
    "Mundo": "world",       # NOVA
    "Brasil": "nation"      # NOVA
}

def buscar_e_salvar():
    print("🔄 Iniciando ciclo de atualização...")
    try:
        conn = psycopg2.connect(DB_URI)
        cursor = conn.cursor()

        for nome_categoria, api_categoria in categorias_api.items():
            url = f"https://gnews.io/api/v4/top-headlines?category={api_categoria}&lang=pt&max=5&token={API_KEY}"
            res = requests.get(url)
            data = res.json()

            if "articles" in data:
                for noticia in data["articles"]:
                    cursor.execute("""
                        INSERT INTO noticias (titulo, descricao, url, imagem, fonte, data_publicacao, categoria, acessos)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, 0)
                        ON CONFLICT (url) DO NOTHING
                    """, (
                        noticia["title"], noticia["description"], noticia["url"],
                        noticia["image"], noticia["source"]["name"], noticia["publishedAt"],
                        nome_categoria
                    ))
                print(f"✅ {nome_categoria} processada.")
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✨ Banco de dados atualizado!")
    except Exception as e:
        print(f"❌ Erro no bot: {e}")

scheduler = BlockingScheduler()
scheduler.add_job(buscar_e_salvar, 'interval', minutes=30)

if __name__ == '__main__':
    buscar_e_salvar() # Roda uma vez ao iniciar
    scheduler.start()