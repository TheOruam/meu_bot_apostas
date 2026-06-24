import requests
import google.generativeai as genai
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

# Credenciais
TELEGRAM_TOKEN = '8983808854:AAH36YnSLE2ACY_1s5wSDhxQgCUbs66VzlA'
CHAT_ID = '747956770'
API_FOOTBALL_KEY = '418766ef4ec5450f1cab64d32229ddee'
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Configuração Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

LIGAS_PRIORITARIAS = [1, 71, 72, 73, 39, 140, 135, 78, 61, 2] 

def enviar_telegram(texto):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"})

def traduzir(texto):
    try: return GoogleTranslator(source='auto', target='pt').translate(texto)
    except: return texto

def analisar_com_ia(casa, fora, liga_nome):
    prompt = f"""
    Analise o jogo {casa} vs {fora} pela liga {liga_nome}. 
    Considere o cenário atual para apostas na Bet365.
    Forneça: 
    1. Uma breve análise técnica.
    2. Sugestão de mercado (Vencedor, Over/Under ou Ambas Marcam).
    3. Porcentagem de confiança.
    Seja direto e objetivo em português.
    """
    response = model.generate_content(prompt)
    return response.text

def executar_analise():
    agora = datetime.utcnow()
    # Janela de 8 horas para garantir que nenhum jogo escape
    janela_limite = agora + timedelta(hours=8)
    
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    resposta = requests.get("https://v3.football.api-sports.io/fixtures", 
                            headers={'x-apisports-key': API_FOOTBALL_KEY}, 
                            params={'date': data_hoje})
    
    jogos = resposta.json().get('response', [])
    
    jogos_do_turno = []
    for j in jogos:
        horario_jogo = datetime.strptime(j['fixture']['date'], '%Y-%m-%dT%H:%M:%S+00:00')
        if (j['league']['id'] in LIGAS_PRIORITARIAS and 
            j['fixture']['status']['short'] == 'NS' and
            agora <= horario_jogo <= janela_limite):
            jogos_do_turno.append(j)

    if not jogos_do_turno:
        enviar_telegram("✅ Varredura concluída: Nenhum jogo prioritário nas próximas 8h.")
        return

    enviar_telegram(f"🚀 {len(jogos_do_turno)} jogos encontrados. Consultando IA...")

    for jogo in jogos_do_turno:
        casa = traduzir(jogo['teams']['home']['name'])
        fora = traduzir(jogo['teams']['away']['name'])
        liga = traduzir(jogo['league']['name'])
        
        analise = analisar_com_ia(casa, fora, liga)
        
        mensagem = f"🔥 *ANÁLISE IA - Bet365*\n{casa} vs {fora}\n\n{analise}"
        enviar_telegram(mensagem)

if __name__ == "__main__":
    executar_analise()
