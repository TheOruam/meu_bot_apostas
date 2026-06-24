import os
import requests
import random
import time
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
from google import genai 

# --- Configurações Principais ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID') 
API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# --- Ligas VIPs ---
LIGAS_PRIORITARIAS = [1, 2, 3, 13, 71, 72, 73, 39, 140, 135, 78, 61, 848, 866]

# --- Inicialização da IA (Sintaxe Nova) ---
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# --- Funções Utilitárias ---
def enviar_telegram(texto, chat_id=CHAT_ID):
    if not TELEGRAM_TOKEN or not chat_id:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": texto, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"❌ Erro ao enviar Telegram: {e}")

def traduzir(texto):
    if not texto: return ""
    try:
        return GoogleTranslator(source='auto', target='pt').translate(texto)
    except:
        return texto

def verificar_se_eh_admin(chat_id, user_id):
    if chat_id > 0:
        return True
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getChatAdministrators"
    try:
        resposta = requests.get(url, params={"chat_id": chat_id}, timeout=10).json()
        if resposta.get("ok"):
            admins = [membro["user"]["id"] for membro in resposta["result"]]
            return user_id in admins
    except Exception as e:
        print(f"⚠️ Erro ao verificar lista de admins: {e}")
    return False

# --- Central de Updates (Comandos e Novos Membros) ---
def processar_updates():
    if not TELEGRAM_TOKEN: return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    comando_executado = False
    
    try:
        resposta = requests.get(url, timeout=10).json()
        if "result" not in resposta: return False
        
        agora_timestamp = datetime.utcnow().timestamp()
        
        for update in resposta["result"]:
            if "message" not in update: continue
            msg = update["message"]
            chat_id_origem = msg["chat"]["id"]
            user_id = msg["from"]["id"]
            msg_date = msg["date"]

            # 1. VERIFICAÇÃO DE NOVOS MEMBROS (Roda conforme programado)
            if "new_chat_members" in msg and (agora_timestamp - msg_date < 32400):
                for novo_membro in msg["new_chat_members"]:
                    if novo_membro["is_bot"]: continue
                    nome_membro = novo_membro.get("first_name", "Craque")
                    
                    msg_boas_vindas = (
                        f"👋 **Fala, {nome_membro}! GOOOOOOL!**\n\n"
                        f"Seja bem-vindo ao **VAR do Lucro**! 🟢
