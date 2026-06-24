import os
import requests
from datetime import datetime, timezone, timedelta
from google import genai
import config 

# --- Configurações ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY')
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

def enviar_telegram(texto):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Erro: Token ou Chat ID faltando!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

def executar_analise():
    print("DEBUG: Iniciando busca de jogos na API...")
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    # Busca jogos de hoje
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    headers = {"x-rapidapi-key": API_FOOTBALL_KEY}
    params = {"date": data_hoje}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        print(f"DEBUG: Status Code da API: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            jogos = data.get('response', [])
            print(f"DEBUG: Quantidade total de jogos retornados pela API: {len(jogos)}")
            
            # Aqui entraria a sua lógica de filtrar ligas (ex: usando config.LIGAS_ATIVAS)
            if len(jogos) > 0:
                print("DEBUG: Sucesso! Jogos encontrados.")
                enviar_telegram(f"⚽ O sistema encontrou {len(jogos)} jogos hoje!")
            else:
                print("DEBUG: Nenhum jogo encontrado para hoje.")
        else:
            print(f"DEBUG: Erro na API. Resposta: {response.text}")
            
    except Exception as e:
        print(f"DEBUG: Ocorreu um erro na requisição: {e}")

if __name__ == "__main__":
    print("DEBUG: Iniciando o script...")
    
    # Validação de Horário
    hora_brt = datetime.now(timezone.utc) - timedelta(hours=3)
    print(f"DEBUG: Hora atual calculada: {hora_brt.hour}h")

    if 5 <= hora_brt.hour < 21:
        print("DEBUG: Entrou no intervalo de horário (05h-21h). Executando análise...")
        executar_analise()
    else:
        print("DEBUG: Fora do intervalo de análise. Bot em repouso.")
        enviar_telegram("💤 O VAR do Lucro está em repouso (fora da janela de análise).")
