import requests
import psycopg2
from apscheduler.schedulers.blocking import BlockingScheduler

API_KEY = "01634258ed9ced032658a8ed5bdc5de1"

def buscar_e_salvar():
    print("🔄 Buscando notícias...")

    url = f"https://gnews.io/api/v4/top-headlines?token={API_KEY}&lang=pt&max=10"
    res = requests.get(url)
    data = res.json()

    conn = psycopg2.connect("postgresql://postgres:C66236DBCc.@db.ruwagoepsujdemktrqno.supabase.co:5432/postgres")

    cursor = conn.cursor()

    for noticia in data["articles"]:
        try:
            cursor.execute("""
                INSERT INTO noticias (titulo, descricao, url, imagem, fonte, data_publicacao)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING
            """, (
                noticia["title"],
                noticia["description"],
                noticia["url"],
                noticia["image"],
                noticia["source"]["name"],
                noticia["publishedAt"]
            ))
        except:
            pass

    conn.commit()
    conn.close()

    print("✅ Atualização concluída!\n")


# ⏱️ Agenda a cada 90 minutos (1h30)
sched = BlockingScheduler()
sched.add_job(buscar_e_salvar, 'interval', minutes=90)

print("🚀 Bot automático iniciado...")
buscar_e_salvar()  # roda uma vez ao iniciar
sched.start()