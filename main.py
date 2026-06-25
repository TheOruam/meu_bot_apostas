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
    
    # Remove asteriscos e sublinhados que quebram o Telegram
    texto_seguro = texto.replace('*', '').replace('_', '')
    
    # Tenta enviar usando HTML (Mais seguro que Markdown)
    payload = {"chat_id": chat_id, "text": texto_seguro, "parse_mode": "HTML"}
    
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            print(f"⚠️ Telegram rejeitou o HTML. Reenviando texto puro... Erro: {r.text}")
            # Se falhar, tira o parse_mode e remove as tags HTML manualmente
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
    
    INVESTIGAÇÃO NECESSÁRIA (USE A FERRAMENTA DE BUSCA):
    - Pesquise sobre desfalques, notícias de última hora, prováveis escalações e motivação para esta partida específica.
    
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

# --- Execução Principal de Análise ---
def executar_analise():
    hora_brt = datetime.now(timezone.utc) - timedelta(hours=3)
    janela_horas = 6 
    
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
        print(f"❌ Erro ao conectar na API: {e}")
        return

    agora_timestamp = time.time()
    limite_timestamp = agora_timestamp + (janela_horas * 3600)
    
    print(f"🔍 Buscando jogos do dia: {params['date']}")
    print(f"⚽ Total de jogos encontrados no mundo hoje: {len(jogos)}")
    
    jogos_validos = []
    for j in jogos:
        try:
            jogo_timestamp = j['fixture']['timestamp']
            id_liga = j['league']['id']
            status = j['fixture']['status']['short']
            
            if id_liga in LIGAS_PRIORITARIAS:
                if status == 'NS' and agora_timestamp <= jogo_timestamp <= limite_timestamp:
                    jogos_validos.append(j)
        except: continue

    if not jogos_validos:
        enviar_telegram("⚠️ Nenhuma oportunidade VIP encontrada nas próximas horas. O VAR segue de olho...")
        if hora_brt.hour >= 21:
            msg_boa_noite = (
                "🌙 <b>FIM DE RODADA! O VAR ENCERRA OS TRABALHOS!</b> 🏁\n\n"
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
        
        print(f"🧠 A Inteligência Artificial está analisando: {casa} vs {fora}...")
        analise = analisar_com_ia_e_dados(jogo, liga)
        print(f"✅ Análise concluída! Tentando enviar para o Telegram...")
        
        msg_final = f"🔍 <b>RELATÓRIO DE INTELIGÊNCIA</b>\n⚽ <b>{casa}</b> vs <b>{fora}</b>\n🏆 {liga}\n\n{analise}\n\n👉 <b>Aposta sugerida? Confira na sua Casa favorita!</b>"
        enviar_telegram(msg_final)
        time.sleep(15) 

    if hora_brt.hour >= 21:
        msg_boa_noite = (
            "🌙 <b>FIM DE RODADA! O VAR ENCERRA OS TRABALHOS!</b> 🏁\n\n"
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

    msg = "🏁 <b>FECHAMENTO DO VAR: BALANÇO DO DIA</b>\n\n"
    for jogo in jogos_finalizados:
        casa = traduzir(jogo['teams']['home']['name'])
        fora = traduzir(jogo['teams']['away']['name'])
        msg += f"⚽ {casa} <b>{jogo['goals']['home']} x {jogo['goals']['away']}</b> {fora}\n"
    
    msg += "\n<b>O VAR encerra os trabalhos. Amanhã tem mais!</b> 🚀"
    enviar_telegram(msg)

# --- Fluxo de Entrada Principal ---
if __name__ == "__main__":
    if not processar_updates():
        hora_brt = datetime.now(timezone.utc) - timedelta(hours=3)
        if hora_brt.hour >= 23 or hora_brt.hour < 1:
            enviar_resumo_do_dia()
        elif 5 <= hora_brt.hour <= 22:
            executar_analise()
