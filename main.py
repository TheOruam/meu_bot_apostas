import os
import requests
import google.generativeai as genai
import random
import json
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

# --- Configurações Principais ---
# Buscamos os tokens das variáveis de ambiente do GitHub Secrets
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID') # ID do seu Canal (Ex: -100xxxxxxxxxx)
API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# --- Configuração das Ligas Priorities ---
# Incluindo Brasileirão A, B, Copa do Brasil, Libertadores, Sulamericana e principais Europeias
LIGAS_PRIORITARIAS = [1, 2, 3, 13, 71, 72, 73, 39, 140, 135, 78, 61, 848, 866]

# --- Inicialização da IA ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# --- Funções Utilitárias ---
def enviar_telegram(texto, chat_id=CHAT_ID):
    if not TELEGRAM_TOKEN or not chat_id:
        print("❌ Erro: TELEGRAM_TOKEN ou CHAT_ID não configurados.")
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
    except Exception as e:
        print(f"⚠️ Erro na tradução: {e}")
        return texto

# --- Função de Boas-Vindas (/start) ---
def checar_comandos_e_saudar():
    """Verifica se novos usuários enviaram /start no privado e responde."""
    if not TELEGRAM_TOKEN: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    try:
        resposta = requests.get(url, timeout=10).json()
        if "result" in resposta:
            for update in resposta["result"]:
                if "message" in update and update["message"].get("text") == "/start":
                    user_id = update["message"]["chat"]["id"]
                    user_name = update["message"]["from"].get("first_name", "Craque")
                    
                    msg_boas_vindas = (
                        f"👋 **Fala, {user_name}! GOOOOOOL!**\n\n"
                        "Seja bem-vindo ao **VAR do Lucro**, o único lugar onde o VAR nunca erra o impedimento e a gente só comemora Green! 🟢\n\n"
                        "Você acaba de ser escalado para o time que não vive de palpite, vive de análise! Nosso robô é um 'fominha' por dados: ele varre os campos, checa o clima, verifica as lesões e só te manda a bola quando o gol está aberto.\n\n"
                        "🚀 **Como jogar com a gente:**\n"
                        "1. **Ative as notificações:** Quando o VAR apitar, é porque a oportunidade é de ouro.\n"
                        "2. **Não inventa moda:** O robô sabe o que faz, segue a gestão que o Green vem!\n"
                        "3. **Resenha liberada:** Pode comemorar o lucro aqui no grupo.\n\n"
                        "O árbitro já autorizou a saída de bola. Vamos pra cima da banca? 💰🔥"
                    )
                    enviar_telegram(msg_boas_vindas, user_id)
    except Exception as e:
        print(f"⚠️ Erro ao checar comandos: {e}")

# --- Função de Análise com IA ---
def analisar_com_ia_e_dados(jogo_dados, liga_nome):
    casa = jogo_dados['teams']['home']['name']
    fora = jogo_dados['teams']['away']['name']
    
    prompt = f"""
    Você é o 'VAR do Lucro', um analista de apostas de elite. Sua missão é identificar 'Value Bets' (apostas de valor) no confronto: {casa} vs {fora} ({liga_nome}).
    
    Use seu conhecimento de dados reais (lesões, escalações, clima, notícias recentes) para decidir.
    
    SUGIRA 3 MERCADOS (se houver valor):
    1. RESULTADO FINAL (1x2 ou Handicap Asiático).
    2. GOLS (Over/Under ou Ambas Marcam).
    3. ESTATÍSTICAS (Escanteios ou Cartões).
    
    REGRAS DE OURO:
    - Só sugira um mercado se tiver > 65% de confiança estatística.
    - Dê uma justificativa técnica curta (máx. 15 palavras) para cada mercado.
    - Se o jogo for imprevisível, indique apenas: "Jogo de alta incerteza. Evitar apostas."
    
    FORMATO DE RESPOSTA (Obrigatório):
    [Nome do Mercado]: [Sugestão] (Confiança: X%) - [Justificativa].
    """
    try:
        response = model.generate_content(prompt)
        return response.text if response.text else "⚠️ IA não retornou análise."
    except Exception as e:
        return f"⚠️ Erro na análise da IA: {str(e)}"

# --- Função Principal de Execução de Análises ---
def executar_analise():
    """Busca jogos do dia e envia análises baseada na janela de horário."""
    
    # 1. Obter hora atual de Brasília (BRT)
    # GitHub Actions roda em UTC. BRT é UTC-3.
    hora_utc = datetime.utcnow()
    hora_brt = hora_utc - timedelta(hours=3)
    
    print(f"🕒 Execução iniciada. Hora atual BRT: {hora_brt.strftime('%H:%M')}")
    
    # 2. Definir a Janela de Análise baseada na rodada
    # Rodada 1 (06:00 BRT): Analisa jogos das próximas 10 horas (cobre manhã e início da tarde)
    if 5 <= hora_brt.hour < 7:
        janela_horas = 10
        print("🌅 Rodada Manhã. Janela de 10 horas.")
    # Rodada 2 (13:00 BRT): Analisa jogos das próximas 10 horas (cobre tarde e noite)
    elif 12 <= hora_brt.hour < 14:
        janela_horas = 10
        print("☀️ Rodada Tarde. Janela de 10 horas.")
    # Evitar execuções fora do horário ou se o cron furar
    else:
        print("⛔ Horário fora das rodadas de análise. Pulando.")
        return

    # 3. Mensagem inicial divertida
    frases_inicio = [
        "⚽ O VAR do Lucro entrou em campo! Analisando os lances de hoje...",
        "🏃‍♂️ Corrida para o Green iniciada! O Robô está varrendo os campos...",
        "🧐 Olho no lance! O VAR do Lucro está revisando as odds da Bet365...",
        "🏆 Bola rolando e o VAR na espreita. Buscando o gol da vitória...",
        "⚡ Escalação definida: O VAR do Lucro está pronto para buscar o lucro!"
    ]
    enviar_telegram(random.choice(frases_inicio))
    
    # 4. Buscar Jogos na API
    data_hoje = hora_brt.strftime('%Y-%m-%d')
    url_api = "https://v3.football.api-sports.io/fixtures"
    headers = {'x-apisports-key': API_FOOTBALL_KEY}
    params = {'date': data_hoje}
    
    try:
        resposta = requests.get(url_api, headers=headers, params=params, timeout=15)
        jogos = resposta.json().get('response', [])
    except Exception as e:
        enviar_telegram(f"❌ Erro crítico ao conectar na API de Futebol: {e}")
        return

    # 5. Filtrar jogos prioritários, não iniciados e dentro da janela
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

    if not jogos_validos:
        enviar_telegram("⚠️ Nenhuma oportunidade de valor encontrada nas próximas horas. O VAR segue monitorando...")
        return

    # 6. Analisar e enviar cada jogo
    for jogo in jogos_validos:
        liga = traduzir(jogo['league']['name'])
        casa_nome = traduzir(jogo['teams']['home']['name'])
        fora_nome = traduzir(jogo['teams']['away']['name'])
        
        print(f"🔍 Analisando: {casa_nome} vs {fora_nome} ({liga})...")
        
        analise = analisar_com_ia_e_dados(jogo, liga)
        
        msg_final = (
            f"🔍 *RELATÓRIO DE INTELIGÊNCIA*\n"
            f"⚽ *{casa_nome}* vs *{fora_nome}*\n"
            f"🏆 {liga}\n\n"
            f"{analise}\n\n"
            f"👉 *Aposta sugerida? Confira agora na Bet365!*"
        )
        enviar_telegram(msg_final)

# --- Função de Resumo do Dia ---
def enviar_resumo_do_dia():
    """Busca jogos finalizados das ligas prioritárias e envia o placar."""
    # Pegamos a data de Brasília
    hora_brt = datetime.utcnow() - timedelta(hours=3)
    data_hoje = hora_brt.strftime('%Y-%m-%d')
    
    print(f"📊 Iniciando resumo do dia: {data_hoje}")
    
    url_api = "https://v3.football.api-sports.io/fixtures"
    headers = {'x-apisports-key': API_FOOTBALL_KEY}
    params = {'date': data_hoje}
    
    try:
        resposta = requests.get(url_api, headers=headers, params=params, timeout=15)
        jogos = resposta.json().get('response', [])
    except Exception as e:
        print(f"❌ Erro ao buscar resumo: {e}")
        return

    # Filtrar apenas jogos finalizados (FT) das ligas prioritárias
    jogos_finalizados = [j for j in jogos if j['league']['id'] in LIGAS_PRIORITARIAS and j['fixture']['status']['short'] == 'FT']

    if not jogos_finalizados:
        return # Sem jogos para resumir

    msg = "🏁 *FECHAMENTO DO VAR: BALANÇO DO DIA*\n\n"
    for jogo in jogos_finalizados:
        casa = traduzir(jogo['teams']['home']['name'])
        fora = traduzir(jogo['teams']['away']['name'])
        gols_casa = jogo['goals']['home']
        gols_fora = jogo['goals']['away']
        
        msg += f"⚽ {casa} *{gols_casa} x {gols_fora}* {fora}\n"
    
    msg += "\n*O dia encerrou! O VAR revisou as estatísticas e agora é hora de descansar para os Greens de amanhã.* 🚀"
    enviar_telegram(msg)

# --- Fluxo Principal (Ponto de Entrada) ---
if __name__ == "__main__":
    # 1. Sempre tenta saudar novos usuários que deram /start no privado
    checar_comandos_e_saudar()
    
    # 2. Define ação baseada na hora de Brasília
    hora_utc = datetime.utcnow()
    hora_brt = hora_utc - timedelta(hours=3)
    
    # Decisão inteligente do Bot
    if hora_brt.hour >= 23 or hora_brt.hour < 1:
        # Entre 23:00 e 00:59: Envia o Resumo
        enviar_resumo_do_dia()
    elif 5 <= hora_brt.hour < 21:
        # Entre 05:00 e 20:59: Executa Análises (cobre as 2 rodadas)
        executar_analise()
