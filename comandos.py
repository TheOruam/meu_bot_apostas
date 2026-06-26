import os
import requests
import time
from google import genai

# Puxa os tokens do Render
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Inicializa IA localmente para os comandos
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def enviar_telegram(texto, chat_id):
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
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

def verificar_se_eh_admin(chat_id, user_id):
    if chat_id > 0: return True
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getChatAdministrators"
    try:
        resposta = requests.get(url, params={"chat_id": chat_id}, timeout=10).json()
        if resposta.get("ok"):
            return user_id in [m["user"]["id"] for m in resposta["result"]]
    except: return False
    return False

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
    except: return "Fala, time! O foco continua no Green!"

def processar_updates(offset, funcao_analise_manual):
    if not TELEGRAM_TOKEN: return offset
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {'offset': offset, 'timeout': 10} if offset else {'timeout': 10}
    
    try:
        resposta = requests.get(url, params=params, timeout=15).json()
        if not resposta.get("ok") or not resposta.get("result"): return offset
            
        agora_atual = time.time()
        
        for update in resposta["result"]:
            offset = update["update_id"] + 1
            msg = update.get("message")
            if not msg: continue
                
            chat_id_origem = msg.get("chat", {}).get("id")
            user_id = msg.get("from", {}).get("id")
            msg_date = msg.get("date", 0)
            
            try:
                # 1. Boas-vindas
                if "new_chat_members" in msg and (agora_atual - msg_date < 300):
                    for novo_membro in msg["new_chat_members"]:
                        if novo_membro.get("is_bot"): continue
                        nome = novo_membro.get("first_name", "Craque")
                        msg_boas_vindas = f"👋 <b>Fala, {nome}! GOOOOOOL!</b>\n\nSeja bem-vindo ao <b>VAR do Lucro</b>! 🟢\nEntraste para o time de análise técnica.\n\n💰 Vamos para cima deles!"
                        enviar_telegram(msg_boas_vindas, chat_id_origem)

                # 2. Comandos de Texto
                if "text" in msg:
                    texto = msg["text"].lower().strip()
                    if (agora_atual - msg_date < 600):
                        comandos_ia = ["/bomdia", "/bemvindo", "/start", "/green", "/red", "/resenha", "/update"]
                        
                        if texto in comandos_ia and verificar_se_eh_admin(chat_id_origem, user_id):
                            if texto == "/update":
                                enviar_telegram("🔄 <b>Varredura manual acionada...</b>", chat_id_origem)
                                # Chama a função que vem do main.py
                                funcao_analise_manual() 
                            else:
                                comando_real = "/bemvindo" if texto == "/start" else texto
                                enviar_telegram("<i>⏳ O VAR está a analisar o chat...</i>", chat_id_origem)
                                enviar_telegram(gerar_mensagem_interativa(comando_real), chat_id_origem)
            except Exception as e:
                print(f"⚠️ Erro interno no comando: {e}")

        return offset
    except Exception as e:
        return offset
