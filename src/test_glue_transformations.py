#!/usr/bin/env python3
"""
Teste das Transformações do Glue ETL
Simula localmente as transformações que serão aplicadas no AWS Glue
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys

def create_sample_data():
    """Cria dados de exemplo simulando dados da B3"""
    np.random.seed(42)
    
    # Símbolos de ações brasileiras
    symbols = ['PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'ABEV3', 'WEGE3', 'MGLU3', 'JBSS3']
    companies = ['PETROBRAS', 'VALE', 'ITAU UNIBANCO', 'BRADESCO', 'AMBEV', 'WEG', 'MAGAZINE LUIZA', 'JBS']
    
    data = []
    
    # Gerar dados para cada símbolo
    for i, (symbol, company) in enumerate(zip(symbols, companies)):
        # Preço base para cada ação
        base_price = np.random.uniform(10, 100)
        
        # Gerar múltiplos registros por ação (simulando diferentes horários)
        for j in range(np.random.randint(3, 8)):
            # Variação de preço
            price_variation = np.random.uniform(-0.05, 0.05)
            current_price = base_price * (1 + price_variation)
            
            record = {
                'codigo_negociacao': symbol,
                'nome_empresa': company,
                'preco_abertura': round(current_price * np.random.uniform(0.98, 1.02), 2),
                'preco_maximo': round(current_price * np.random.uniform(1.00, 1.05), 2),
                'preco_minimo': round(current_price * np.random.uniform(0.95, 1.00), 2),
                'preco_ultimo_negocio': round(current_price, 2),
                'volume_total_negociado': round(np.random.uniform(100000, 5000000), 2),
                'numero_negocios': np.random.randint(50, 500),
                'quantidade_papeis_negociados': np.random.randint(1000, 100000),
                'year': 2025,
                'month': 1,
                'day': 15
            }
            data.append(record)
    
    return pd.DataFrame(data)

def apply_transformation_a(df):
    """
    Transformação A: Agrupamento numérico com sumarização
    """
    print("Aplicando Transformação A: Agrupamento e Sumarização")
    
    # Agrupar por código de negociação e nome da empresa
    grouped = df.groupby(['codigo_negociacao', 'nome_empresa']).agg({
        'volume_total_negociado': 'sum',
        'numero_negocios': 'sum', 
        'quantidade_papeis_negociados': 'sum',
        'preco_ultimo_negocio': 'mean',
        'preco_maximo': 'max',
        'preco_minimo': 'min',
        'preco_abertura': 'first',
        'year': 'first',
        'month': 'first',
        'day': 'first'
    }).reset_index()
    
    # Renomear colunas agregadas
    grouped.columns = [
        'codigo_negociacao', 'nome_empresa',
        'volume_total_agregado', 'total_negocios', 'quantidade_total_papeis',
        'preco_medio_ponderado', 'preco_maximo_dia', 'preco_minimo_dia',
        'preco_abertura_primeiro', 'year', 'month', 'day'
    ]
    
    # Adicionar contagem de registros
    count_df = df.groupby(['codigo_negociacao', 'nome_empresa']).size().reset_index(name='numero_registros_agregados')
    grouped = grouped.merge(count_df, on=['codigo_negociacao', 'nome_empresa'])
    
    # Adicionar preço de fechamento (último negócio)
    last_price = df.groupby(['codigo_negociacao', 'nome_empresa'])['preco_ultimo_negocio'].last().reset_index()
    last_price.columns = ['codigo_negociacao', 'nome_empresa', 'preco_fechamento_ultimo']
    grouped = grouped.merge(last_price, on=['codigo_negociacao', 'nome_empresa'])
    
    print(f"Dados agrupados: {len(grouped)} registros")
    print("Colunas após agrupamento:", grouped.columns.tolist())
    
    return grouped

def apply_transformation_b(df):
    """
    Transformação B: Renomear duas colunas (além das de agrupamento)
    """
    print("Aplicando Transformação B: Renomeação de Colunas")
    
    # Renomear duas colunas conforme requisito
    df_renamed = df.rename(columns={
        'volume_total_agregado': 'vol_financeiro_total',
        'quantidade_total_papeis': 'qtd_acoes_negociadas'
    })
    
    print("Colunas renomeadas:")
    print("- volume_total_agregado → vol_financeiro_total")
    print("- quantidade_total_papeis → qtd_acoes_negociadas")
    
    return df_renamed

def apply_transformation_c(df):
    """
    Transformação C: Cálculos com campos de data
    """
    print("Aplicando Transformação C: Cálculos com Datas")
    
    # Criar coluna de data
    df['data_pregao'] = pd.to_datetime(df[['year', 'month', 'day']])
    
    # Cálculos com datas
    df['dia_semana'] = df['data_pregao'].dt.dayofweek + 1  # 1=Segunda, 7=Domingo
    df['dia_ano'] = df['data_pregao'].dt.dayofyear
    df['semana_ano'] = df['data_pregao'].dt.isocalendar().week
    df['trimestre'] = df['data_pregao'].dt.quarter
    
    # Cálculos de diferença de datas
    inicio_ano = pd.to_datetime(f"{df['year'].iloc[0]}-01-01")
    fim_ano = pd.to_datetime(f"{df['year'].iloc[0]}-12-31")
    
    df['dias_desde_inicio_ano'] = (df['data_pregao'] - inicio_ano).dt.days
    df['dias_ate_fim_ano'] = (fim_ano - df['data_pregao']).dt.days
    
    # Comparações de data
    df['eh_inicio_mes'] = df['day'] <= 5
    df['eh_fim_mes'] = df['day'] >= 25
    
    print("Cálculos de data adicionados:")
    print("- dia_semana, dia_ano, semana_ano, trimestre")
    print("- dias_desde_inicio_ano, dias_ate_fim_ano")
    print("- eh_inicio_mes, eh_fim_mes")
    
    return df

def add_calculated_metrics(df):
    """Adiciona métricas calculadas adicionais"""
    print("Adicionando métricas calculadas...")
    
    # Evitar divisão por zero
    df['ticket_medio'] = df['vol_financeiro_total'] / df['total_negocios'].replace(0, 1)
    
    # Variação percentual do dia
    df['variacao_percentual_dia'] = (
        (df['preco_fechamento_ultimo'] - df['preco_abertura_primeiro']) / 
        df['preco_abertura_primeiro'].replace(0, 1) * 100
    )
    
    # Amplitude de preço
    df['amplitude_preco'] = df['preco_maximo_dia'] - df['preco_minimo_dia']
    
    # Volatilidade relativa
    df['volatilidade_relativa'] = (
        df['amplitude_preco'] / df['preco_medio_ponderado'].replace(0, 1) * 100
    )
    
    # Adicionar símbolo para particionamento
    df['symbol'] = df['codigo_negociacao']
    
    print("Métricas calculadas adicionadas:")
    print("- ticket_medio, variacao_percentual_dia")
    print("- amplitude_preco, volatilidade_relativa")
    
    return df

def save_results(df, output_dir):
    """Salva resultados em formato parquet com particionamento"""
    print(f"Salvando resultados em: {output_dir}")
    
    # Criar diretório se não existir
    os.makedirs(output_dir, exist_ok=True)
    
    # Salvar por partição (símbolo)
    for symbol in df['symbol'].unique():
        symbol_df = df[df['symbol'] == symbol]
        
        # Criar estrutura de particionamento
        year = symbol_df['year'].iloc[0]
        month = symbol_df['month'].iloc[0]
        day = symbol_df['day'].iloc[0]
        
        partition_dir = f"{output_dir}/year={year}/month={month:02d}/day={day:02d}/symbol={symbol}"
        os.makedirs(partition_dir, exist_ok=True)
        
        # Salvar arquivo parquet
        file_path = f"{partition_dir}/data.parquet"
        symbol_df.to_parquet(file_path, index=False)
        
        print(f"Salvo: {file_path} ({len(symbol_df)} registros)")

def generate_summary_report(df):
    """Gera relatório de resumo das transformações"""
    print("\n" + "="*60)
    print("RELATÓRIO DE RESUMO DAS TRANSFORMAÇÕES")
    print("="*60)
    
    print(f"Total de ações processadas: {len(df)}")
    print(f"Volume financeiro total: R$ {df['vol_financeiro_total'].sum():,.2f}")
    print(f"Número total de negócios: {df['total_negocios'].sum():,}")
    print(f"Quantidade total de ações: {df['qtd_acoes_negociadas'].sum():,}")
    
    print("\nTop 5 ações por volume:")
    top_volume = df.nlargest(5, 'vol_financeiro_total')[['codigo_negociacao', 'vol_financeiro_total']]
    for _, row in top_volume.iterrows():
        print(f"- {row['codigo_negociacao']}: R$ {row['vol_financeiro_total']:,.2f}")
    
    print("\nMaior variação percentual:")
    max_var = df.loc[df['variacao_percentual_dia'].abs().idxmax()]
    print(f"- {max_var['codigo_negociacao']}: {max_var['variacao_percentual_dia']:.2f}%")
    
    print("\nMaior volatilidade relativa:")
    max_vol = df.loc[df['volatilidade_relativa'].idxmax()]
    print(f"- {max_vol['codigo_negociacao']}: {max_vol['volatilidade_relativa']:.2f}%")
    
    print("\nColunas finais:", df.columns.tolist())
    print(f"Registros finais: {len(df)}")

def main():
    """Função principal de teste"""
    print("Testando Transformações do AWS Glue ETL")
    print("="*50)
    
    # 1. Criar dados de exemplo
    print("1. Criando dados de exemplo...")
    df = create_sample_data()
    print(f"Dados criados: {len(df)} registros")
    print("Colunas iniciais:", df.columns.tolist())
    print("\nAmostra dos dados:")
    print(df.head())
    
    # 2. Aplicar Transformação A (Agrupamento)
    print("\n" + "="*50)
    df = apply_transformation_a(df)
    
    # 3. Aplicar Transformação B (Renomeação)
    print("\n" + "="*50)
    df = apply_transformation_b(df)
    
    # 4. Aplicar Transformação C (Cálculos de Data)
    print("\n" + "="*50)
    df = apply_transformation_c(df)
    
    # 5. Adicionar métricas calculadas
    print("\n" + "="*50)
    df = add_calculated_metrics(df)
    
    # 6. Salvar resultados
    print("\n" + "="*50)
    output_dir = "../data/refined"
    save_results(df, output_dir)
    
    # 7. Gerar relatório
    generate_summary_report(df)
    
    print("\n✅ Teste das transformações concluído com sucesso!")
    
    return df

if __name__ == "__main__":
    result_df = main()

