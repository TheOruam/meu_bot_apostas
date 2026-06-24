import os
import google.generativeai as genai

# Carrega a chave
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

# Diagnóstico: Imprime todos os modelos disponíveis na sua conta
print("--- MODELOS DISPONÍVEIS NA SUA CONTA ---")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"Nome do modelo: {m.name}")
print("----------------------------------------")
