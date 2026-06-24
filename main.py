import os
import requests
import random
from datetime import datetime, timedelta, timezone
from google import genai
import config 

print("DEBUG: Iniciando o script...")

# --- Configurações ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY')
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

# --- Funções definem-se ANTES de serem usadas ---
def enviar_telegram(texto, chat_id=CHAT_ID, reply_markup=None):
    if not TELEGRAM_TOKEN or not chat_id:
        print("Erro: Token ou Chat ID faltando!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": texto, "parse_mode": "Markdown", "reply_markup": reply_markup}
    requests.post(url, json=payload, timeout=10)

def checar_comandos_e_saudar():
    # ... (seu código de saudação) ...
    pass

def executar_analise():
    print("DEBUG: Iniciando busca de jogos na API...")
    
    # Adicione esse print logo após a chamada da API (onde você busca os dados)
    # Exemplo:
    # resposta = requests.get(url_da_api)
    # print(f"DEBUG: Resposta da API: {resposta.status_code}")
    
    # Se você tiver uma lista de jogos, adicione:
    # print(f"DEBUG: Quantidade de jogos encontrados: {len(lista_jogos)}")
    pass

# --- Fluxo Principal (Onde o bot começa) ---
if __name__ == "__main__":
    # Agora a função existe antes de ser chamada!
    enviar_telegram("🤖 O VAR do Lucro iniciou a verificação do sistema!")
    
    checar_comandos_e_saudar()
    
    hora_brt = datetime.now(timezone.utc) - timedelta(hours=3)
    if 5 <= hora_brt.hour < 21:
        executar_analise()
    else:
        enviar_telegram("💤 O VAR do Lucro está em repouso.")

print(f"DEBUG: Hora atual calculada: {hora_brt.hour}")

if 5 <= hora_brt.hour < 21:
    print("DEBUG: Entrou no intervalo de horário (05h-21h). Executando análise...")
    executar_analise()
else:
    print("DEBUG: Fora do intervalo de análise. Bot em repouso.")
    enviar_telegram("💤 O VAR do Lucro está em repouso (fora da janela de análise).")
