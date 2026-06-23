import requests
from datetime import datetime

# 1. SUAS CREDENCIAIS REAIS
TELEGRAM_TOKEN = '8983808854:AAH36YnSLE2ACY_1s5wSDhxQgCUbs66VzlA'
CHAT_ID = '747956770'
API_FOOTBALL_KEY = '418766ef4ec5450f1cab64d32229ddee'

def executar_analise():
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    url_fixtures = "https://v3.football.api-sports.io/fixtures"
    headers_football = {'x-apisports-key': API_FOOTBALL_KEY}
    params_fixtures = {'date': data_hoje, 'season': '2026'}

    print("Buscando jogos do dia...")
    try:
        resp_fixtures = requests.get(url_fixtures, headers=headers_football, params=params_fixtures)
        jogos = resp_fixtures.json().get('response', [])

        if not jogos:
            print("Nenhum jogo encontrado para hoje.")
            return

        # Analisa o primeiro jogo da lista
        primeiro_jogo = jogos[0]
        id_jogo = primeiro_jogo['fixture']['id']
        time_casa = primeiro_jogo['teams']['home']['name']
        time_fora = primeiro_jogo['teams']['away']['name']
        
        url_predictions = "https://v3.football.api-sports.io/predictions"
        resp_pred = requests.get(url_predictions, headers=headers_football, params={'fixture': id_jogo})
        previsao_dados = resp_pred.json().get('response', [])
        
        if previsao_dados:
            porcentagens = previsao_dados[0]['predictions']['percent']
            dica_algoritmo = previsao_dados[0]['predictions']['advice']
            
            texto_analise = (
                f"📊 *Nova Análise de Jogo*\n\n"
                f"⚽ *Confronto:* {time_casa} vs {time_fora}\n\n"
                f"📈 *Probabilidades:*\n"
                f"🏠 Vitória Casa: {porcentagens.get('home')}\n"
                f"🤝 Empate: {porcentagens.get('draw')}\n"
                f"✈️ Vitória Fora: {porcentagens.get('away')}\n\n"
                f"💡 *Sugestão:* {dica_algoritmo}"
            )

            url_telegram = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(url_telegram, json={"chat_id": CHAT_ID, "text": texto_analise, "parse_mode": "Markdown"})
            print("✅ Análise enviada para o Telegram!")
    except Exception as e:
        print(f"Erro durante a execução: {e}")

# Executa direto uma única vez
if __name__ == "__main__":
    executar_analise()
