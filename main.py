import os
import requests
import time
import json
from datetime import datetime, timedelta, timezone
from deep_translator import GoogleTranslator
from google import genai

# --- Configurações Principais ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# --- Ligas VIPs ---
# 1 = Copa do Mundo 2026
LIGAS_PRIORITARIAS = [1, 2, 3, 13, 71, 72, 73, 39, 140, 135, 78, 61, 848, 866]

# Copa do Mundo usa temporada 2026; todas as outras usam a temporada atual
LIGAS_TEMPORADA_2026 = [1]

# --- Arquivo de armazenamento de agendamentos ---
ARQUIVO_AGENDAMENTOS = "agendamentos_jogos.json"

# --- Inicialização da IA ---
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None



# --- CORRIGIDO 1: Detecta temporada dinamicamente ---
def detectar_temporada(liga_id):
    """Retorna 2026 para a Copa do Mundo, 2025 para todas as outras ligas."""
    if liga_id in LIGAS_TEMPORADA_2026:
        return 2026
    return 2025


# --- Funções Utilitárias ---
def enviar_telegram(texto, chat_id=CHAT_ID):
    if not TELEGRAM_TOKEN or not chat_id:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    texto_seguro = texto.replace('*', '').replace('_', '')
    payload = {"chat_id": chat_id, "text": texto_seguro, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            print(f"Telegram rejeitou o HTML. Reenviando texto puro... Erro: {r.text}")
            payload.pop("parse_mode", None)
            payload["text"] = (texto_seguro
                               .replace('<b>', '').replace('</b>', '')
                               .replace('<i>', '').replace('</i>', ''))
            requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Erro de conexão com o Telegram: {e}")


def traduzir(texto):
    if not texto:
        return ""
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
    except:
        return False
    return False


# --- Central de Updates ---
def processar_updates():
    if not TELEGRAM_TOKEN:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    comando_executado = False
    try:
        resposta = requests.get(url, timeout=10).json()
        if "result" not in resposta:
            return False

        agora_timestamp = time.time()

        for update in resposta["result"]:
            if "message" not in update:
                continue
            msg = update["message"]
            chat_id_origem = msg["chat"]["id"]
            user_id = msg["from"]["id"]
            msg_date = msg["date"]

            if "new_chat_members" in msg and (agora_timestamp - msg_date < 32400):
                for novo_membro in msg["new_chat_members"]:
                    if novo_membro.get("is_bot"):
                        continue
                    nome_membro = novo_membro.get("first_name", "Craque")
                    msg_boas_vindas = (
                        f"Fala, {nome_membro}! GOOOOOOL!\n\n"
                        f"Seja bem-vindo ao VAR do Lucro!\n"
                        f"Você acaba de entrar para o time que não vive de palpite, vive de análise técnica de verdade.\n\n"
                        f"Regras de jogo:\n"
                        f"1. Deixe as notificações ativadas para não perder os lances de ouro.\n"
                        f"2. Siga a gestão de banca.\n\n"
                        f"Vamos pra cima da banca!"
                    )
                    enviar_telegram(msg_boas_vindas, chat_id_origem)

            if "text" in msg:
                texto = msg["text"].lower().strip()
                if agora_timestamp - msg_date > 600:
                    continue

                if texto in ["/bomdia", "/bemvindo", "/start"] and verificar_se_eh_admin(chat_id_origem, user_id):
                    if texto in ["/bemvindo", "/start"]:
                        enviar_telegram("Fala, time! GOOOOOOL!\n\nSejam bem-vindos ao VAR do Lucro!\n\nAqui o nosso robô analisa lesões, escalações e o clima para mandar as melhores...")
                    elif texto == "/bomdia":
                        enviar_telegram("Bom dia, time de Campeões!\n\nO gramado já está cortado e o VAR do Lucro está mapeando as melhores oportunidades de hoje. Fiquem de olho!")
                    comando_executado = True
    except:
        pass
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
    1. PLACAR MAIS PROVÁVEL: [Palpite]
    2. MERCADOS COM MAIS VALOR: [1-3 mercados com justificativa técnica]
    3. GRAU DE CONFIANÇA: [Nota 0-10]
    4. PRINCIPAIS RISCOS DA ENTRADA: [Riscos]
    """
    if not client:
        return "IA não configurada (GEMINI_API_KEY ausente)."
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text if response.text else "IA não retornou análise."
    except Exception as e:
        return f"Erro na análise da IA: {str(e)}"


# --- Carregar agendamentos do arquivo ---
def carregar_agendamentos():
    try:
        if os.path.exists(ARQUIVO_AGENDAMENTOS):
            with open(ARQUIVO_AGENDAMENTOS, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}


# --- Salvar agendamentos no arquivo ---
def salvar_agendamentos(agendamentos):
    try:
        with open(ARQUIVO_AGENDAMENTOS, 'w') as f:
            json.dump(agendamentos, f, indent=2)
    except Exception as e:
        print(f"Erro ao salvar agendamentos: {e}")


# --- Buscar jogos do dia por liga (com temporada correta) ---
def buscar_jogos_do_dia():
    hora_brt = datetime.now(timezone.utc) - timedelta(hours=3)
    headers = {'x-apisports-key': API_FOOTBALL_KEY}
    todos_jogos = []

    # CORRIGIDO 1: Busca separada por liga com a temporada correta
    for liga_id in LIGAS_PRIORITARIAS:
        temporada = detectar_temporada(liga_id)
        params = {
            'date': hora_brt.strftime('%Y-%m-%d'),
            'league': liga_id,
            'season': temporada,
            'timezone': 'America/Sao_Paulo',
        }
        print(f"Buscando liga {liga_id} (season {temporada})...")
        try:
            resposta = requests.get(
                "https://v3.football.api-sports.io/fixtures",
                headers=headers,
                params=params,
                timeout=15,
            )
            if resposta.status_code == 200:
                jogos = resposta.json().get('response', [])
                print(f"  Liga {liga_id}: {len(jogos)} jogos")
                todos_jogos.extend(jogos)
            else:
                print(f"  Liga {liga_id}: erro {resposta.status_code}")
        except Exception as e:
            print(f"  Liga {liga_id}: falha na requisição — {e}")

    print(f"Total geral encontrado: {len(todos_jogos)} jogos")
    return todos_jogos if todos_jogos else None


# --- Filtrar jogos VIP que ainda não começaram ---
def filtrar_jogos_vip(jogos):
    if not jogos:
        return []

    agora_timestamp = time.time()
    jogos_vip = []

    print(f"\nFiltrando jogos VIP...")

    for jogo in jogos:
        try:
            id_liga = jogo['league']['id']
            jogo_timestamp = jogo['fixture']['timestamp']
            status = jogo['fixture']['status']['short']
            casa = jogo['teams']['home']['name']
            fora = jogo['teams']['away']['name']

            nao_comecou = status == 'NS'
            no_futuro = jogo_timestamp > agora_timestamp

            if nao_comecou and no_futuro:
                jogos_vip.append(jogo)
                print(f"  VIP: {casa} vs {fora} (liga {id_liga})")
        except Exception as e:
            print(f"Erro ao processar jogo: {e}")
            continue

    print(f"Total de jogos VIP filtrados: {len(jogos_vip)}\n")
    return jogos_vip


# --- Agendar análises para 1 hora antes de cada jogo ---
def agendar_analises():
    print("\nINICIANDO AGENDAMENTO DE ANÁLISES...")

    jogos = buscar_jogos_do_dia()

    if jogos is None:
        enviar_telegram("Erro na API de futebol! Não consegui buscar os jogos.")
        print("Erro crítico na API")
        return

    if len(jogos) == 0:
        enviar_telegram("Nenhum jogo encontrado para hoje em nenhuma das ligas VIP.")
        print("Nenhum jogo encontrado")
        return

    jogos_vip = filtrar_jogos_vip(jogos)

    if not jogos_vip:
        enviar_telegram("Nenhum jogo VIP encontrado para hoje. O VAR volta amanhã!")
        print("Nenhum jogo VIP (mas API funcionando)")
        return

    agendamentos = carregar_agendamentos()
    agora = datetime.now(timezone.utc) - timedelta(hours=3)

    for jogo in jogos_vip:
        try:
            fixture_id = jogo['fixture']['id']
            jogo_timestamp = jogo['fixture']['timestamp']
            tempo_jogo = datetime.fromtimestamp(jogo_timestamp)
            tempo_analise = tempo_jogo - timedelta(hours=1)
            timestamp_analise = tempo_analise.timestamp()

            if timestamp_analise > agora.timestamp():
                chave = f"jogo_{fixture_id}"
                if chave not in agendamentos:
                    agendamentos[chave] = {
                        'fixture_id': fixture_id,
                        'timestamp_jogo': jogo_timestamp,
                        'timestamp_analise': timestamp_analise,
                        'tempo_jogo': tempo_jogo.strftime('%H:%M'),
                        'tempo_analise': tempo_analise.strftime('%H:%M'),
                        'casa': jogo['teams']['home']['name'],
                        'fora': jogo['teams']['away']['name'],
                        'liga': jogo['league']['name'],
                        'analisado': False,
                    }
                    print(f"Agendado: {jogo['teams']['home']['name']} vs {jogo['teams']['away']['name']}")
                    print(f"  Análise em: {tempo_analise.strftime('%H:%M')} | Jogo em: {tempo_jogo.strftime('%H:%M')}")
        except Exception as e:
            print(f"Erro ao agendar jogo: {e}")
            continue

    salvar_agendamentos(agendamentos)
    total = len([v for v in agendamentos.values() if not v['analisado']])
    print(f"Total de análises agendadas: {total}")
    enviar_telegram(f"VAR pronto! {total} jogos VIP agendados para análise hoje.")


# --- Verificar e executar análises agendadas ---
def executar_analises_agendadas():
    print("\nVERIFICANDO ANÁLISES AGENDADAS...")

    agendamentos = carregar_agendamentos()
    agora = time.time()

    # CORRIGIDO 3: Tolerância aumentada para 6 minutos (cobre atrasos do Actions)
    tolerancia = 360

    for chave, agendamento in list(agendamentos.items()):
        if agendamento['analisado']:
            continue

        timestamp_analise = agendamento['timestamp_analise']

        if agora >= timestamp_analise and agora <= (timestamp_analise + tolerancia):
            print(f"Hora de analisar: {agendamento['casa']} vs {agendamento['fora']}")

            try:
                fixture_id = agendamento['fixture_id']
                headers = {'x-apisports-key': API_FOOTBALL_KEY}
                params = {'id': fixture_id}

                resposta = requests.get(
                    "https://v3.football.api-sports.io/fixtures",
                    headers=headers,
                    params=params,
                    timeout=10,
                )
                jogos = resposta.json().get('response', [])

                if jogos:
                    jogo = jogos[0]
                    liga = traduzir(jogo['league']['name'])
                    casa = traduzir(jogo['teams']['home']['name'])
                    fora = traduzir(jogo['teams']['away']['name'])

                    print(f"IA analisando: {casa} vs {fora}...")
                    analise = analisar_com_ia_e_dados(jogo, liga)

                    msg_final = (
                        f"LANCE DE OURO DETECTADO!\n\n"
                        f"{casa} vs {fora}\n"
                        f"{liga}\n"
                        f"Jogo em 1 hora\n\n"
                        f"{analise}\n\n"
                        f"Confira na sua Casa de apostas!"
                    )
                    enviar_telegram(msg_final)

                    agendamentos[chave]['analisado'] = True
                    salvar_agendamentos(agendamentos)
                    print(f"Análise enviada para {casa} vs {fora}")

            except Exception as e:
                print(f"Erro ao analisar jogo: {e}")

        if agora > (timestamp_analise + 86400):
            del agendamentos[chave]
            salvar_agendamentos(agendamentos)


# --- Limpeza diária de agendamentos ---
def limpar_agendamentos_antigos():
    agendamentos = carregar_agendamentos()
    agora = time.time()

    chaves_remover = []
    for chave, agendamento in agendamentos.items():
        if agora > (agendamento['timestamp_jogo'] + 14400):
            chaves_remover.append(chave)

    for chave in chaves_remover:
        del agendamentos[chave]

    if chaves_remover:
        salvar_agendamentos(agendamentos)
        print(f"Limpeza: {len(chaves_remover)} agendamentos antigos removidos")


# --- Fluxo de Entrada Principal ---
if __name__ == "__main__":
    hora_brt = datetime.now(timezone.utc) - timedelta(hours=3)

    print(f"\n{'='*50}")
    print(f"VAR DO LUCRO - {hora_brt.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"{'='*50}")

    # 1. Processa comandos do Telegram
    processar_updates()

    # Agenda às 00:00 BRT OU quando não há agendamentos pendentes (primeira execução/manual)
    agendamentos_atuais = carregar_agendamentos()
    sem_pendentes = not any(not v['analisado'] for v in agendamentos_atuais.values())

    if hora_brt.hour == 0 or sem_pendentes:
        agendar_analises()

    # 3. Verifica e executa análises agendadas
    executar_analises_agendadas()

    # 4. Limpa agendamentos antigos
    limpar_agendamentos_antigos()

    print(f"Ciclo completo. Proxima execucao em 5 minutos.\n")
