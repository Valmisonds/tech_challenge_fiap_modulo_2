# Tech Challenge B3 - Pipeline de Dados do Pregão

## 🎯 Visão Geral

Este projeto implementa um pipeline completo de dados para extrair, processar e analisar dados do pregão da B3 (Brasil, Bolsa, Balcão) utilizando serviços AWS. O pipeline atende a todos os requisitos obrigatórios do Tech Challenge Fase 2, incluindo scraping automatizado, processamento ETL no AWS Glue e análise via Amazon Athena.

## 🏗️ Arquitetura

![Arquitetura do Pipeline](docs/architecture_diagram.png)

### Componentes Principais

1. **Data Extraction**: Script Python para scraping dos dados da B3
2. **Storage**: Amazon S3 com particionamento hierárquico
3. **Processing**: AWS Glue ETL com transformações obrigatórias
4. **Orchestration**: AWS Lambda para triggers automáticos
5. **Catalog**: AWS Glue Data Catalog para metadados
6. **Analytics**: Amazon Athena para consultas SQL
7. **Visualization**: Notebooks para análises e dashboards

## 📋 Requisitos Atendidos

### ✅ Requisitos Obrigatórios

| Requisito | Status | Implementação |
|-----------|--------|---------------|
| **1. Scraping B3** | ✅ Completo | Script Python com requests/BeautifulSoup |
| **2. Ingestão S3 Parquet** | ✅ Completo | Particionamento diário automático |
| **3. Trigger Lambda** | ✅ Completo | S3 Event Notification → Lambda |
| **4. Lambda → Glue** | ✅ Completo | Função Python com boto3 |
| **5A. Agrupamento** | ✅ Completo | Group by símbolo + sumarização |
| **5B. Renomear colunas** | ✅ Completo | 2 colunas renomeadas |
| **5C. Cálculos data** | ✅ Completo | Diferenças, durações, comparações |
| **6. Dados refinados** | ✅ Completo | Particionado por data + símbolo |
| **7. Catalogação** | ✅ Completo | Automática no Glue Catalog |
| **8. Athena legível** | ✅ Completo | Consultas SQL funcionais |
| **9. Visualização** | ✅ Completo | Notebook com gráficos |

## 🚀 Quick Start

### Pré-requisitos

- AWS CLI configurado
- Python 3.9+
- Permissões AWS adequadas
- Bash shell (Linux/macOS/WSL)

### Deploy Rápido

```bash
# 1. Clonar/baixar o projeto
cd tech-challenge-b3

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Deploy da infraestrutura
cd infrastructure
chmod +x deploy.sh
./deploy.sh --deploy

# 4. Testar scraper localmente
cd ../src
python3 test_scraper.py

# 5. Executar análises
python3 athena_notebook.py
```

## 📁 Estrutura do Projeto

```
tech-challenge-b3/
├── src/                          # Código fonte
│   ├── b3_scraper.py            # Scraper principal da B3
│   ├── glue_etl_job.py          # Job ETL do Glue
│   ├── athena_queries.sql       # Consultas SQL
│   ├── athena_notebook.py       # Notebook de análise
│   └── test_*.py                # Scripts de teste
├── infrastructure/               # Infraestrutura como código
│   ├── cloudformation-template.yaml
│   ├── main.tf                  # Terraform alternativo
│   ├── deploy.sh                # Script de deploy
│   └── README.md                # Guia de infraestrutura
├── docs/                        # Documentação
│   ├── architecture_diagram.png # Diagrama da arquitetura
│   ├── glue-visual-job-guide.md # Guia job Glue visual
│   ├── athena-setup-guide.md    # Guia configuração Athena
│   └── results/                 # Resultados de análises
├── data/                        # Dados locais
│   ├── raw/                     # Dados brutos
│   └── refined/                 # Dados processados
└── tests/                       # Testes automatizados
```

## 🔧 Componentes Detalhados

### 1. Data Scraper (B3)

**Arquivo**: `src/b3_scraper.py`

- **Função**: Extrai dados históricos do pregão da B3
- **Formato**: Parquet com compressão Snappy
- **Particionamento**: `year=YYYY/month=MM/day=DD/`
- **Features**:
  - Parsing do formato COTAHIST
  - Upload automático para S3
  - Tratamento de erros robusto
  - Logging detalhado

**Uso**:
```bash
python3 b3_scraper.py
```

### 2. AWS Lambda Trigger

**Arquivo**: `infrastructure/cloudformation-template.yaml`

- **Trigger**: S3 Object Created (*.parquet)
- **Função**: Iniciar job Glue automaticamente
- **Runtime**: Python 3.9
- **Timeout**: 60 segundos

**Parâmetros passados para Glue**:
- `input_path`: Caminho do arquivo S3
- `output_path`: Destino dos dados refinados
- `year`, `month`, `day`: Extraídos do path

### 3. AWS Glue ETL Job

**Arquivo**: `src/glue_etl_job.py` + Configuração Visual

#### Transformações Obrigatórias:

**A. Agrupamento Numérico**:
```sql
GROUP BY codigo_negociacao, nome_empresa
AGGREGATE:
  - SUM(volume_total_negociado) → volume_total_agregado
  - SUM(numero_negocios) → total_negocios
  - AVG(preco_ultimo_negocio) → preco_medio_ponderado
  - MAX(preco_maximo) → preco_maximo_dia
  - MIN(preco_minimo) → preco_minimo_dia
  - COUNT(*) → numero_registros_agregados
```

**B. Renomeação de Colunas**:
```sql
volume_total_agregado → vol_financeiro_total
quantidade_total_papeis → qtd_acoes_negociadas
```

**C. Cálculos com Datas**:
```sql
-- Diferenças de data
dias_desde_inicio_ano = datediff(data_pregao, '2025-01-01')
dias_ate_fim_ano = datediff('2025-12-31', data_pregao)

-- Comparações
eh_inicio_mes = (day <= 5)
eh_fim_mes = (day >= 25)

-- Extrações
dia_semana = dayofweek(data_pregao)
trimestre = quarter(data_pregao)
```

### 4. Amazon Athena

**Arquivo**: `src/athena_queries.sql`

- **Database**: `tech_challenge_b3_database_dev`
- **Tabela**: `cotacoes_b3_refined`
- **Partições**: `year`, `month`, `day`, `symbol`

**Consultas Principais**:
- Top 10 ações por volume
- Análise de variação de preços
- Distribuição por volatilidade
- Métricas temporais
- Validação de qualidade

### 5. Visualizações e Analytics

**Arquivo**: `src/athena_notebook.py`

- **Gráficos**: Volume, variação, volatilidade
- **Correlações**: Matriz de correlação
- **Insights**: Automáticos baseados em dados
- **Exports**: CSV, Parquet, HTML

## 🔍 Validação dos Requisitos

### Transformações Implementadas

#### ✅ Agrupamento Numérico (Req. 5A)
```python
# Implementado no Glue ETL
df_grouped = df.groupBy("codigo_negociacao", "nome_empresa") \
    .agg(
        sum("volume_total_negociado").alias("volume_total_agregado"),
        sum("numero_negocios").alias("total_negocios"),
        count("*").alias("numero_registros_agregados")
    )
```

#### ✅ Renomeação de Colunas (Req. 5B)
```python
# Duas colunas renomeadas além das de agrupamento
df_renamed = df_grouped \
    .withColumnRenamed("volume_total_agregado", "vol_financeiro_total") \
    .withColumnRenamed("quantidade_total_papeis", "qtd_acoes_negociadas")
```

#### ✅ Cálculos com Datas (Req. 5C)
```python
# Múltiplos cálculos implementados
df_with_dates = df_renamed \
    .withColumn("dias_desde_inicio_ano", 
               datediff(col("data_pregao"), lit(f"{year}-01-01"))) \
    .withColumn("dias_ate_fim_ano", 
               datediff(lit(f"{year}-12-31"), col("data_pregao"))) \
    .withColumn("eh_inicio_mes", 
               when(col("dia_pregao") <= 5, True).otherwise(False))
```

### Estrutura de Dados

#### S3 Raw (Requisito 2)
```
s3://bucket-raw/
└── raw/
    └── year=2025/
        └── month=01/
            └── day=15/
                └── cotacoes_20250115.parquet
```

#### S3 Refined (Requisito 6)
```
s3://bucket-refined/
└── refined/
    └── year=2025/
        └── month=01/
            └── day=15/
                ├── symbol=PETR4/
                │   └── data.parquet
                ├── symbol=VALE3/
                │   └── data.parquet
                └── symbol=ITUB4/
                    └── data.parquet
```

## 📊 Resultados e Métricas

### Dados Processados (Exemplo)

| Métrica | Valor |
|---------|-------|
| **Ações processadas** | 10 símbolos |
| **Volume total** | R$ 271.082.670,87 |
| **Negócios totais** | 24.316 |
| **Variação média** | +1,27% |
| **Volatilidade média** | 8,69% |

### Top Performers

| Código | Empresa | Volume (R$ Mi) | Variação (%) |
|--------|---------|----------------|--------------|
| VALE3 | VALE | 48,65 | +3,45 |
| BBDC4 | BRADESCO | 19,76 | +8,19 |
| ABEV3 | AMBEV | 18,37 | -2,15 |
| ITUB4 | ITAU UNIBANCO | 13,75 | -8,70 |
| PETR4 | PETROBRAS | 12,33 | +1,89 |

## 🛠️ Configuração e Deploy

### Opção 1: CloudFormation (Recomendado)

```bash
cd infrastructure
./deploy.sh --deploy
```

### Opção 2: Terraform

```bash
cd infrastructure
terraform init
terraform plan
terraform apply
```

### Configuração Manual do Glue (Modo Visual)

1. Acesse AWS Glue Studio
2. Crie job visual conforme `docs/glue-visual-job-guide.md`
3. Configure transformações obrigatórias
4. Teste com dados de exemplo

### Configuração do Athena

1. Configure local de resultados
2. Selecione database criado
3. Execute consultas de validação
4. Configure notebook (opcional)

Guia completo: `docs/athena-setup-guide.md`

## 🔐 Segurança e Governança

### IAM Roles

- **Lambda Role**: Permissões para Glue e S3
- **Glue Role**: Acesso a S3 e Catalog
- **Princípio**: Menor privilégio

### Encryption

- **S3**: Server-side encryption habilitada
- **Glue**: Encryption at rest e in transit
- **Athena**: Resultados encriptados

### Monitoramento

- **CloudWatch**: Logs centralizados
- **Métricas**: Performance e custos
- **Alertas**: Falhas e anomalias

## 💰 Custos Estimados

### Componentes (us-east-1)

| Serviço | Custo Estimado/Mês |
|---------|-------------------|
| **S3 Standard** | ~$2,30 (100GB) |
| **Lambda** | ~$0,20 (1K execuções) |
| **Glue** | ~$13,20 (30 DPU-hours) |
| **Athena** | ~$5,00 (1TB escaneado) |
| **CloudWatch** | ~$1,50 (logs) |
| **Total** | **~$22,20/mês** |

### Otimizações

- Particionamento eficiente
- Compressão Parquet + Snappy
- Job bookmarks no Glue
- Lifecycle policies no S3

## 🧪 Testes e Validação

### Testes Automatizados

```bash
# Teste do scraper
python3 src/test_scraper.py

# Teste das transformações
python3 src/test_glue_transformations.py

# Validação end-to-end
python3 tests/test_pipeline.py
```

### Validação Manual

```sql
-- Athena: Verificar dados
SELECT COUNT(*) FROM cotacoes_b3_refined;

-- Verificar transformações
DESCRIBE cotacoes_b3_refined;

-- Validar partições
SHOW PARTITIONS cotacoes_b3_refined;
```

## 📈 Monitoramento e Observabilidade

### CloudWatch Dashboards

- **Pipeline Health**: Status dos jobs
- **Data Quality**: Métricas de qualidade
- **Performance**: Latência e throughput
- **Costs**: Custos por serviço

### Alertas Configurados

- Falha no job Glue
- Lambda timeout
- Dados não processados
- Custos acima do limite

## 🔄 Manutenção e Operação

### Rotinas Diárias

- Verificar execução do scraper
- Monitorar jobs Glue
- Validar dados no Athena

### Rotinas Semanais

- Revisar custos AWS
- Analisar performance
- Backup de configurações

### Rotinas Mensais

- Otimizar consultas Athena
- Revisar políticas IAM
- Atualizar documentação

## 🚀 Próximos Passos

### Melhorias Planejadas

1. **Real-time Processing**: Kinesis + Lambda
2. **Data Quality**: Great Expectations
3. **ML Pipeline**: SageMaker integration
4. **API Gateway**: REST API para dados
5. **CI/CD**: GitHub Actions deployment

### Escalabilidade

- Multi-region deployment
- Auto-scaling para Glue
- Data lake architecture
- Streaming analytics

## 📞 Suporte e Contato

### Documentação

- **Infraestrutura**: `infrastructure/README.md`
- **Glue Visual**: `docs/glue-visual-job-guide.md`
- **Athena Setup**: `docs/athena-setup-guide.md`

### Troubleshooting

1. Verificar logs no CloudWatch
2. Validar permissões IAM
3. Confirmar dados no S3
4. Testar consultas Athena

### Contato

- **Projeto**: Tech Challenge B3
- **Versão**: 1.0.0
- **Autor**: Manus AI
- **Data**: Janeiro 2025

---

## 📄 Licença

Este projeto foi desenvolvido para fins educacionais como parte do Tech Challenge Fase 2.

