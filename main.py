if __name__ == "__main__":
    # Teste de conexão imediato
    enviar_telegram("🤖 O VAR do Lucro iniciou a verificação do sistema!")
    
    checar_comandos_e_saudar()
    hora_brt = datetime.now(timezone.utc) - timedelta(hours=3) # Ajustado para o aviso do log
    
    if 5 <= hora_brt.hour < 21:
        executar_analise()
    else:
        enviar_telegram("💤 O VAR do Lucro está em repouso (fora da janela de análise).")
