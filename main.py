import requests
import os

TOKEN = '8983808854:AAH36YnSLE2ACY_1s5wSDhxQgCUbs66VzlA'
ID = '747956770'

try:
    print("Tentando disparar mensagem...")
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    res = requests.post(url, json={"chat_id": ID, "text": "TESTE DE COMUNICAÇÃO GitHub->Telegram"})
    print(f"Resposta do Telegram: {res.status_code}")
    print(res.text)
except Exception as e:
    print(f"Erro no disparo: {e}")
