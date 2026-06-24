import os
import requests
import random
import subprocess
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
from google import genai  # Biblioteca nova e compatível
import config # Importa as ligas do arquivo config.py

# --- Configurações ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
ADMIN_ID = "747956770"
API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY')
# Inicialização correta da nova API
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

def enviar_telegram(texto, chat_id=CHAT_ID, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": texto, "parse_mode": "Markdown", "reply_markup": reply_markup}
    requests.post(url, json=payload, timeout=10)

def atualizar_config_github(nova_lista):
    """Atualiza o arquivo config.py e faz o commit automático."""
    with open("config.py", "w") as f:
        f.write(f"LIGAS_ATIVAS = {nova_lista}")
    
    subprocess.run(["git", "config", "--global", "user.email", "bot@var.com"])
    subprocess.run(["git", "config", "--global", "user.name", "VAR Bot"])
    subprocess.run(["git", "add", "config.py"])
    subprocess.run(["git", "commit", "-m", "Auto-update ligas via Telegram"])
    subprocess.run(["git", "push"])

def checar_comandos_e_saudar():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    try:
        res = requests.get(url, timeout=10).json()
        for u in res.get("result", []):
            # Saudação /start original
            if "message" in u and u["message"].get("text") == "/start":
                cid = u["message"]["chat"]["id"]
                user_name = u["message"]["from"].get("first_name", "Craque")
                msg = (f"👋 **Fala, {user_name}! GOOOOOOL!** Seja bem-vindo ao **VAR do Lucro**, o único lugar onde o VAR nunca erra o impedimento e a gente só comemora Green! 🟢\n\n"
                       "Você acaba de ser escalado para o time que não vive de palpite, vive de análise! Nosso robô é um 'fominha' por dados: ele varre os campos e só te manda a bola quando o gol está aberto.\n\n"
                       "O árbitro já autorizou a saída de bola. Vamos pra cima da banca? 💰🔥")
                enviar_telegram(msg, cid)
            
            # Painel Administrativo /ligas
            if "message" in u and u["message"].get("text") == "/ligas" and str(u["message"]["chat"]["id"]) == ADMIN_ID:
                botoes = [[{"text": f"{'🟢' if lid in config.LIGAS_ATIVAS else '🔴'} Liga {lid}", "callback_data": f"toggle_{lid}"}] for lid in [71, 72, 39, 13, 2, 1]]
                enviar_telegram("🎛️ *PAINEL ADMINISTRATIVO*", u["message"]["chat"]["id"], {"inline_keyboard": botoes})
            
            if "callback_query" in u:
                cb = u["callback_query"]
                if cb["data"].startswith("toggle_"):
                    lid = int(cb["data"].split("_")[1])
                    nova_lista = list(config.LIGAS_ATIVAS)
                    if lid in nova_lista: nova_lista.remove(lid)
                    else: nova_lista.append(lid)
                    atualizar_config_github(nova_lista)
                    enviar_telegram(f"✅ Liga {lid} alterada!", cb["from"]["id"])
    except: pass

def executar_analise():
    frases_inicio = [
        "⚽ O VAR do Lucro entrou em campo! Analisando os lances de hoje...",
        "🏃‍♂️ Corrida para o Green iniciada! O Robô está em campo...",
        "🧐 Olho no lance! O VAR do Lucro está revisando as odds da Bet365...",
        "🏆 Bola rolando e o VAR na espreita. Buscando o gol da vitória...",
        "⚡ Escalação definida: O VAR do Lucro está pronto para buscar o lucro!"
    ]
    enviar_telegram(random.choice(frases_inicio))
    
    # Exemplo de chamada da nova API dentro da análise:
    # response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)

if __name__ == "__main__":
    checar_comandos_e_saudar()
    hora_brt = datetime.utcnow() - timedelta(hours=3)
    if 5 <= hora_brt.hour < 21: executar_analise()
