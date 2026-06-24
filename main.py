import requests
from datetime import datetime

# Credenciais
TELEGRAM_TOKEN = '8983808854:AAH36YnSLE2ACY_1s5wSDhxQgCUbs66VzlA'
CHAT_ID = '747956770'
API_FOOTBALL_KEY = '418766ef4ec5450f1cab64d32229ddee'

def enviar_telegram(texto):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"})

def executar_analise():
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    # Busca da API
    resposta = requests.get("https://v3.football.api-sports.io/fixtures", 
                         headers={'x-apisports-key': API_FOOTBALL_KEY}, 
                         params={'date': data_hoje})
    
    jogos = resposta.json().get('response', [])
    
    if not jogos:
        enviar_telegram("🤖 Nenhum jogo encontrado na API para hoje.")
        return

    # Contador para depuração
    jogos_nao_iniciados = [j for j in jogos if j['fixture']['status']['short'] == 'NS']
    
    if not jogos_nao_iniciados:
        enviar_telegram(f"🤖 Hoje houve {len(jogos)} jogos, mas todos já acabaram ou estão acontecendo agora. Nenhum jogo 'Not Started' para analisar.")
        return
    else:
        enviar_telegram(f"🔍 Encontrei {len(jogos_nao_iniciados)} jogos pendentes. Iniciando análise...")
        # ... (seu código de análise continua aqui)
