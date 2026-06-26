import os
import requests
import time
from datetime import datetime, timedelta, timezone
from deep_translator import GoogleTranslator
from google import genai
from flask import Flask
from threading import Thread

# --- Configurações Principais ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

LIGAS_PRIORITARIAS = [1, 2, 3, 13, 71, 72, 73, 39, 140, 135, 78, 61, 848, 866]

# --- Inicialização da IA ---
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# --- Servidor Fantasma (Render) ---
app = Flask(__name__)
@app.route('/')
def home(): 
    return "VAR do Lucro está Online!"
def run_server(): 
    app.run(host='0.0.0.0', port=8080)
def keep_alive(): 
    Thread(target=run_server, daemon=True).start()

# --- Funções Utilitárias ---
def enviar_telegram(texto, chat_id=CHAT_ID):
    if not TELEGRAM_TOKEN or not chat_id: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    texto_seguro = texto.replace('*', '').replace('_', '')
    payload = {"chat_id": chat_id, "text": texto_seguro, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            payload.pop("parse_mode", None)
            payload["text"] = texto_seguro.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '')
            requests.post(url, json=payload, timeout=10)
    except:
        pass

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
            return user_id in [m["user"]["id"] for m in resposta["result"]]
    except: 
        return False
    return False

# --- Fábrica de Mensagens (IA) ---
def gerar_mensagem_interativa(comando):
    if not client: return "⚠️ IA offline."
    prompts = {
        "/bomdia": "Bom dia animado para apostadores. Tema: VAR do Lucro. Sem asteriscos.",
        "/bemvindo": "Boas-vindas animadas para grupo 'VAR do Lucro'. Sem asteriscos.",
        "/green": "Comemoração de Green explosiva. Sem asteriscos.",
        "/red": "Consolo pós-Red focado em gestão de banca. Sem asteriscos.",
        "/resenha": "Curiosidade bizarra de futebol. Curto e engraçado. Sem asteriscos."
    }
    try:
        res = client.models.generate_content(model='gemini-2.5-flash', contents=prompts.get(comando, "Fala time!"))
        return res.text if res.text else "Fala, time!"
    except: 
        return "Fala, time! O foco continua no Green!"

def analisar_com_ia_e_dados(jogo, liga):
    # Função tampão para evitar NameError. Pode implementar sua lógica de IA profunda aqui.
    return "📊 Análise técnica em processamento..."

# --- Central de Updates (Versão Blindada Contra Repetições) ---
def processar_updates(offset=None):
    if not TELEGRAM_TOKEN: return offset
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {'offset': offset, 'timeout': 10} if offset else {'timeout': 10}
    
    try:
        resposta = requests.get(url, params=params, timeout=15).json()
        if not resposta.get("ok") or not resposta.get("result"):
            return offset
            
        agora_atual = time.time()
        
        for update in resposta["result"]:
            # 1. ATUALIZAMOS O MARCADOR IMEDIATAMENTE
            # Assim, mesmo que o código dê erro abaixo, a mensagem nunca mais se repete!
            offset = update["update_id"] + 1
            
            msg = update.get("message")
            if not msg: continue
                
            chat_id_origem = msg.get("chat", {}).get("id")
            user_id = msg.get("from", {}).get("id")
            msg_date = msg.get("date", 0)
            
            # 2. ISOLAMOS OS COMANDOS EM UM BLOCO "TRY"
            try:
                # Boas-vindas
                if "new_chat_members" in msg and (agora_atual - msg_date < 300):
                    for novo_membro in msg["new_chat_members"]:
                        if novo_membro.get("is_bot"): continue
                        nome_membro = novo_membro.get("first_name", "Craque")
                        msg_boas_vindas = f"👋 <b>Fala, {nome_membro}! GOOOOOOL!</b>\n\nSeja bem-vindo ao <b>VAR do Lucro</b>! 🟢\nEntraste para o time de análise técnica.\n\n💰 Vamos para cima deles!"
                        enviar_telegram(msg_boas_vindas, chat_id_origem)

                # Comandos de Texto
                if "text" in msg:
                    texto = msg["text"].lower().strip()
                    if (agora_atual - msg_date < 600):
                        comandos_ia = ["/bomdia", "/bemvindo", "/start", "/green", "/red", "/resenha", "/update"]
                        
                        if texto in comandos_ia and verificar_se_eh_admin(chat_id_origem, user_id):
                            if texto == "/update":
                                enviar_telegram("🔄 <b>Varredura manual acionada...</b>", chat_id_origem)
                                buscar_e_analisar_jogos()
                            else:
                                comando_real = "/bemvindo" if texto == "/start" else texto
                                enviar_telegram("<i>⏳ O VAR está a analisar o chat...</i>", chat_id_origem)
                                enviar_telegram(gerar_mensagem_interativa(comando_real), chat_id_origem)
            except Exception as erro_interno:
                print(f"⚠️ Erro ao executar comando: {erro_interno}")
                # O erro é capturado aqui, e o bot continua rodando sem repetir!

        return offset
    except Exception as e:
        print(f"⚠️ Falha de conexão com o Telegram: {e}")
        return offset

# --- Execução Principal de Análise (Futebol) ---
def buscar_e_analisar_jogos():
    hora_brt = datetime.now(timezone.utc) - timedelta(hours=3)
    url_api = "https://v3.football.api-sports.io/fixtures"
    params = {'date': hora_brt.strftime('%Y-%m-%d'), 'timezone': 'America/Sao_Paulo'}
    
    try:
        resposta = requests.get(url_api, headers={'x-apisports-key': API_FOOTBALL_KEY}, params=params, timeout=15)
        jogos = resposta.json().get('response', [])
    except: return

    agora_timestamp = time.time()
    janela_inicio = agora_timestamp + 3600
    janela_fim = agora_timestamp + 7140
    jogos_na_janela = []
    
    for jogo in jogos:
        try:
            if jogo['league']['id'] in LIGAS_PRIORITARIAS and jogo['fixture']['status']['short'] == 'NS':
                if janela_inicio <= jogo['fixture']['timestamp'] <= janela_fim:
                    jogos_na_janela.append(jogo)
        except: continue

    if not jogos_na_janela:
        return

    enviar_telegram("⚽ O VAR do Lucro encontrou lances que vão começar em 1 hora! Gerando relatórios...")

    for jogo in jogos_na_janela:
        liga = traduzir(jogo['league']['name'])
        casa = traduzir(jogo['teams']['home']['name'])
        fora = traduzir(jogo['teams']['away']['name'])
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

def enviar_resumo_do_dia():
    hora_brt = datetime.now(timezone.utc) - timedelta(hours=3)
    url_api = "https://v3.football.api-sports.io/fixtures"
    params = {'date': hora_brt.strftime('%Y-%m-%d'), 'timezone': 'America/Sao_Paulo'}
    
    try:
        resposta = requests.get(url_api, headers={'x-apisports-key': API_FOOTBALL_KEY}, params=params, timeout=15)
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

# --- Fluxo Principal de Loop 24/7 ---
if __name__ == "__main__":
    keep_alive()
    offset = None
    ultima_hora = None
    
    while True:
        try:
            offset = processar_updates(offset)
            hora_brt = datetime.now(timezone.utc) - timedelta(hours=3)
            
            if hora_brt.minute == 0 and hora_brt.hour != ultima_hora:
                if hora_brt.hour == 23:
                    enviar_resumo_do_dia()
                else:
                    buscar_e_analisar_jogos()
                ultima_hora = hora_brt.hour
                
            time.sleep(5)
        except Exception as e:
            print(f"⚠️ Erro no loop: {e}")
            time.sleep(10)
