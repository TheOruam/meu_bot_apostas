import os
import requests
import google.generativeai as genai
import random
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

# Configurações - Puxa o token do GitHub Secrets automaticamente
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
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
    Você é o 'VAR do Lucro', um analista de apostas de elite. Identifique 'Value Bets' no confronto: {casa} vs {fora} ({liga_nome}).
    
    ETAPA 1: INVESTIGAÇÃO
    - Considere dados reais (lesões, escalações, clima, notícias recentes de FBref, WhoScored, Flashscore).
    
    ETAPA 2: ANÁLISE DE VALOR
    - Só sugira se a confiança for superior a 65%.
    - Estime a 'Odd Justa' para comparação com a Bet365.
    
    ETAPA 3: ENTREGA (Direta e Técnica)
    Sugira 3 mercados da Bet365:
    1. RESULTADO: (1x2 ou Handicap Asiático).
    2. GOLS: (Over/Under ou Ambas Marcam).
    3. ESTATÍSTICAS: (Escanteios ou Cartões).
    
    REGRAS:
    - Justificativa técnica (máx. 15 palavras).
    - Se incerto, indique: "Jogo de alta incerteza. Evitar apostas."
    - Formato: [Nome do Mercado]: [Sugestão] (Confiança: X%) - Justificativa.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Erro na análise: {str(e)}"

def executar_analise():
    # Frases de início divertidas para o seu bot
    frases_inicio = [
        "⚽ O VAR do Lucro entrou em campo! Analisando os lances de hoje...",
        "🏃‍♂️ Corrida para o Green iniciada! O Robô está em campo...",
        "🧐 Olho no lance! O VAR do Lucro está revisando as odds da Bet365...",
        "🏆 Bola rolando e o VAR na espreita. Buscando o gol da vitória...",
        "⚡ Escalação definida: O VAR do Lucro está pronto para buscar o lucro!"
    ]
    enviar_telegram(random.choice(frases_inicio))
    
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
        enviar_telegram("⚠️ Nenhuma oportunidade de valor encontrada nas próximas 8 horas. O VAR segue monitorando...")
        return

    for jogo in jogos_do_turno:
        liga = traduzir(jogo['league']['name'])
        casa_nome = traduzir(jogo['teams']['home']['name'])
        fora_nome = traduzir(jogo['teams']['away']['name'])
        
        analise = analisar_com_ia_e_dados(jogo, liga)
        enviar_telegram(f"🔍 *RELATÓRIO DE INTELIGÊNCIA*\n{casa_nome} vs {fora_nome}\n\n{analise}\n\n👉 *Confira na Bet365!*")

if __name__ == "__main__":
    executar_analise()
