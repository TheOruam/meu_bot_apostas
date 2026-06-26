import os
import requests
import time
from datetime import datetime, timedelta, timezone
from deep_translator import GoogleTranslator
from google import genai

# --- Configurações Principais ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# --- Ligas VIPs ---
LIGAS_PRIORITARIAS = [1, 2, 3, 13, 71, 72, 73, 39, 140, 135, 78, 61, 848, 866]

# --- Inicialização da IA ---
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# --- Funções Utilitárias ---
def enviar_telegram(texto, chat_id=CHAT_ID):
    if not TELEGRAM_TOKEN or not chat_id:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    texto_seguro = texto.replace('*', '').replace('_', '')
    payload = {"chat_id": chat_id, "text": texto_seguro, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            print(f"⚠️ Telegram rejeitou o HTML. Erro: {r.text}")
            payload.pop("parse_mode", None)
            payload["text"] = texto_seguro.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '')
            requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"❌ Erro de conexão com o Telegram: {e}")

def traduzir(texto):
    if not texto: return ""
    try: return GoogleTranslator(source='auto', target='pt').translate(texto)
    except: return texto

# --- Função de Análise com IA ---
def analisar_com_ia_e_dados(jogo_dados, liga_nome):
    casa = jogo_dados['teams']['home']['name']
    fora = jogo_dados['teams']['away']['name']

    prompt = f"""
    Você é o 'VAR do Lucro', analista de apostas de elite.

    DADOS TÉCNICOS FORNECIDOS PELA API:
    - Casa: {casa}
    - Visitante: {fora}
    - Contexto: {liga_nome}

    Analise o confronto considerando o momento recente das equipes, histórico de confrontos diretos (H2H), desempenho como mandante/visitante e importância da partida.

    REGRA DE FORMATAÇÃO: NÃO USE asteriscos, sublinhados ou negrito no texto. Escreva em formato de texto limpo.

    ANÁLISE DE SAÍDA (FORMATO OBRIGATÓRIO):
    🎯 1. PLACAR MAIS PROVÁVEL: [Palpite]
    💰 2. MERCADOS COM MAIS VALOR: [1-3 mercados com justificativa técnica]
    📊 3. GRAU DE CONFIANÇA: [Nota 0-10]
    ⚠️ 4. PRINCIPAIS RISCOS DA ENTRADA: [Riscos]
    """
    if not client:
        return "⚠️ IA não configurada (GEMINI_API_KEY ausente)."
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text if response.text else "⚠️ IA não retornou análise."
    except Exception as e:
        return f"⚠️ Erro na análise da IA: {str(e)}"

# --- Execução Principal de Análise (Olhando 1h para frente) ---
def buscar_e_analisar_jogos():
    hora_brt = datetime.now(timezone.utc) - timedelta(hours=3)
    
    url_api = "https://v3.football.api-sports.io/fixtures"
    headers = {'x-apisports-key': API_FOOTBALL_KEY}
    
    # 1 única requisição para economizar cota da API
    params = {
        'date': hora_brt.strftime('%Y-%m-%d'),
        'timezone': 'America/Sao_Paulo'
    }
    
    try:
        resposta = requests.get(url_api, headers=headers, params=params, timeout=15)
        jogos = resposta.json().get('response', [])
    except Exception as e:
        print(f"❌ Erro ao conectar na API: {e}")
        return

    print(f"🔍 Buscando jogos do dia: {params['date']}")
    
    agora_timestamp = time.time()
    # Define a janela exata: Jogos que começam entre 60 e 119 minutos a partir de agora
    janela_inicio = agora_timestamp + 3600
    janela_fim = agora_timestamp + 7140
    
    jogos_na_janela = []
    
    for jogo in jogos:
        try:
            jogo_timestamp = jogo['fixture']['timestamp']
            id_liga = jogo['league']['id']
            status = jogo['fixture']['status']['short']
            
            if id_liga in LIGAS_PRIORITARIAS and status == 'NS':
                if janela_inicio <= jogo_timestamp <= janela_fim:
                    jogos_na_janela.append(jogo)
        except: continue

    if not jogos_na_janela:
        print("Nenhum jogo VIP agendado para a próxima hora.")
        return

    enviar_telegram("⚽ O VAR do Lucro encontrou lances que vão começar em 1 hora! Gerando relatórios...")

    for jogo in jogos_na_janela:
        liga = traduzir(jogo['league']['name'])
        casa = traduzir(jogo['teams']['home']['name'])
        fora = traduzir(jogo['teams']['away']['name'])
        
        print(f"🧠 IA analisando: {casa} vs {fora}...")
        analise = analisar_com_ia_e_dados(jogo, liga)
        
        msg_final = (
            f"🚨 <b>LANCE DE OURO DETECTADO!</b>\n\n"
            f"⚽ <b>{casa}</b> vs <b>{fora}</b>\n"
            f"🏆 {liga}\n"
            f"⏳ <i>O jogo começa em cerca de 1 hora!</i>\n\n"
            f"{analise}\n\n"
            f"👉 <b>Aposta sugerida? Confira na sua Casa favorita!</b>"
        )
        enviar_telegram(msg_final)
        time.sleep(15)

# --- Resumo do Dia ---
def enviar_resumo_do_dia():
    hora_brt = datetime.now(timezone.utc) - timedelta(hours=3)
    url_api = "https://v3.football.api-sports.io/fixtures"
    headers = {'x-apisports-key': API_FOOTBALL_KEY}
    params = {
        'date': hora_brt.strftime('%Y-%m-%d'),
        'timezone': 'America/Sao_Paulo'
    }
    
    try:
        resposta = requests.get(url_api, headers=headers, params=params, timeout=15)
        jogos = resposta.json().get('response', [])
    except: return

    jogos_finalizados = [j for j in jogos if j['league']['id'] in LIGAS_PRIORITARIAS and j['fixture']['status']['short'] == 'FT']
    if not jogos_finalizados: return

    msg = "🏁 <b>FECHAMENTO DO VAR: BALANÇO DO DIA</b>\n\n"
    for jogo in jogos_finalizados:
        casa = traduzir(jogo['teams']['home']['name'])
        fora = traduzir(jogo['teams']['away']['name'])
        msg += f"⚽ {casa} <b>{jogo['goals']['home']} x {jogo['goals']['away']}</b> {fora}\n"
    
    msg += "\n<b>O VAR encerra os trabalhos. Amanhã tem mais!</b> 🚀"
    enviar_telegram(msg)

# --- Fluxo de Entrada Principal ---
if __name__ == "__main__":
    hora_brt = datetime.now(timezone.utc) - timedelta(hours=3)
    print(f"\n{'='*50}\nVAR DO LUCRO - {hora_brt.strftime('%d/%m/%Y %H:%M:%S')}\n{'='*50}")

    if hora_brt.hour == 23:
        enviar_resumo_do_dia()
    else:
        buscar_e_analisar_jogos()
