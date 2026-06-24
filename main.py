import os
import requests
import google-genai as genai
import random
import time
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

# --- Configurações Principais ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID') 
API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# --- Ligas VIPs ---
LIGAS_PRIORITARIAS = [1, 2, 3, 13, 71, 72, 73, 39, 140, 135, 78, 61, 848, 866]

# --- Inicialização da IA ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

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
    """Verifica se o usuário que enviou o comando é administrador do grupo."""
    # Se for chat privado com o bot, o próprio usuário é o "admin"
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
    """Processa novos membros e comandos disparados por administradores."""
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

            # 1. VERIFICAÇÃO DE NOVOS MEMBROS (Conforme programado)
            # Verifica se alguém entrou no grupo nas últimas 9 horas (tempo entre as rodadas cron)
            if "new_chat_members" in msg and (agora_timestamp - msg_date < 32400):
                for novo_membro in msg["new_chat_members"]:
                    if novo_membro["is_bot"]: continue
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
                    print(f"DEBUG: Novo membro {nome_membro} saudado automaticamente.")

            # 2. VERIFICAÇÃO DE COMANDOS MANUAIS (Executa na hora se for Admin)
            if "text" in msg:
                texto = msg["text"].lower().strip()
                
                # Só aceita comandos enviados nos últimos 10 minutos (execução imediata manual)
                if agora_timestamp - msg_date > 600:
                    continue
                
                if texto in ["/bomdia", "/bemvindo", "/start"]:
                    print(f"DEBUG: Comando {texto} detectado. Validando privilégios...")
                    
                    if verificar_se_eh_admin(chat_id_origem, user_id):
                        user_name = msg["from"].get("first_name", "Admin")
                        
                        if texto in ["/bemvindo", "/start"]:
                            msg_admin = (
                                f"👋 **Fala, time! GOOOOOOL!**\n\n"
                                "Sejam bem-vindos ao **VAR do Lucro**! 🟢\n\n"
                                "Aqui o nosso robô analisa lesões, escalações e o clima para mandar a bola direto no gol aberto.\n\n"
                                "🚀 Fiquem atentos às notificações e boa resenha a todos!"
                            )
                            enviar_telegram(msg_admin, chat_id_origem)
                        elif texto == "/bomdia":
                            msg_admin = (
                                "☀️ **Bom dia, time de Campeões!**\n\n"
                                "O gramado já está cortado e o VAR do Lucro está mapeando as melhores oportunidades de hoje. "
                                "Fiquem de olho que vem Green por aí! 🚀💸"
                            )
                            enviar_telegram(msg_admin, chat_id_origem)
                        
                        print(f"DEBUG: Comando {texto} executado com sucesso pelo admin {user_name}.")
                        comando_executado = True
                    else:
                        print(f"DEBUG: Usuário {user_id} tentou usar o comando {texto} mas não é Admin. Ignorado.")

    except Exception as e:
        print(f"⚠️ Erro ao processar updates do Telegram: {e}")
    
    return comando_executado

# --- Função de Análise com IA ---
def analisar_com_ia_e_dados(jogo_dados, liga_nome):
    casa = jogo_dados['teams']['home']['name']
    fora = jogo_dados['teams']['away']['name']
    
    prompt = f"""
    Você é o 'VAR do Lucro', um analista de apostas de elite. Missão: achar 'Value Bets' em {casa} vs {fora} ({liga_nome}).
    SUGIRA 3 MERCADOS (se houver valor):
    1. RESULTADO FINAL.
    2. GOLS.
    3. ESTATÍSTICAS.
    REGRAS: > 65% de confiança. Justificativa curta (máx 15 palavras). Formato: [Mercado]: [Sugestão] (Confiança: X%) - [Justificativa].
    """
    try:
        response = model.generate_content(prompt)
        return response.text if response.text else "⚠️ IA não retornou análise."
    except Exception as e:
        return f"⚠️ Erro na análise da IA: {str(e)}"

# --- Execução Principal de Análise (Programada) ---
def executar_analise():
    hora_utc = datetime.utcnow()
    hora_brt = hora_utc - timedelta(hours=3)
    
    if 5 <= hora_brt.hour < 7:
        janela_horas = 9  
        print("🌅 Rodada Manhã. Janela de 9 horas.")
    elif 12 <= hora_brt.hour < 14:
        janela_horas = 11 
        print("☀️ Rodada Tarde. Janela de 11 horas.")
    else:
        janela_horas = 12 
        print("⚠️ Rodando fora da janela padrão. Janela de 12 horas.")

    url_api = "https://v3.football.api-sports.io/fixtures"
    headers = {'x-apisports-key': API_FOOTBALL_KEY}
    params = {'date': hora_brt.strftime('%Y-%m-%d')}
    
    try:
        resposta = requests.get(url_api, headers=headers, params=params, timeout=15)
        jogos = resposta.json().get('response', [])
        print(f"DEBUG: Pacote recebido: {len(jogos)} jogos no mundo.")
    except Exception as e:
        print(f"❌ Erro na API: {e}")
        return

    agora_utc = datetime.utcnow()
    limite_utc = agora_utc + timedelta(hours=janela_horas)
    
    jogos_validos = []
    for j in jogos:
        try:
            fixture_date_utc = datetime.strptime(j['fixture']['date'], '%Y-%m-%dT%H:%M:%S+00:00')
            if (j['league']['id'] in LIGAS_PRIORITARIAS and 
                j['fixture']['status']['short'] == 'NS' and 
                agora_utc <= fixture_date_utc <= limite_utc):
                jogos_validos.append(j)
        except: continue

    print(f"DEBUG: Após filtro VIP, restaram {len(jogos_validos)} jogos.")

    if not jogos_validos:
        enviar_telegram("⚠️ Nenhuma oportunidade VIP encontrada nas próximas horas. O VAR segue de olho...")
        return

    enviar_telegram("⚽ O VAR do Lucro entrou em campo! Analisando os lances de hoje...")

    for jogo in jogos_validos:
        liga = traduzir(jogo['league']['name'])
        casa = traduzir(jogo['teams']['home']['name'])
        fora = traduzir(jogo['teams']['away']['name'])
        
        analise = analisar_com_ia_e_dados(jogo, liga)
        msg_final = f"🔍 *RELATÓRIO DE INTELIGÊNCIA*\n⚽ *{casa}* vs *{fora}*\n🏆 {liga}\n\n{analise}\n\n👉 *Aposta sugerida? Confira na sua Casa favorita!*"
        enviar_telegram(msg_final)
        time.sleep(2) 

# --- Resumo do Dia ---
def enviar_resumo_do_dia():
    hora_brt = datetime.utcnow() - timedelta(hours=3)
    url_api = "https://v3.football.api-sports.io/fixtures"
    headers = {'x-apisports-key': API_FOOTBALL_KEY}
    params = {'date': hora_brt.strftime('%Y-%m-%d')}
    
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
    # 1. Verifica se há comandos recentes de admins ou novos membros para saudar
    foi_comando_manual = processar_updates()
    
    # 2. Se a execução foi para responder a um comando manual recente, paramos por aqui
    if foi_comando_manual:
        print("DEBUG: Execução manual de comando concluída com sucesso. Pulando rotina agendada.")
    else:
        # Se não foi comando manual, segue a rotina programada por horário do cron
        hora_brt = datetime.utcnow() - timedelta(hours=3)
        
        if hora_brt.hour >= 23 or hora_brt.hour < 1:
            enviar_resumo_do_dia()
        elif 5 <= hora_brt.hour < 21:
            executar_analise()
