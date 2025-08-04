#!/usr/bin/env python3
"""
Teste do B3 Data Scraper
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd

# Adicionar o diretório src ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from b3_scraper import B3DataScraper

def test_scraper():
    """Testa o scraper com dados de exemplo"""
    print("Testando B3 Data Scraper...")
    
    # Criar dados de exemplo (simulando dados da B3)
    sample_data = {
        'codigo_negociacao': ['PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'ABEV3'],
        'nome_empresa': ['PETROBRAS', 'VALE', 'ITAU UNIBANCO', 'BRADESCO', 'AMBEV'],
        'preco_abertura': [25.50, 65.30, 22.80, 18.90, 14.20],
        'preco_maximo': [26.10, 66.50, 23.20, 19.30, 14.50],
        'preco_minimo': [25.20, 64.80, 22.60, 18.70, 14.10],
        'preco_ultimo_negocio': [25.80, 65.90, 23.00, 19.10, 14.35],
        'volume_total_negociado': [1500000.00, 2300000.00, 1800000.00, 1200000.00, 900000.00],
        'numero_negocios': [1250, 1890, 1560, 980, 750]
    }
    
    # Criar DataFrame
    df = pd.DataFrame(sample_data)
    print(f"DataFrame criado com {len(df)} registros")
    print(df.head())
    
    # Testar salvamento em parquet
    scraper = B3DataScraper(local_path="./data/raw")
    test_date = datetime.now().date()
    
    try:
        file_path = scraper.save_to_parquet(df, test_date)
        print(f"Arquivo salvo com sucesso: {file_path}")
        
        # Verificar se o arquivo foi criado
        if file_path and file_path.exists():
            # Ler o arquivo para verificar
            df_read = pd.read_parquet(file_path)
            print(f"Arquivo lido com sucesso: {len(df_read)} registros")
            print("Colunas:", df_read.columns.tolist())
            return True
        else:
            print("Erro: arquivo não foi criado")
            return False
            
    except Exception as e:
        print(f"Erro durante o teste: {e}")
        return False

if __name__ == "__main__":
    success = test_scraper()
    if success:
        print("✅ Teste do scraper passou!")
    else:
        print("❌ Teste do scraper falhou!")
        sys.exit(1)

