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

def buscar_odds_bet365(time_casa, time_fora):
    url_odds = "https://api.the-odds-api.com/v4/sports/upcoming/odds/"
    params = {'apiKey': ODDS_API_KEY, 'regions': 'eu', 'markets': 'h2h', 'bookmakers': 'bet365'}
    try:
        dados = requests.get(url_odds, params=params).json()
        for jogo in dados:
            if time_casa.lower() in jogo.get('home_team', '').lower():
                for book in jogo.get('bookmakers', []):
                    if book['key'] == 'bet365':
                        outcomes = {o['name']: o['price'] for o in book['markets'][0]['outcomes']}
                        return outcomes
    except: return None

def executar_analise():
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    # Busca todos os jogos do dia
    jogos = requests.get("https://v3.football.api-sports.io/fixtures", 
                         headers={'x-apisports-key': API_FOOTBALL_KEY}, 
                         params={'date': data_hoje}).json().get('response', [])

    if not jogos:
        enviar_telegram("🤖 Nenhum jogo encontrado para hoje.")
        return

    enviar_telegram(f"🚀 Iniciando varredura de {len(jogos)} jogos para hoje...")

    for jogo in jogos:
        # Filtra apenas jogos que ainda não começaram
        if jogo['fixture']['status']['short'] != 'NS':
            continue
            
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
            except: continue
            
            if maior_chance >= 60:
                odds = buscar_odds_bet365(casa, fora)
                sugestao = GoogleTranslator(source='en', target='pt').translate(pred[0]['predictions']['advice'])
                
                texto = (f"🔥 *OPORTUNIDADE (+60%):*\n{casa} vs {fora}\n"
                         f"📈 Chance: {maior_chance}%\n"
                         f"💰 Odd (Casa/Fora): {odds.get(casa, 'N/A')} / {odds.get(fora, 'N/A')}\n"
                         f"💡 {sugestao}")
                enviar_telegram(texto)
            else:
                # Opcional: Descomente a linha abaixo se quiser receber aviso de TODOS os jogos baixos
                # enviar_telegram(f"⚠️ {casa} x {fora}: {maior_chance}% (Baixa chance)")
                pass

if __name__ == "__main__":
    executar_analise()
