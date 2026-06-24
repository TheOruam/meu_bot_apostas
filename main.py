import os
import requests
import google.generativeai as genai
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

# Configurações
TELEGRAM_TOKEN = '8983808854:AAH36YnSLE2ACY_1s5wSDhxQgCUbs66VzlA'
CHAT_ID = '747956770'
API_FOOTBALL_KEY = '418766ef4ec5450f1cab64d32229ddee'

# Configuração Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

LIGAS_PRIORITARIAS = [1, 71, 72, 73, 39, 140, 135, 78, 61, 2] 

def enviar_telegram(texto):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"})

def traduzir(texto):
    try: return GoogleTranslator(source='auto', target='pt').translate(texto)
    except: return texto

def analisar_com_ia_e_dados(jogo_dados, liga_nome):
    casa = jogo_dados['teams']['home']['name']
    fora = jogo_dados['teams']['away']['name']
    
    prompt = f"""
    Você é um analista de apostas esportivas de elite. Seu objetivo é identificar 'Value Bets' (apostas de valor) no confronto: {casa} vs {fora} ({liga_nome}).
    
    ETAPA 1: INVESTIGAÇÃO
    - Acesse dados reais sobre lesões, escalações, clima e declarações recentes nos portais (FBref, WhoScored, Flashscore).
    - Cruze isso com o momento atual dos times.
    
    ETAPA 2: ANÁLISE DE VALOR (Regra de Ouro)
    - Só sugira um mercado se a probabilidade estatística for superior a 65%.
    - Para cada mercado sugerido, estime a "Odd Justa" (o preço que deveria estar na Bet365).
    
    ETAPA 3: ENTREGA (Direta e Técnica)
    Sugira 3 mercados da Bet365:
    1. RESULTADO: (1x2 ou Handicap Asiático).
    2. GOLS: (Over/Under ou Ambas Marcam).
    3. ESTATÍSTICAS: (Escanteios Asiáticos ou Cartões).
    
    REGRAS DE FORMATO:
    - Justificativa técnica (máx. 15 palavras por sugestão).
    - Se não houver clareza estatística > 65%, indique: "Jogo de alta incerteza. Evitar apostas."
    - Formato: 
      [Nome do Mercado]: [Sugestão] (Confiança: X%) - Justificativa.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Erro na análise: {str(e)}"

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
        liga = traduzir(jogo['league']['name'])
        casa_nome = traduzir(jogo['teams']['home']['name'])
        fora_nome = traduzir(jogo['teams']['away']['name'])
        
        analise = analisar_com_ia_e_dados(jogo, liga)
        enviar_telegram(f"🔍 *RELATÓRIO DE INTELIGÊNCIA*\n{casa_nome} vs {fora_nome}\n\n{analise}")

if __name__ == "__main__":
    executar_analise()
