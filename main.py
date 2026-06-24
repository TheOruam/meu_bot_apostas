import os
import requests
import json
import random
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
import google.generativeai as genai

# Configurações
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
ADMIN_ID = "747956770" # SEU ID DO TELEGRAM AQUI
API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY')
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash')

LIGAS_MAP = {
    "Brasileirão A": 71, "Brasileirão B": 72, "Premier League": 39,
    "Libertadores": 13, "Champions": 2
}

def carregar_ligas():
    try:
        with open('ligas.json', 'r') as f: return json.load(f)['ids']
    except: return [71]

def enviar_telegram(texto, chat_id=CHAT_ID, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": texto, "parse_mode": "Markdown", "reply_markup": reply_markup}
    requests.post(url, json=payload)

def processar_updates():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    updates = requests.get(url).json().get("result", [])
    for u in updates:
        # Lógica de Botões (Ligas)
        if "callback_query" in u:
            cb = u["callback_query"]
            cid = str(cb["from"]["id"])
            if cid == ADMIN_ID and cb["data"].startswith("toggle_"):
                id_liga = int(cb["data"].split("_")[1])
                ligas = carregar_ligas()
                if id_liga in ligas: ligas.remove(id_liga)
                else: ligas.append(id_liga)
                with open('ligas.json', 'w') as f: json.dump({"ids": ligas}, f)
                # Opcional: editar a mensagem aqui
        
        # Lógica de Comandos
        elif "message" in u:
            msg = u["message"]
            cid = str(msg.get("chat", {}).get("id"))
            txt = msg.get("text", "")
            if txt == "/ligas" and cid == ADMIN_ID:
                # Lógica para enviar o painel com botões
                ligas_ativas = carregar_ligas()
                botoes = [[{"text": f"{'🟢' if lid in ligas_ativas else '🔴'} {nome}", "callback_data": f"toggle_{lid}"}] for nome, lid in LIGAS_MAP.items()]
                enviar_telegram("🎛️ Painel de Ligas:", cid, {"inline_keyboard": botoes})

def analisar_com_ia_e_dados(casa, fora, liga):
    prompt = f"VAR do Lucro: Analise {casa} vs {fora} ({liga}). Segurança: 75%+. Se incerto, 'Alta Incerteza'. Formato: [Mercado]: [Sugestão] (Confiança: X%) - [Justificativa]. Evite riscos desnecessários."
    return model.generate_content(prompt).text

def executar_analise():
    hora_brt = datetime.utcnow() - timedelta(hours=3)
    # Lógica de Horários
    if 5 <= hora_brt.hour < 21:
        # Buscar jogos... (seu código de busca da API aqui)
        # Ao analisar, use: LIGAS_PRIORITARIAS = carregar_ligas()
        pass
    else:
        # Enviar Resumo
        pass

if __name__ == "__main__":
    processar_updates()
    executar_analise()
