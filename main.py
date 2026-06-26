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
    
    # Limpeza de segurança contra caracteres que quebram o Telegram
    texto_seguro = texto.replace('*', '').replace('_', '')
    
    payload = {"chat_id": chat_id, "text": texto_seguro, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            print(f"⚠️ Telegram rejeitou o HTML. Reenviando texto limpo... Erro: {r.text}")
            payload.pop("parse_mode", None)
            payload["text"] = (texto_seguro
                               .replace('<b>', '').replace('</b>', '')
                               .replace('<i>', '').replace('</i>', ''))
            requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"❌ Erro de conexão com o Telegram: {e}")

def traduzir(texto):
    if not texto: return ""
    try: return GoogleTranslator(source='auto', target='pt').translate(texto)
    except: return texto

def verificar_se_eh_admin(chat_id, user_id):
    if chat_id > 0: 
        return True  # Permite comandos diretos no privado com o Bot
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getChatAdministrators"
    try:
        resposta = requests.get(url, params={"chat_id": chat_id}, timeout=10).json()
        if resposta.get("ok"):
            admins = [membro["user"]["id"] for membro in resposta["result"]]
            return user_id in admins
    except: 
        return False
    return False

# --- Fábrica de Mensagens de Chat (IA) ---
def gerar_mensagem_interativa(comando):
    if not client:
        return "⚠️ O VAR está sem comunicação com a cabine (IA offline)."
    
    if comando == "/bomdia":
        prompt = "Escreva uma mensagem de 'Bom dia' muito animada, curta e engraçada para um grupo de apostas esportivas chamado 'VAR do Lucro'. Use gírias de futebol e apostas (green, forrar, banca). NÃO USE asteriscos ou formatação especial."
    elif comando == "/bemvindo":
        prompt = "Escreva uma mensagem de boas-vindas curta, animada e engraçada para os novos membros do grupo 'VAR do Lucro'. Avise para ativarem as notificações e seguirem a gestão de banca. NÃO USE asteriscos ou formatação especial."
    elif comando == "/green":
        prompt = "Escreva uma comemoração explosiva, curta e muito feliz para o grupo 'VAR do Lucro' celebrando que uma aposta deu Green! Fale sobre forrar o bolso. NÃO USE asteriscos."
    elif comando == "/red":
        prompt = "Escreva uma mensagem de apoio curta e bem-humorada para o grupo 'VAR do Lucro' após um Red (aposta perdida). Relembre a importância de manter a calma e focar na gestão de banca. NÃO USE asteriscos."
    elif comando == "/resenha":
        prompt = "Escreva uma curiosidade bizarra, engraçada ou histórica sobre o mundo do futebol para descontrair o grupo 'VAR do Lucro'. Seja curto, rápido e divertido. NÃO USE asteriscos."
    else:
        return "Comando não reconhecido pelo VAR."

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text if response.text else "Fala, time! Vamos em busca do Green!"
    except Exception as e:
        print(f"Erro na IA do chat: {e}")
        return "Fala, time! O foco continua no Green!"

# --- Central de Updates (Leitura de Comandos) ---
def processar_updates():
    if not TELEGRAM_TOKEN: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    try:
        resposta = requests.get(url, timeout=10).json()
        if "result" not in resposta: return
        
        agora_timestamp = time.time()
        
        for update in resposta["result"]:
            if "message" not in update: continue
            msg = update["message"]
            chat_id_origem = msg["chat"]["id"]
            user_id = msg["from"]["id"]
            msg_date = msg["date"]

            # Boas-vindas automáticas para novos membros no grupo
            if "new_chat_members" in msg and (agora_timestamp - msg_date < 32400):
                for novo_membro in msg["new_chat_members"]:
                    if novo_membro.get("is_bot"): continue
                    nome_membro = novo_membro.get("first_name", "Craque")
                    msg_boas_vindas = (
                        f"👋 <b>Fala, {nome_membro}! GOOOOOOL!</b>\n\n"
                        f"Seja bem-vindo ao <b>VAR do Lucro</b>! 🟢\n"
                        f"Entraste para o time que não vive de palpites, vive de análise técnica.\n\n"
                        f"🚀 <b>Regras do jogo:</b>\n"
                        f"1. Ativa as notificações para não perderes os lances de ouro.\n"
                        f"2. Segue à risca a gestão de banca.\n\n"
                        f"💰 Vamos para cima deles!"
                    )
                    enviar_telegram(msg_boas_vindas, chat_id_origem)

            # Processamento de comandos de texto (Apenas administradores)
            if "text" in msg:
                texto = msg["text"].lower().strip()
                # Ignora mensagens enviadas há mais de 10 minutos para não responder comandos antigos
                if agora_timestamp - msg_date > 600: continue
                
                comandos_ia = ["/bomdia", "/bemvindo", "/start", "/green", "/red", "/resenha"]
                
                if texto in comandos_ia and verificar_se_eh_admin(chat_id_origem, user_id):
                    comando_real = "/bemvindo" if texto == "/start" else texto
                    
                    # Notificação de digitação visual para o grupo
                    enviar_telegram("<i>⏳ O VAR está a analisar o chat...</i>", chat_id_origem)
                    
                    # Gera e envia a resposta dinâmica da IA
                    mensagem_gerada = gerar_mensagem_interativa(comando_real)
                    enviar_telegram(mensagem_gerada, chat_id_origem)
    except Exception as e:
        print(f"⚠️ Falha ao processar updates do Telegram: {e}")

# --- Execução Principal de Análise (Futebol) ---
def buscar_e_analisar_jogos():
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
    except Exception as e:
        print(f"❌ Erro ao conectar na API de Futebol: {e}")
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
            status = j_status = jogo['fixture']['status']['short']
            
            if id_liga in LIGAS_PRIORITARIAS and j_status == 'NS':
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

# --- Resumo Final do Dia ---
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
    
    msg += "\n<b>O VAR encerra os trabalhos por hoje. Amanhã há mais greens!</b> 🚀"
    enviar_telegram(msg)

# --- Fluxo de Entrada Principal (Executado de hora em hora) ---
if __name__ == "__main__":
    hora_brt = datetime.now(timezone.utc) - timedelta(hours=3)
    print(f"\n{'='*50}\nVAR DO LUCRO - {hora_brt.strftime('%d/%m/%Y %H:%M:%S')}\n{'='*50}")

    # 1. Executa comandos pendentes enviados por Admins no Telegram
    processar_updates()

    # 2. Executa a varredura automática de jogos ou balanço do dia
    if hora_brt.hour == 23:
        enviar_resumo_do_dia()
    else:
        buscar_e_analisar_jogos()
