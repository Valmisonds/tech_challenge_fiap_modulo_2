#!/usr/bin/env python3
"""
Athena Analytics Notebook - Tech Challenge B3
Notebook Python para análise e visualização dos dados do pregão da B3
Simula um notebook do Athena com visualizações gráficas
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import boto3
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configurar estilo dos gráficos
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class B3AthenaAnalytics:
    """Classe para análise e visualização de dados da B3 via Athena"""
    
    def __init__(self, region='us-east-1', database='tech_challenge_b3_database_dev'):
        self.region = region
        self.database = database
        self.athena_client = None
        self.s3_client = None
        
        # Dados de exemplo (em produção, viria do Athena)
        self.df = self._load_sample_data()
    
    def _load_sample_data(self):
        """Carrega dados de exemplo (simula consulta Athena)"""
        # Em produção, isso seria uma consulta real ao Athena
        np.random.seed(42)
        
        symbols = ['PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'ABEV3', 'WEGE3', 'MGLU3', 'JBSS3', 'SUZB3', 'RENT3']
        companies = ['PETROBRAS', 'VALE', 'ITAU UNIBANCO', 'BRADESCO', 'AMBEV', 'WEG', 'MAGAZINE LUIZA', 'JBS', 'SUZANO', 'LOCALIZA']
        
        data = []
        for symbol, company in zip(symbols, companies):
            record = {
                'codigo_negociacao': symbol,
                'nome_empresa': company,
                'vol_financeiro_total': np.random.uniform(5000000, 50000000),
                'total_negocios': np.random.randint(500, 5000),
                'qtd_acoes_negociadas': np.random.randint(100000, 1000000),
                'preco_medio_ponderado': np.random.uniform(10, 100),
                'preco_maximo_dia': np.random.uniform(50, 120),
                'preco_minimo_dia': np.random.uniform(8, 50),
                'preco_abertura_primeiro': np.random.uniform(20, 80),
                'preco_fechamento_ultimo': np.random.uniform(15, 85),
                'variacao_percentual_dia': np.random.uniform(-10, 10),
                'volatilidade_relativa': np.random.uniform(1, 20),
                'ticket_medio': np.random.uniform(1000, 50000),
                'amplitude_preco': np.random.uniform(2, 15),
                'data_pregao': '2025-01-15',
                'dia_semana': 3,
                'trimestre': 1
            }
            data.append(record)
        
        return pd.DataFrame(data)
    
    def query_athena(self, query):
        """Executa consulta no Athena (simulado)"""
        print(f"Executando consulta Athena: {query[:100]}...")
        # Em produção, executaria a consulta real
        return self.df
    
    def create_volume_analysis(self):
        """Análise de volume financeiro"""
        print("📊 Análise de Volume Financeiro")
        print("=" * 50)
        
        # Top 10 por volume
        top_volume = self.df.nlargest(10, 'vol_financeiro_total')
        
        # Gráfico de barras - Volume por ação
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Volume em milhões
        volumes_milhoes = top_volume['vol_financeiro_total'] / 1_000_000
        
        ax1.bar(top_volume['codigo_negociacao'], volumes_milhoes, color='steelblue')
        ax1.set_title('Volume Financeiro por Ação (Top 10)', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Código da Ação')
        ax1.set_ylabel('Volume (R$ Milhões)')
        ax1.tick_params(axis='x', rotation=45)
        
        # Gráfico de pizza - Distribuição de volume
        ax2.pie(volumes_milhoes[:5], labels=top_volume['codigo_negociacao'][:5], 
                autopct='%1.1f%%', startangle=90)
        ax2.set_title('Distribuição de Volume (Top 5)', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('../docs/volume_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Estatísticas
        print(f"Volume total do mercado: R$ {self.df['vol_financeiro_total'].sum():,.2f}")
        print(f"Volume médio por ação: R$ {self.df['vol_financeiro_total'].mean():,.2f}")
        print(f"Maior volume: {top_volume.iloc[0]['codigo_negociacao']} - R$ {top_volume.iloc[0]['vol_financeiro_total']:,.2f}")
        
        return top_volume
    
    def create_price_variation_analysis(self):
        """Análise de variação de preços"""
        print("\n📈 Análise de Variação de Preços")
        print("=" * 50)
        
        # Ordenar por variação
        df_sorted = self.df.sort_values('variacao_percentual_dia', ascending=False)
        
        # Gráfico de variação
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # Gráfico de barras - Variação percentual
        colors = ['green' if x > 0 else 'red' for x in df_sorted['variacao_percentual_dia']]
        ax1.bar(df_sorted['codigo_negociacao'], df_sorted['variacao_percentual_dia'], color=colors)
        ax1.set_title('Variação Percentual por Ação', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Código da Ação')
        ax1.set_ylabel('Variação (%)')
        ax1.tick_params(axis='x', rotation=45)
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # Histograma de distribuição de variações
        ax2.hist(self.df['variacao_percentual_dia'], bins=15, color='skyblue', alpha=0.7, edgecolor='black')
        ax2.set_title('Distribuição das Variações Percentuais', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Variação (%)')
        ax2.set_ylabel('Frequência')
        ax2.axvline(x=0, color='red', linestyle='--', alpha=0.7, label='Zero')
        ax2.legend()
        
        plt.tight_layout()
        plt.savefig('../docs/price_variation_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Estatísticas
        positive_var = self.df[self.df['variacao_percentual_dia'] > 0]
        negative_var = self.df[self.df['variacao_percentual_dia'] < 0]
        
        print(f"Ações em alta: {len(positive_var)} ({len(positive_var)/len(self.df)*100:.1f}%)")
        print(f"Ações em baixa: {len(negative_var)} ({len(negative_var)/len(self.df)*100:.1f}%)")
        print(f"Maior alta: {df_sorted.iloc[0]['codigo_negociacao']} (+{df_sorted.iloc[0]['variacao_percentual_dia']:.2f}%)")
        print(f"Maior baixa: {df_sorted.iloc[-1]['codigo_negociacao']} ({df_sorted.iloc[-1]['variacao_percentual_dia']:.2f}%)")
        
        return df_sorted
    
    def create_volatility_analysis(self):
        """Análise de volatilidade"""
        print("\n📊 Análise de Volatilidade")
        print("=" * 50)
        
        # Scatter plot - Volume vs Volatilidade
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Volume vs Volatilidade
        scatter = ax1.scatter(self.df['vol_financeiro_total']/1_000_000, 
                             self.df['volatilidade_relativa'],
                             c=self.df['variacao_percentual_dia'], 
                             cmap='RdYlGn', s=100, alpha=0.7)
        ax1.set_xlabel('Volume Financeiro (R$ Milhões)')
        ax1.set_ylabel('Volatilidade Relativa (%)')
        ax1.set_title('Volume vs Volatilidade', fontsize=14, fontweight='bold')
        plt.colorbar(scatter, ax=ax1, label='Variação (%)')
        
        # Adicionar labels das ações
        for i, row in self.df.iterrows():
            ax1.annotate(row['codigo_negociacao'], 
                        (row['vol_financeiro_total']/1_000_000, row['volatilidade_relativa']),
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        # Box plot - Volatilidade por faixa de preço
        self.df['faixa_preco'] = pd.cut(self.df['preco_medio_ponderado'], 
                                       bins=[0, 25, 50, 75, 100], 
                                       labels=['Até R$25', 'R$25-50', 'R$50-75', 'Acima R$75'])
        
        sns.boxplot(data=self.df, x='faixa_preco', y='volatilidade_relativa', ax=ax2)
        ax2.set_title('Volatilidade por Faixa de Preço', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Faixa de Preço')
        ax2.set_ylabel('Volatilidade Relativa (%)')
        
        plt.tight_layout()
        plt.savefig('../docs/volatility_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Estatísticas
        high_vol = self.df[self.df['volatilidade_relativa'] > self.df['volatilidade_relativa'].quantile(0.75)]
        print(f"Ações de alta volatilidade (>Q3): {len(high_vol)}")
        print(f"Volatilidade média: {self.df['volatilidade_relativa'].mean():.2f}%")
        print(f"Ação mais volátil: {self.df.loc[self.df['volatilidade_relativa'].idxmax(), 'codigo_negociacao']}")
        
        return high_vol
    
    def create_market_overview(self):
        """Visão geral do mercado"""
        print("\n🏢 Visão Geral do Mercado")
        print("=" * 50)
        
        # Dashboard com múltiplas métricas
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Volume por Setor', 'Distribuição de Preços', 
                          'Variação vs Volume', 'Ranking de Performance'),
            specs=[[{"type": "bar"}, {"type": "histogram"}],
                   [{"type": "scatter"}, {"type": "bar"}]]
        )
        
        # 1. Volume por "setor" (simulado)
        setores = ['Petróleo', 'Mineração', 'Bancos', 'Bancos', 'Bebidas', 
                  'Industrial', 'Varejo', 'Alimentos', 'Papel', 'Serviços']
        self.df['setor'] = setores
        
        volume_setor = self.df.groupby('setor')['vol_financeiro_total'].sum().sort_values(ascending=False)
        
        fig.add_trace(
            go.Bar(x=volume_setor.index, y=volume_setor.values/1_000_000, name='Volume'),
            row=1, col=1
        )
        
        # 2. Distribuição de preços
        fig.add_trace(
            go.Histogram(x=self.df['preco_medio_ponderado'], nbinsx=10, name='Preços'),
            row=1, col=2
        )
        
        # 3. Variação vs Volume
        fig.add_trace(
            go.Scatter(
                x=self.df['vol_financeiro_total']/1_000_000,
                y=self.df['variacao_percentual_dia'],
                mode='markers+text',
                text=self.df['codigo_negociacao'],
                textposition="top center",
                name='Ações'
            ),
            row=2, col=1
        )
        
        # 4. Ranking de performance
        top_performance = self.df.nlargest(5, 'variacao_percentual_dia')
        fig.add_trace(
            go.Bar(
                x=top_performance['codigo_negociacao'],
                y=top_performance['variacao_percentual_dia'],
                name='Top Performance'
            ),
            row=2, col=2
        )
        
        fig.update_layout(height=800, showlegend=False, title_text="Dashboard - Mercado B3")
        fig.write_html('../docs/market_dashboard.html')
        fig.show()
        
        # Métricas resumo
        total_volume = self.df['vol_financeiro_total'].sum()
        total_negocios = self.df['total_negocios'].sum()
        preco_medio_mercado = self.df['preco_medio_ponderado'].mean()
        
        print(f"💰 Volume total negociado: R$ {total_volume:,.2f}")
        print(f"🔄 Total de negócios: {total_negocios:,}")
        print(f"📊 Preço médio do mercado: R$ {preco_medio_mercado:.2f}")
        print(f"📈 Variação média: {self.df['variacao_percentual_dia'].mean():.2f}%")
        print(f"⚡ Volatilidade média: {self.df['volatilidade_relativa'].mean():.2f}%")
    
    def create_correlation_matrix(self):
        """Matriz de correlação entre variáveis"""
        print("\n🔗 Análise de Correlações")
        print("=" * 50)
        
        # Selecionar variáveis numéricas
        numeric_cols = ['vol_financeiro_total', 'total_negocios', 'qtd_acoes_negociadas',
                       'preco_medio_ponderado', 'variacao_percentual_dia', 
                       'volatilidade_relativa', 'ticket_medio', 'amplitude_preco']
        
        correlation_matrix = self.df[numeric_cols].corr()
        
        # Heatmap de correlação
        plt.figure(figsize=(12, 8))
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0,
                   square=True, linewidths=0.5, cbar_kws={"shrink": .8})
        plt.title('Matriz de Correlação - Variáveis do Mercado', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig('../docs/correlation_matrix.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Correlações mais fortes
        print("Correlações mais significativas:")
        correlations = []
        for i in range(len(correlation_matrix.columns)):
            for j in range(i+1, len(correlation_matrix.columns)):
                corr_value = correlation_matrix.iloc[i, j]
                if abs(corr_value) > 0.5:
                    correlations.append((
                        correlation_matrix.columns[i],
                        correlation_matrix.columns[j],
                        corr_value
                    ))
        
        for var1, var2, corr in sorted(correlations, key=lambda x: abs(x[2]), reverse=True):
            print(f"  {var1} ↔ {var2}: {corr:.3f}")
    
    def generate_insights(self):
        """Gera insights automáticos dos dados"""
        print("\n🧠 Insights Automáticos")
        print("=" * 50)
        
        insights = []
        
        # Insight 1: Ação com melhor performance
        best_performer = self.df.loc[self.df['variacao_percentual_dia'].idxmax()]
        insights.append(f"🏆 Melhor performance: {best_performer['codigo_negociacao']} "
                       f"({best_performer['variacao_percentual_dia']:.2f}%)")
        
        # Insight 2: Maior volume
        highest_volume = self.df.loc[self.df['vol_financeiro_total'].idxmax()]
        insights.append(f"💰 Maior volume: {highest_volume['codigo_negociacao']} "
                       f"(R$ {highest_volume['vol_financeiro_total']:,.2f})")
        
        # Insight 3: Volatilidade
        most_volatile = self.df.loc[self.df['volatilidade_relativa'].idxmax()]
        insights.append(f"⚡ Mais volátil: {most_volatile['codigo_negociacao']} "
                       f"({most_volatile['volatilidade_relativa']:.2f}%)")
        
        # Insight 4: Ticket médio
        highest_ticket = self.df.loc[self.df['ticket_medio'].idxmax()]
        insights.append(f"🎫 Maior ticket médio: {highest_ticket['codigo_negociacao']} "
                       f"(R$ {highest_ticket['ticket_medio']:,.2f})")
        
        # Insight 5: Concentração de mercado
        top3_volume = self.df.nlargest(3, 'vol_financeiro_total')['vol_financeiro_total'].sum()
        total_volume = self.df['vol_financeiro_total'].sum()
        concentration = (top3_volume / total_volume) * 100
        insights.append(f"📊 Concentração: Top 3 ações representam {concentration:.1f}% do volume")
        
        for insight in insights:
            print(insight)
        
        return insights
    
    def export_results(self):
        """Exporta resultados para arquivos"""
        print("\n💾 Exportando Resultados")
        print("=" * 50)
        
        # Criar diretório de resultados
        import os
        os.makedirs('../docs/results', exist_ok=True)
        
        # Exportar dados processados
        self.df.to_csv('../docs/results/dados_processados.csv', index=False)
        self.df.to_parquet('../docs/results/dados_processados.parquet', index=False)
        
        # Exportar resumos
        summary_stats = self.df.describe()
        summary_stats.to_csv('../docs/results/estatisticas_resumo.csv')
        
        # Top performers
        top_performers = self.df.nlargest(10, 'variacao_percentual_dia')
        top_performers.to_csv('../docs/results/top_performers.csv', index=False)
        
        # Volume ranking
        volume_ranking = self.df.nlargest(10, 'vol_financeiro_total')
        volume_ranking.to_csv('../docs/results/volume_ranking.csv', index=False)
        
        print("✅ Arquivos exportados:")
        print("  - dados_processados.csv/parquet")
        print("  - estatisticas_resumo.csv")
        print("  - top_performers.csv")
        print("  - volume_ranking.csv")

def main():
    """Função principal do notebook"""
    print("🚀 Tech Challenge B3 - Athena Analytics Notebook")
    print("=" * 60)
    print("Simulação de notebook Athena para análise de dados da B3")
    print("=" * 60)
    
    # Inicializar analytics
    analytics = B3AthenaAnalytics()
    
    # Executar análises
    print("\n📋 Executando análises...")
    
    # 1. Análise de volume
    volume_data = analytics.create_volume_analysis()
    
    # 2. Análise de variação de preços
    price_data = analytics.create_price_variation_analysis()
    
    # 3. Análise de volatilidade
    volatility_data = analytics.create_volatility_analysis()
    
    # 4. Visão geral do mercado
    analytics.create_market_overview()
    
    # 5. Matriz de correlação
    analytics.create_correlation_matrix()
    
    # 6. Insights automáticos
    insights = analytics.generate_insights()
    
    # 7. Exportar resultados
    analytics.export_results()
    
    print("\n🎉 Análise concluída com sucesso!")
    print("📁 Verifique a pasta 'docs' para visualizações e resultados")
    
    return analytics

if __name__ == "__main__":
    analytics = main()

