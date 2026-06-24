import os
import requests
import google.generativeai as genai
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

# Configurações
TELEGRAM_TOKEN = '8983808854:AAH36YnSLE2ACY_1s5wSDhxQgCUbs66VzlA'
CHAT_ID = '747956770'
API_FOOTBALL_KEY = '418766ef4ec5450f1cab64d32229ddee'

# Configuração simples e direta
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

# Usamos o modelo generico padrão, o SDK vai detectar o disponível na sua conta
model = genai.GenerativeModel('gemini-1.5-flash')

LIGAS_PRIORITARIAS = [1, 71, 72, 73, 39, 140, 135, 78, 61, 2] 

def enviar_telegram(texto):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"})

def traduzir(texto):
    try: return GoogleTranslator(source='auto', target='pt').translate(texto)
    except: return texto

def analisar_com_ia(casa, fora, liga_nome):
    try:
        # Prompt simples para evitar erros de formatação
        prompt = f"Analise o jogo {casa} vs {fora} pela {liga_nome}. Sugira mercado e confiança."
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Erro na IA: {str(e)}"

def executar_analise():
    agora = datetime.utcnow()
    janela_limite = agora + timedelta(hours=8)
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    
    resposta = requests.get("https://v3.football.api-sports.io/fixtures", 
                            headers={'x-apisports-key': API_FOOTBALL_KEY}, 
                            params={'date': data_hoje})
    
    jogos = resposta.json().get('response', [])
    jogos_do_turno = [j for j in jogos if j['league']['id'] in LIGAS_PRIORITARIAS and 
                      j['fixture']['status']['short'] == 'NS' and 
                      agora <= datetime.strptime(j['fixture']['date'], '%Y-%m-%dT%H:%M:%S+00:00') <= janela_limite]

    if not jogos_do_turno:
        return

    for jogo in jogos_do_turno:
        casa = traduzir(jogo['teams']['home']['name'])
        fora = traduzir(jogo['teams']['away']['name'])
        liga = traduzir(jogo['league']['name'])
        
        analise = analisar_com_ia(casa, fora, liga)
        enviar_telegram(f"🔥 *ANÁLISE*\n{casa} vs {fora}\n\n{analise}")

if __name__ == "__main__":
    executar_analise()
