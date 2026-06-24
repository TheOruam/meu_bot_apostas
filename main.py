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
    """Busca jogos do dia usando o endpoint do RapidAPI."""
    print("DEBUG: Iniciando busca de jogos no RapidAPI...")
    
    # URL DO RAPIDAPI (Obrigatório para sua assinatura)
    url_api = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    
    # Cabeçalhos CRUCIAIS para o RapidAPI
    headers = {
        'x-rapidapi-key': API_FOOTBALL_KEY,
        'x-rapidapi-host': "api-football-v1.p.rapidapi.com"
    }
    
    # Data de hoje
    hora_brt = datetime.utcnow() - timedelta(hours=3)
    data_hoje = hora_brt.strftime('%Y-%m-%d')
    params = {'date': data_hoje}
    
    try:
        resposta = requests.get(url_api, headers=headers, params=params, timeout=15)
        print(f"DEBUG: Status Code: {resposta.status_code}")
        
        if resposta.status_code != 200:
            print(f"DEBUG: Erro na API: {resposta.text}")
            enviar_telegram(f"⚠️ Erro na API: {resposta.status_code}")
            return

        jogos = resposta.json().get('response', [])
        
    except Exception as e:
        print(f"❌ Erro crítico ao conectar na API de Futebol: {e}")
        return

    # O resto do seu código (filtragem, análise, etc) continua aqui embaixo...
    # (Copie a lógica de filtragem que você já tem no seu arquivo original)

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
