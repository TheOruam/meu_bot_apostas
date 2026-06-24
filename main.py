import requests
from datetime import datetime

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
    """Busca as cotações atuais na Bet365 para o confronto desejado"""
    # Buscamos os próximos jogos de futebol geral na API de Odds
    url_odds = "https://api.the-odds-api.com/v4/sports/upcoming/odds/"
    params = {
        'apiKey': ODDS_API_KEY,
        'regions': 'eu',      # Região padrão que engloba a Bet365 mundial
        'markets': 'h2h',     # Mercado de Resultado Final
        'bookmakers': 'bet365'
    }
    try:
        resposta = requests.get(url_odds, params=params)
        dados_odds = resposta.json()
        
        # Procura no banco de dados de odds o jogo que combine com os nossos times
        for jogo in dados_odds:
            home_api = jogo.get('home_team', '').lower()
            away_api = jogo.get('away_team', '').lower()
            
            # Verificação por proximidade de nome (evita problemas se um nome estiver abreviado)
            if time_casa.lower() in home_api or home_api in time_casa.lower():
                for bookmaker in jogo.get('bookmakers', []):
                    if bookmaker.get('key') == 'bet365':
                        outcomes = bookmaker['markets'][0]['outcomes']
                        
                        valores = {}
                        for o in outcomes:
                            if o['name'] == jogo['home_team']:
                                valores['casa'] = o['price']
                            elif o['name'] == jogo['away_team']:
                                valores['fora'] = o['price']
                            else:
                                valores['empate'] = o['price']
                        return valores
    except Exception as e:
        print(f"Erro ao buscar odds de mercado: {e}")
    return None

def executar_analise():
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    url_fixtures = "https://v3.football.api-sports.io/fixtures"
    headers_football = {'x-apisports-key': API_FOOTBALL_KEY}
    params_fixtures = {'date': data_hoje, 'season': '2026'}

    try:
        resp_fixtures = requests.get(url_fixtures, headers=headers_football, params=params_fixtures)
        jogos = resp_fixtures.json().get('response', [])

        if not jogos:
            enviar_telegram(f"🤖 *Status de Hoje ({data_hoje}):*\nO robô rodou com sucesso, mas nenhum jogo foi localizado para análise na temporada atual.")
            return

        # Pega o primeiro jogo do dia para a análise detalhada
        primeiro_jogo = jogos[0]
        id_jogo = primeiro_jogo['fixture']['id']
        time_casa = primeiro_jogo['teams']['home']['name']
        time_fora = primeiro_jogo['teams']['away']['name']
        
        # Executa a busca em paralelo da cotação de mercado
        odds_encontradas = buscar_odds_bet365(time_casa, time_fora)
        
        # Busca a previsão estatística do algoritmo
        url_predictions = "https://v3.football.api-sports.io/predictions"
        resp_pred = requests.get(url_predictions, headers=headers_football, params={'fixture': id_jogo})
        previsao_dados = resp_pred.json().get('response', [])
        
        if previsao_dados:
            porcentagens = previsao_dados[0]['predictions']['percent']
            dica_algoritmo = previsao_dados[0]['predictions']['advice']
            
            # Monta o bloco de texto das odds se elas forem encontradas
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
                f"📊 *Nova Análise de Jogo*\n\n
