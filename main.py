import requests
from datetime import datetime

# 1. SUAS CREDENCIAIS REAIS
TELEGRAM_TOKEN = '8983808854:AAH36YnSLE2ACY_1s5wSDhxQgCUbs66VzlA'
CHAT_ID = '747956770'
API_FOOTBALL_KEY = '418766ef4ec5450f1cab64d32229ddee'

def enviar_telegram(texto):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"})

def executar_analise():
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    url_fixtures = "https://v3.football.api-sports.io/fixtures"
    headers_football = {'x-apisports-key': API_FOOTBALL_KEY}
    params_fixtures = {'date': data_hoje, 'season': '2026'}

    try:
        resp_fixtures = requests.get(url_fixtures, headers=headers_football, params=params_fixtures)
        jogos = resp_fixtures.json().get('response', [])

        if not jogos:
            # Agora ele avisa se não achar jogos, em vez de ficar mudo
            enviar_telegram(f"🤖 *Status de Hoje ({data_hoje}):*\nO robô rodou com sucesso, mas a API não retornou nenhum jogo disponível na temporada '2026' para análise.")
            return

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
                f"⚽ *Confronto:* {time_casa} vs {time_fora}\n"
                f"📅 *Data:* {data_hoje}\n\n"
                f"📈 *Probabilidades:*\n"
                f"🏠 Vitória Casa: {porcentagens.get('home')}\n"
                f"🤝 Empate: {porcentagens.get('draw')}\n"
                f"✈️ Vitória Fora: {porcentagens.get('away')}\n\n"
                f"💡 *Sugestão:* {dica_algoritmo}"
            )
            enviar_telegram(texto_analise)
            
    except Exception as e:
        # Se der erro de conexão, ele te avisa pelo Telegram também
        enviar_telegram(f"❌ *Erro no Robô:* Ocorreu uma falha na execução de hoje. Detalhe técnico: {e}")

if __name__ == "__main__":
    executar_analise()
