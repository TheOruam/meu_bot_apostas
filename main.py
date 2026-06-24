import requests
from datetime import datetime
from deep_translator import GoogleTranslator

# Credenciais
TELEGRAM_TOKEN = '8983808854:AAH36YnSLE2ACY_1s5wSDhxQgCUbs66VzlA'
CHAT_ID = '747956770'
API_FOOTBALL_KEY = '418766ef4ec5450f1cab64d32229ddee'

LIGAS_PRIORITARIAS = [1, 71, 72, 73, 39, 140, 135, 78, 61, 2] 

def enviar_telegram(texto):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"})

def executar_analise():
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    resposta = requests.get("https://v3.football.api-sports.io/fixtures", 
                            headers={'x-apisports-key': API_FOOTBALL_KEY}, 
                            params={'date': data_hoje})
    
    jogos = resposta.json().get('response', [])
    jogos_filtrados = [j for j in jogos if j['league']['id'] in LIGAS_PRIORITARIAS and j['fixture']['status']['short'] == 'NS']
    
    if not jogos_filtrados:
        enviar_telegram("✅ Nenhum jogo das ligas monitoradas encontrado para hoje.")
        return

    enviar_telegram(f"🚀 Varredura: {len(jogos_filtrados)} jogos encontrados. Analisando...")

    for jogo in jogos_filtrados:
        id_jogo = jogo['fixture']['id']
        casa = jogo['teams']['home']['name']
        fora = jogo['teams']['away']['name']
        
        pred_resp = requests.get("https://v3.football.api-sports.io/predictions", 
                                 headers={'x-apisports-key': API_FOOTBALL_KEY}, 
                                 params={'fixture': id_jogo})
        
        pred = pred_resp.json().get('response', [])
        if pred:
            p = pred[0]['predictions']['percent']
            home_p = int(p.get('home', '0').replace('%', ''))
            away_p = int(p.get('away', '0').replace('%', ''))
            maior_chance = max(home_p, away_p)
            
            # Se for oportunidade, manda mensagem chamativa
            if maior_chance >= 60:
                sugestao = GoogleTranslator(source='en', target='pt').translate(pred[0]['predictions']['advice'])
                texto = (f"🔥 *OPORTUNIDADE (+60%):*\n{casa} vs {fora}\n"
                         f"📈 Chance: {maior_chance}%\n"
                         f"💡 {sugestao}")
                enviar_telegram(texto)
            else:
                # SE NÃO FOR OPORTUNIDADE, envia um resumo discreto apenas para você saber que o robô checou
                enviar_telegram(f"ℹ️ {casa} x {fora}: {maior_chance}% (Baixa chance)")

if __name__ == "__main__":
    executar_analise()
