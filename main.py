import os
import requests
import time
from datetime import datetime, timedelta, timezone
from deep_translator import GoogleTranslator
import google.generativeai as genai 

# --- Configurações Principais ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID') 
API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# --- Ligas VIPs ---
LIGAS_PRIORITARIAS = [1, 2, 3, 13, 71, 72, 73, 39, 140, 135, 78, 61, 848, 866]

# --- Inicialização da IA ---
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    tools=[{'google_search_retrieval': {}}] 
)

# --- Funções Utilitárias ---
def enviar_telegram(texto, chat_id=CHAT_ID):
    if not TELEGRAM_TOKEN or not chat_id: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": texto, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except: pass

def traduzir(texto):
    if not texto: return ""
    try: return GoogleTranslator(source='auto', target='pt').translate(texto)
    except: return texto

def verificar_se_eh_admin(chat_id, user_id):
    if chat_id > 0: return True
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getChatAdministrators"
    try:
        resposta = requests.get(url, params={"chat_id": chat_id}, timeout=10).json()
        if resposta.get("ok"):
            admins = [membro["user"]["id"] for membro in resposta["result"]]
            return user_id in admins
    except: return False
    return False

# --- Central de Updates ---
def processar_updates():
    if not TELEGRAM_TOKEN: return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    comando_executado = False
    try:
        resposta = requests.get(url, timeout=10).json()
        if "result" not in resposta: return False
        
        agora_timestamp = time.time()
        
        for update in resposta["result"]:
            if "message" not in update: continue
            msg = update["message"]
            chat_id_origem = msg["chat"]["id"]
            user_id = msg["from"]["id"]
            msg_date = msg["date"]

            if "new_chat_members" in msg and (agora_timestamp - msg_date < 32400):
                for novo_membro in msg["new_chat_members"]:
                    if novo_membro.get("is_bot"): continue
                    nome_membro = novo_membro.get("first_name", "Craque")
                    msg_boas_vindas = (
                        f"👋 **Fala, {nome_membro}! GOOOOOOL!**\n\n"
                        f"Seja bem-vindo ao **VAR do Lucro**! 🟢\n"
                        f"Você acaba de entrar para o time que não vive de palpite, vive de análise técnica de verdade.\n\n"
                        f"🚀 **Regras de jogo:**\n"
                        f"1. Deixe as notificações ativadas para não perder os lances de ouro.\n"
                        f"2. Siga a gestão de banca.\n\n"
                        f"💰 Vamos pra cima da banca!"
                    )
                    enviar_telegram(msg_boas_vindas, chat_id_origem)

            if "text" in msg:
                texto = msg["text"].lower().strip()
                if agora_timestamp - msg_date > 600: continue
                
                if texto in ["/bomdia", "/bemvindo", "/start"] and verificar_se_eh_admin(chat_id_origem, user_id):
                    if texto in ["/bemvindo", "/start"]:
                        enviar_telegram("👋 **Fala, time! GOOOOOOL!**\n\nSejam bem-vindos ao **VAR do Lucro**! 🟢\n\nAqui o nosso robô analisa lesões, escalações e o clima para mandar a bola direto no gol aberto.\n\n🚀 Fiquem atentos às notificações!", chat_id_origem)
                    elif texto == "/bomdia":
                        enviar_telegram("☀️ **Bom dia, time de Campeões!**\n\nO gramado já está cortado e o VAR do Lucro está mapeando as melhores oportunidades de hoje. Fiquem de olho que vem Green por aí! 🚀💸", chat_id_origem)
                    comando_executado = True
    except: pass
    return comando_executado

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
    
    INVESTIGAÇÃO NECESSÁRIA (USE A FERRAMENTA DE BUSCA):
    - Pesquise sobre desfalques, notícias de última hora, prováveis escalações e motivação para esta partida específica.
    
    ANÁLISE DE SAÍDA (FORMATO OBRIGATÓRIO):
    🎯 1. PLACAR MAIS PROVÁVEL: [Palpite]
    💰 2. MERCADOS COM MAIS VALOR: [1-3 mercados com justificativa técnica baseada nos dados e nas notícias encontradas]
    📊 3. GRAU DE CONFIANÇA: [Nota 0-10]
    ⚠️ 4. PRINCIPAIS RISCOS DA ENTRADA: [Baseado em possíveis desfalques ou notícias negativas]
    """
    try:
        response = model.generate_content(prompt)
        return response.text if response.text else "⚠️ IA não retornou análise."
    except Exception as e:
        return f"⚠️ Erro na análise da IA: {str(e)}"

# --- Execução Principal de Análise ---
def executar_analise():
    hora_brt = datetime.now(timezone.utc) - timedelta(hours=3)
    janela_horas = 6 # Aumentado para 6 horas de varredura garantindo o alcance dos jogos
    
    url_api = "https://v3.football.api-sports.io/fixtures"
    headers = {'x-apisports-key': API_FOOTBALL_KEY}
    
    # AJUSTE DE OURO: Adicionado o fuso horário de São Paulo para a API
    params = {
        'date': hora_brt.strftime('%Y-%m-%d'),
        'timezone': 'America/Sao_Paulo'
    }
    
    try:
        resposta = requests.get(url_api, headers=headers, params=params, timeout=15)
        jogos = resposta.json().get('response', [])
    except: return

    # Usando Timestamp (Matemática pura que ignora falhas de fuso horário)
    agora_timestamp = time.time()
    limite_timestamp = agora_timestamp + (janela_horas * 3600)
    
    jogos_validos = []
    for j in jogos:
        try:
            jogo_timestamp = j['fixture']['timestamp']
            if (j['league']['id'] in LIGAS_PRIORITARIAS and 
                j['fixture']['status']['short'] == 'NS' and 
                agora_timestamp <= jogo_timestamp <= limite_timestamp):
                jogos_validos.append(j)
        except: continue

    if not jogos_validos:
        enviar_telegram("⚠️ Nenhuma oportunidade VIP encontrada nas próximas horas. O VAR segue de olho...")
        if hora_brt.hour >= 21:
            msg_boa_noite = (
                "🌙 *FIM DE RODADA! O VAR ENCERRA OS TRABALHOS!* 🏁\n\n"
                "Por hoje é só, amigos! O dever foi cumprido e a rodada da noite fechou sem novos lances. "
                "Hora de desligar os servidores, guardar os greens no bolso e descansar a mente.\n\n"
                "Grande abraço do VAR e boa noite, campeões! 🛌⚽💰"
            )
            enviar_telegram(msg_boa_noite)
        return

    enviar_telegram("⚽ O VAR do Lucro entrou em campo! Analisando os lances de hoje...")

    for jogo in jogos_validos:
        liga = traduzir(jogo['league']['name'])
        casa = traduzir(jogo['teams']['home']['name'])
        fora = traduzir(jogo['teams']['away']['name'])
        
        analise = analisar_com_ia_e_dados(jogo, liga)
        msg_final = f"🔍 *RELATÓRIO DE INTELIGÊNCIA*\n⚽ *{casa}* vs *{fora}*\n🏆 {liga}\n\n{analise}\n\n👉 *Aposta sugerida? Confira na sua Casa favorita!*"
        enviar_telegram(msg_final)
        time.sleep(15) 

    if hora_brt.hour >= 21:
        msg_boa_noite = (
            "🌙 *FIM DE RODADA! O VAR ENCERRA OS TRABALHOS!* 🏁\n\n"
            "Por hoje é só, amigos! O robô varreu os campos, a IA trabalhou firme e o green foi decretado. "
            "Agora é hora de desligar os motores, descansar a mente e se preparar para os lucros de amanhã.\n\n"
            "Grande abraço do VAR e uma excelente noite de sono para todos! 🛌⚽💰"
        )
        enviar_telegram(msg_boa_noite)

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

    msg = "🏁 *FECHAMENTO DO VAR: BALANÇO DO DIA*\n\n"
    for jogo in jogos_finalizados:
        casa = traduzir(jogo['teams']['home']['name'])
        fora = traduzir(jogo['teams']['away']['name'])
        msg += f"⚽ {casa} *{jogo['goals']['home']} x {jogo['goals']['away']}* {fora}\n"
    
    msg += "\n*O VAR encerra os trabalhos. Amanhã tem mais!* 🚀"
    enviar_telegram(msg)

# --- Fluxo de Entrada Principal ---
if __name__ == "__main__":
    if not processar_updates():
        hora_brt = datetime.now(timezone.utc) - timedelta(hours=3)
        if hora_brt.hour >= 23 or hora_brt.hour < 1:
            enviar_resumo_do_dia()
        elif 5 <= hora_brt.hour <= 22:
            executar_analise()
