import requests
from datetime import datetime
from deep_translator import GoogleTranslator

# ==========================================
# 1. SUAS CREDENCIAIS REAIS
# ==========================================
TELEGRAM_TOKEN = '8983808854:AAH36YnSLE2ACY_1s5wSDhxQgCUbs66VzlA'
CHAT_ID = '747956770'
API_FOOTBALL_KEY = '418766ef4ec5450f1cab64d32229ddee'
ODDS_API_KEY = '36bc630c0d38794602877989fa78cd12'

def enviar_telegram(texto):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"})

def buscar_odds_bet365(time_casa, time_fora):
    url_odds = "https://api.the-odds-api.com/v4/sports/upcoming/odds/"
    params = {'apiKey': ODDS_API_KEY, 'regions': 'eu', 'markets': 'h2h', 'bookmakers': 'bet365'}
    try:
        resposta = requests.get(url_odds, params=params)
        dados_odds = resposta.json()
        for jogo in dados_odds:
            home_api = jogo.get('home_team', '').lower()
            if time_casa.lower() in home_api or home_api in time_casa.lower():
                for bookmaker in jogo.get('bookmakers', []):
                    if bookmaker.get('key') == 'bet365':
                        outcomes = bookmaker['markets'][0]['outcomes']
                        valores = {}
                        for o in outcomes:
                            if o['name'] == jogo['home_team']: valores['casa'] = o['price']
                            elif o['name'] == jogo['away_team']: valores['fora'] = o['price']
                            else: valores['empate'] = o['price']
                        return valores
    except Exception as e:
        print(f"Erro ao buscar odds de mercado: {e}")
    return None

def executar_analise():
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    url_fixtures = "https://v3.football.api-sports.io/fixtures"
    headers_football = {'x-apisports-key': API_FOOTBALL_KEY}
    params_fixtures = {'date': data_hoje}

    try:
        resp_fixtures = requests.get(url_fixtures, headers=headers_football, params=params_fixtures)
        jogos = resp_fixtures.json().get('response', [])

        if not jogos:
            enviar_telegram(f"🤖 *Status de Hoje ({data_hoje}):*\nO robô rodou com sucesso, mas nenhum jogo foi localizado.")
            return

        primeiro_jogo = jogos[0]
        id_jogo = primeiro_jogo['fixture']['id']
        time_casa = primeiro_jogo['teams']['home']['name']
        time_fora = primeiro_jogo['teams']['away']['name']
        
        odds_encontradas = buscar_odds_bet365(time_casa, time_fora)
        
        url_predictions = "https://v3.football.api-sports.io/predictions"
        resp_pred = requests.get(url_predictions, headers=headers_football, params={'fixture': id_jogo})
        previsao_dados = resp_pred.json().get('response', [])
        
        if previsao_dados:
            porcentagens = previsao_dados[0]['predictions']['percent']
            dica_algoritmo_ingles = previsao_dados[0]['predictions']['advice']
            
            # --- O TRADUTOR ENTRA AQUI ---
            try:
                dica_algoritmo = GoogleTranslator(source='en', target='pt').translate(dica_algoritmo_ingles)
            except:
                dica_algoritmo = dica_algoritmo_ingles # Mantém em inglês caso o tradutor falhe
            
            if odds_encontradas:
                bloco_odds = (
                    f"💰 *Cotações atuais na Bet365:*\n"
                    f"🏠 Vitória Casa (1): {odds_encontradas.get('casa', 'N/A')}\n"
                    f"🤝 Empate (X): {odds_encontradas.get('empate', 'N/A')}\n"
                    f"✈️ Vitória Fora (2): {odds_encontradas.get('fora', 'N/A')}\n\n"
                )
            else:
                bloco_odds = "💰 *Cotações Bet365:* Jogo não localizado no catálogo atual da API de odds.\n\n"
            
            texto_analise = (
                f"📊 *Nova Análise de Jogo*\n\n"
                f"⚽ *Confronto:* {time_casa} vs {time_fora}\n"
                f"📅 *Data:* {data_hoje}\n\n"
                f"📈 *Probabilidades do Algoritmo:*\n"
                f"🏠 Vitória Casa: {porcentagens.get('home')}\n"
                f"🤝 Empate: {porcentagens.get('draw')}\n"
                f"✈️ Vitória Fora: {porcentagens.get('away')}\n\n"
                f"{bloco_odds}"
                f"💡 *Sugestão:* {dica_algoritmo}"
            )
            enviar_telegram(texto_analise)
            
    except Exception as e:
        enviar_telegram(f"❌ *Erro no Robô:* Falha técnica durante o processamento: {e}")

if __name__ == "__main__":
    executar_analise()
