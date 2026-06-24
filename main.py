import requests
from datetime import datetime
from deep_translator import GoogleTranslator

# Credenciais
TELEGRAM_TOKEN = '8983808854:AAH36YnSLE2ACY_1s5wSDhxQgCUbs66VzlA'
CHAT_ID = '747956770'
API_FOOTBALL_KEY = '418766ef4ec5450f1cab64d32229ddee'
ODDS_API_KEY = '36bc630c0d38794602877989fa78cd12'

def enviar_telegram(texto):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"})

def executar_analise():
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    # Ajuste: Apenas os 80 primeiros jogos para garantir que não estouraremos os 100 créditos da API
    jogos = requests.get("https://v3.football.api-sports.io/fixtures", 
                         headers={'x-apisports-key': API_FOOTBALL_KEY}, 
                         params={'date': data_hoje}).json().get('response', [])

    if not jogos:
        enviar_telegram("🤖 Nenhum jogo encontrado.")
        return

    enviar_telegram(f"🚀 Iniciando varredura otimizada (limite de 80 jogos)...")

    # Contador para não estourar os 100 créditos da API
    contador = 0
    for jogo in jogos:
        if contador >= 80: break # Para de processar para economizar créditos
        
        if jogo['fixture']['status']['short'] != 'NS': continue
            
        id_jogo = jogo['fixture']['id']
        casa = jogo['teams']['home']['name']
        fora = jogo['teams']['away']['name']
        
        pred = requests.get("https://v3.football.api-sports.io/predictions", 
                            headers={'x-apisports-key': API_FOOTBALL_KEY}, 
                            params={'fixture': id_jogo}).json().get('response', [])
        
        contador += 1 # Conta a requisição de previsão usada
        
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
            except: continue

if __name__ == "__main__":
    executar_analise()
