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
    # Busca a lista de jogos
    jogos_resposta = requests.get("https://v3.football.api-sports.io/fixtures", 
                                  headers={'x-apisports-key': API_FOOTBALL_KEY}, 
                                  params={'date': data_hoje})
    
    if jogos_resposta.status_code != 200:
        enviar_telegram("❌ Erro ao buscar lista de jogos.")
        return

    jogos = jogos_resposta.json().get('response', [])
    jogos_pendentes = [j for j in jogos if j['fixture']['status']['short'] == 'NS']
    
    if not jogos_pendentes:
        enviar_telegram(f"✅ Varredura concluída. Nenhum jogo pendente.")
        return

    enviar_telegram(f"🚀 Iniciando análise (limite de 90 jogos)...")

    analisados = 0
    for jogo in jogos_pendentes:
        if analisados >= 90: 
            enviar_telegram("⚠️ Limite diário de 90 análises atingido para economizar a API.")
            break
        
        id_jogo = jogo['fixture']['id']
        casa = jogo['teams']['home']['name']
        fora = jogo['teams']['away']['name']
        
        # Consulta de previsão
        pred_resp = requests.get("https://v3.football.api-sports.io/predictions", 
                                 headers={'x-apisports-key': API_FOOTBALL_KEY}, 
                                 params={'fixture': id_jogo})
        
        if pred_resp.status_code == 429: # Erro de excesso de chamadas
            enviar_telegram("❌ API Bloqueou: Limite de requisições diárias atingido.")
            break
            
        pred = pred_resp.json().get('response', [])
        
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
