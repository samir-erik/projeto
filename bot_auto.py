import requests
import psycopg2
import os
from apscheduler.schedulers.blocking import BlockingScheduler

# Configurações
API_KEY = "01634258ed9ced032658a8ed5bdc5de1"
DB_URI = "postgresql://postgres.ruwagoepsujdemktrqno:C66236DBCc.@aws-1-us-east-1.pooler.supabase.com:5432/postgres"

categorias_api = {
    "Tecnologia": "technology",
    "Esportes": "sports",
    "Economia": "business",
    "Geral": "general"
}

def buscar_e_salvar():
    print("🔄 Iniciando ciclo de atualização...")
    
    try:
        conn = psycopg2.connect(DB_URI)
        cursor = conn.cursor()

        for nome_categoria, api_categoria in categorias_api.items():
            print(f"📡 Buscando {nome_categoria} na API...")
            url = f"https://gnews.io/api/v4/top-headlines?category={api_categoria}&lang=pt&max=5&token={API_KEY}"
            
            res = requests.get(url)
            data = res.json()

            if "articles" in data:
                for noticia in data["articles"]:
                    # Lógica de INSERT com a categoria correta
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
                        nome_categoria  # Agora o site vai conseguir filtrar!
                    ))
                print(f"✅ {nome_categoria} processada.")
            else:
                print(f"⚠️ Erro na API para {nome_categoria}: {data.get('errors', 'Erro desconhecido')}")

        conn.commit()
        cursor.close()
        conn.close()
        print("✨ Banco de dados atualizado com sucesso!\n")

    except Exception as e:
        print(f"❌ Erro crítico no bot: {e}")

# Agendador
scheduler = BlockingScheduler()
# Rodar imediatamente ao iniciar
buscar_e_salvar()
# Agendar para cada 30 minutos (Seguro para sua cota da API)
scheduler.add_job(buscar_e_salvar, 'interval', minutes=30)

if __name__ == '__main__':
    print("🤖 Bot de automação iniciado...")
    scheduler.start()