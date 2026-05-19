import requests
import psycopg2

API_KEY = "4790c1898eba8d3924a5d675cbd54e06"
DB_URI = "postgresql://postgres.ruwagoepsujdemktrqno:C66236DBCc.@aws-1-us-east-1.pooler.supabase.com:6543/postgres"

CATEGORIAS = {
    "Tecnologia": "technology",
    "Esportes": "sports",
    "Economia": "business",
    "Geral": "general",
    "Saúde": "health",
    "Ciência": "science",
    "Entretenimento": "entertainment",
    "Mundo": "world",       
    "Brasil": "nation"      
}

def executar_rotina_coleta():
    print("🚀 Iniciando rotina integrada de coleta de notícias...")
    
    try:
        conn = psycopg2.connect(DB_URI)
        cursor = conn.cursor()
    except Exception as e:
        print(f"❌ Falha de conexão ao Banco de Dados: {e}")
        return

    for nome_categoria, api_categoria in CATEGORIAS.items():
        print(f"🔄 Solicitando dados da categoria: {nome_categoria}...")
        url = f"https://gnews.io/api/v4/top-headlines?category={api_categoria}&lang=pt&max=10&token={API_KEY}"
        
        try:
            res = requests.get(url)
            data = res.json()
            
            if "articles" not in data:
                print(f"⚠️ Resposta inválida da API para {nome_categoria}: {data}")
                continue

            for artigo in data["articles"]:
                cursor.execute("""
                    INSERT INTO noticias (titulo, descricao, url, imagem, fonte, data_publicacao, categoria, acessos)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 0)
                    ON CONFLICT (url) DO NOTHING
                """, (
                    artigo["title"], artigo["description"], artigo["url"],
                    artigo["image"], artigo["source"]["name"], artigo["publishedAt"],
                    nome_categoria
                ))
            conn.commit()
            print(f"✅ Categoria {nome_categoria} sincronizada com sucesso.")
            
        except Exception as err:
            print(f"❌ Erro durante o processamento da categoria {nome_categoria}: {err}")
            
    cursor.close()
    conn.close()
    print("🏁 Rotina de sincronização de notícias finalizada!")

if __name__ == "__main__":
    executar_rotina_coleta()