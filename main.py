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
    model_name='gemini-2.5-flash'
)

# --- Funções Utilitárias ---
def enviar_telegram(texto, chat_id=CHAT_ID):
    if not TELEGRAM_TOKEN or not chat_id: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # Remove asteriscos e sublinhados que quebram o Telegram
    texto_seguro = texto.replace('*', '').replace('_', '')
    
    # Envia usando HTML
    payload = {"chat_id": chat_id, "text": texto_seguro, "parse_mode": "HTML"}
    
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            print(f"⚠️ Telegram rejeitou o HTML. Reenviando texto puro... Erro: {r.text}")
            payload.pop("parse_mode", None)
            payload["text"] = texto_seguro.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '')
            requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"❌ Erro de conexão com o Telegram: {e}")

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
                        f"👋 <b>Fala, {nome_membro}! GOOOOOOL!</b>\n\n"
                        f"Seja bem-vindo ao <b>VAR do Lucro</b>! 🟢\n"
                        f"Você acaba de entrar para o time que não vive de palpite, vive de análise técnica de verdade.\n\n"
                        f"🚀 <b>Regras de jogo:</b>\n"
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
                        enviar_telegram("👋 <b>Fala, time! GOOOOOOL!</b>\n\nSejam bem-vindos ao <b>VAR do Lucro</b>! 🟢\n\nAqui o nosso robô analisa lesões, escalações e o clima para mandar a bola direto no gol aberto.\n\n🚀 Fiquem atentos às notificações!", chat_id_origem)
                    elif texto == "/bomdia":
                        enviar_telegram("☀️ <b>Bom dia, time de Campeões!</b>\n\nO gramado já está cortado e o VAR do Lucro está mapeando as melhores oportunidades de hoje. Fiquem de olho que vem Green por aí! 🚀💸", chat_id_origem)
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
    
    Analise o confronto considerando o momento recente das equipes, histórico de confrontos diretos (H2H), desempenho como mandante/visitante e importância da partida.
    
    REGRA DE FORMATAÇÃO: NÃO USE asteriscos, sublinhados ou negrito no texto. Escreva em formato de texto limpo.
    
    ANÁLISE DE SAÍDA (FORMATO OBRIGATÓRIO):
    🎯 1. PLACAR MAIS PROVÁVEL: [Palpite]
    💰 2. MERCADOS COM MAIS VALOR: [1-3 mercados com justificativa técnica]
    📊 3. GRAU DE CONFIANÇA: [Nota 0-10]
    ⚠️ 4. PRINCIPAIS RISCOS DA ENTRADA: [Riscos]
    """
    try:
        response = model.generate_content(prompt)
        return response.text if response.text else "⚠️ IA não retornou análise."
    except Exception as e:
        return f"⚠️ Erro na análise da IA: {str(e)}"
