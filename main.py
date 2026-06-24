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
    """Busca jogos do dia usando a conexão DIRETA da API-Sports."""
    print("DEBUG: Iniciando busca de jogos (Conexão Direta API-Sports)...")
    
    # URL DIRETA (A que estava funcionando ontem)
    url_api = "https://v3.football.api-sports.io/fixtures"
    
    # CABEÇALHO DIRETO (Atenção ao nome: x-apisports-key)
    headers = {
        'x-apisports-key': API_FOOTBALL_KEY
    }
    
    # Data de hoje
    hora_utc = datetime.utcnow()
    hora_brt = hora_utc - timedelta(hours=3)
    data_hoje = hora_brt.strftime('%Y-%m-%d')
    params = {'date': data_hoje}
    
    try:
        resposta = requests.get(url_api, headers=headers, params=params, timeout=15)
        print(f"DEBUG: Status Code da API: {resposta.status_code}")
        
        if resposta.status_code == 200:
            jogos = resposta.json().get('response', [])
            print(f"DEBUG: SUCESSO! A API retornou {len(jogos)} jogos no total.")
            enviar_telegram(f"✅ Conexão restabelecida! A API encontrou {len(jogos)} jogos.")
        else:
            print(f"DEBUG: Erro na API: {resposta.text}")
            enviar_telegram(f"⚠️ Erro na API: {resposta.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Erro crítico ao conectar na API de Futebol: {e}")
        return

    # --- AQUI COMEÇA O SEU CÓDIGO DE FILTRAGEM (Pode manter o seu igual) ---
    print("DEBUG: Iniciando filtro de ligas e horários...")
    # (resto do código...)

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
