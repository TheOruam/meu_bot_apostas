import os
import time
from datetime import datetime, timedelta, timezone
import requests
from flask import Flask
from threading import Thread
from deep_translator import GoogleTranslator

# IMPORTA AS FUNÇÕES DO SEU NOVO ARQUIVO DE COMANDOS
from comandos import processar_updates, enviar_telegram

# Configurações do Main
API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY')
CHAT_ID = os.getenv('CHAT_ID')
LIGAS_PRIORITARIAS = [1, 2, 3, 13, 71, 72, 73, 39, 140, 135, 78, 61, 848, 866]

# Servidor Fantasma para o Render
app = Flask(__name__)
@app.route('/')
def home(): return "VAR do Lucro está Online!"
def run_server(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run_server, daemon=True).start()

def traduzir(texto):
    if not texto: return ""
    try: return GoogleTranslator(source='auto', target='pt').translate(texto)
    except: return texto

def analisar_com_ia_e_dados(jogo, liga):
    # Função tampão. Coloque sua lógica de análise profunda aqui.
    return "📊 Análise técnica em processamento..."

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

    if not jogos_na_janela: return

    enviar_telegram("⚽ O VAR do Lucro encontrou lances que vão começar em 1 hora! Gerando relatórios...", CHAT_ID)

    for jogo in jogos_na_janela:
        liga = traduzir(jogo['league']['name'])
        casa = traduzir(jogo['teams']['home']['name'])
        fora = traduzir(jogo['teams']['away']['name'])
        analise = analisar_com_ia_e_dados(jogo, liga)
        
        msg_final = (f"🚨 <b>LANCE DE OURO DETECTADO!</b>\n\n⚽ <b>{casa}</b> vs <b>{fora}</b>\n🏆 {liga}\n"
                     f"⏳ <i>O jogo começa em cerca de 1 hora!</i>\n\n{analise}\n\n"
                     f"👉 <b>Aposta sugerida? Confira na sua Casa favorita!</b>")
        enviar_telegram(msg_final, CHAT_ID)
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
    enviar_telegram(msg, CHAT_ID)

if __name__ == "__main__":
    keep_alive()
    offset = None
    ultima_hora = None
    
    print("🚀 VAR do Lucro Iniciado! Escutando comandos e analisando a API de Futebol...")
    
    while True:
        try:
            # Passamos a função buscar_e_analisar_jogos como parâmetro para que o /update consiga ativá-la
            offset = processar_updates(offset, buscar_e_analisar_jogos)
            
            hora_brt = datetime.now(timezone.utc) - timedelta(hours=3)
            
            # GATILHO INFALÍVEL: Verifica apenas se a hora mudou (Ex: de 13 para 14).
            if ultima_hora is None or hora_brt.hour != ultima_hora:
                # Na primeira vez que ligar (ultima_hora is None), ele não manda nada, apenas registra a hora atual.
                if ultima_hora is not None:
                    if hora_brt.hour == 23:
                        enviar_resumo_do_dia()
                    else:
                        buscar_e_analisar_jogos()
                
                ultima_hora = hora_brt.hour
                
            time.sleep(5)
        except Exception as e:
            print(f"⚠️ Erro no loop: {e}")
            time.sleep(10)
