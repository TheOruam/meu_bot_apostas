import requests
from datetime import datetime
from deep_translator import GoogleTranslator

# Credenciais
TELEGRAM_TOKEN = '8983808854:AAH36YnSLE2ACY_1s5wSDhxQgCUbs66VzlA'
CHAT_ID = '747956770'
API_FOOTBALL_KEY = '418766ef4ec5450f1cab64d32229ddee'

def enviar_telegram(texto):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"})

def executar_analise():
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    jogos_resposta = requests.get("https://v3.football.api-sports.io/fixtures", 
                                  headers={'x-apisports-key': API_FOOTBALL_KEY}, 
                                  params={'date': data_hoje})
    
    jogos = jogos_resposta.json().get('response', [])
    jogos_pendentes = [j for j in jogos if j['fixture']['status']['short'] == 'NS']
    
    # Se não houver nada para analisar
    if not jogos_pendentes:
        enviar_telegram(f"✅ *Status Diário ({data_hoje}):*\nVarredura concluída. Nenhum jogo novo pendente para hoje.")
        return

    enviar_telegram(f"🚀 Iniciando análise de {len(jogos_pendentes)} jogos pendentes...")

    analisados = 0
    for jogo in jogos_pendentes:
        if analisados >= 50: break # Limite de segurança para não estourar a API
        
        id_jogo = jogo['fixture']['id']
        casa = jogo['teams']['home']['name']
        fora = jogo['teams']['away']['name']
        
        pred = requests.get("https://v3.football.api-sports.io/predictions", 
                            headers={'x-apisports-key': API_FOOTBALL_KEY}, 
                            params={'fixture': id_jogo}).json().get('response', [])
        
        if pred:
            p = pred[0]['predictions']['percent']
            try:
                home_p = int(p.get('home', '0').replace('%', ''))
                away_p = int(p.get('away', '0').replace('%', ''))
                maior_chance = max(home_p, away_p)
                
                if maior_chance >= 60:
                    sugestao = GoogleTranslator(source='en', target='pt').translate(pred[0]['predictions']['advice'])
                    texto = (f"🔥 *OPORTUNIDADE (+60%):*\n{casa} vs {fora}\n"
                             f"📈 Chance: {maior_chance}%\n"
                             f"💡 {sugestao}")
                    enviar_telegram(texto)
                analisados += 1
            except: continue

if __name__ == "__main__":
    executar_analise()
