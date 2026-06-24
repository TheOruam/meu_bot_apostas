import os
import requests
from datetime import datetime, timezone, timedelta
from google import genai
import config 

# --- Configurações ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Configura cliente Gemini apenas se a chave existir
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def enviar_telegram(texto):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("DEBUG: ERRO - Token ou Chat ID faltando nas variáveis de ambiente!")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("DEBUG: Mensagem enviada para o Telegram com sucesso!")
        else:
            print(f"DEBUG: ERRO NO TELEGRAM. Status: {response.status_code}, Resposta: {response.text}")
    except Exception as e:
        print(f"DEBUG: Erro ao conectar com Telegram: {e}")

def executar_analise():
    print("DEBUG: Iniciando busca de jogos na API...")
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    
    # Cabeçalhos obrigatórios para o RapidAPI
    headers = {
        "x-rapidapi-key": API_FOOTBALL_KEY,
        "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
    }
    params = {"date": data_hoje}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        print(f"DEBUG: Status Code da API: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            jogos = data.get('response', [])
            print(f"DEBUG: Jogos encontrados hoje: {len(jogos)}")
            enviar_telegram(f"✅ API funcionando! Encontrei {len(jogos)} jogos hoje.")
        else:
            print(f"DEBUG: Erro na API. Resposta completa: {response.text}")
            enviar_telegram(f"⚠️ Erro na API: {response.status_code}")
            
    except Exception as e:
        print(f"DEBUG: Ocorreu um erro na requisição: {e}")

if __name__ == "__main__":
    print("DEBUG: --- INICIANDO EXECUÇÃO ---")
    
    # Teste de Telegram sempre que o bot inicia
    enviar_telegram("🤖 O VAR do Lucro iniciou a verificação!")
    
    # Verificação de horário (considerando UTC-3)
    hora_atual = datetime.now(timezone.utc) - timedelta(hours=3)
    print(f"DEBUG: Hora atual no Brasil: {hora_atual.hour}h")

    if 5 <= hora_atual.hour < 21:
        print("DEBUG: Dentro do horário de análise.")
        executar_analise()
    else:
        print("DEBUG: Fora do horário (05h-21h). Bot em repouso.")
        enviar_telegram("💤 O VAR do Lucro está em repouso.")
