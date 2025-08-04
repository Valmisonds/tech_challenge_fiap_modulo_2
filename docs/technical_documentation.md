# Documentação Técnica - Tech Challenge B3

## 1. Visão Geral da Solução

### 1.1 Contexto e Objetivos

O Tech Challenge B3 representa uma implementação completa de um pipeline de dados moderno para processamento de informações do mercado financeiro brasileiro. A solução foi projetada para atender aos requisitos específicos de extração, transformação e análise de dados do pregão da B3, utilizando as melhores práticas de engenharia de dados e arquitetura cloud-native.

### 1.2 Arquitetura de Referência

A arquitetura implementada segue o padrão de Data Lake moderno, com separação clara entre camadas de ingestão, processamento, armazenamento e consumo. Esta abordagem garante escalabilidade, manutenibilidade e governança adequada dos dados.

#### Princípios Arquiteturais

1. **Separação de Responsabilidades**: Cada componente tem uma função específica e bem definida
2. **Escalabilidade Horizontal**: Capacidade de crescer conforme demanda
3. **Tolerância a Falhas**: Recuperação automática e tratamento de erros
4. **Observabilidade**: Monitoramento e logging em todos os níveis
5. **Segurança por Design**: Controles de acesso e criptografia nativa

### 1.3 Stack Tecnológico

| Camada | Tecnologia | Justificativa |
|--------|------------|---------------|
| **Extração** | Python + Requests | Flexibilidade para web scraping |
| **Armazenamento** | Amazon S3 + Parquet | Durabilidade e performance |
| **Processamento** | AWS Glue | Serverless e integração nativa |
| **Orquestração** | AWS Lambda | Event-driven e baixo custo |
| **Catalogação** | Glue Data Catalog | Metadados centralizados |
| **Análise** | Amazon Athena | SQL familiar e pay-per-query |
| **Visualização** | Python + Plotly | Flexibilidade analítica |

## 2. Implementação Detalhada

### 2.1 Componente de Extração de Dados

#### 2.1.1 Scraper da B3

O componente de extração foi desenvolvido em Python utilizando uma abordagem modular e robusta:

```python
class B3DataScraper:
    def __init__(self, s3_bucket=None, local_path="./data/raw"):
        self.base_url = "https://www.b3.com.br/..."
        self.s3_bucket = s3_bucket
        self.local_path = Path(local_path)
        
    def download_daily_data(self, date):
        # Implementação do download
        
    def parse_cotahist_data(self, content):
        # Parsing do formato COTAHIST
        
    def save_to_parquet(self, df, date):
        # Salvamento com particionamento
```

#### 2.1.2 Características Técnicas

- **Formato de Saída**: Apache Parquet com compressão Snappy
- **Particionamento**: Hierárquico por ano/mês/dia
- **Tratamento de Erros**: Retry logic e logging detalhado
- **Performance**: Processamento em lotes e otimizações de memória

#### 2.1.3 Estrutura de Dados

O scraper processa o formato COTAHIST da B3, extraindo campos essenciais:

```python
record = {
    'codigo_negociacao': line[12:24].strip(),
    'nome_empresa': line[27:39].strip(),
    'preco_abertura': float(line[56:69].strip()) / 100,
    'preco_maximo': float(line[69:82].strip()) / 100,
    'volume_total_negociado': float(line[170:188].strip()) / 100,
    # ... outros campos
}
```

### 2.2 Camada de Armazenamento

#### 2.2.1 Amazon S3 - Dados Brutos

**Estrutura de Particionamento**:
```
s3://bucket-raw/
├── raw/
│   ├── year=2025/
│   │   ├── month=01/
│   │   │   ├── day=01/
│   │   │   │   └── cotacoes_20250101.parquet
│   │   │   ├── day=02/
│   │   │   └── day=03/
│   │   ├── month=02/
│   │   └── month=03/
│   └── year=2024/
├── scripts/
│   └── etl_job.py
└── temp/
    └── glue-temp-files/
```

**Configurações de Performance**:
- **Storage Class**: S3 Standard para acesso frequente
- **Compression**: Snappy (balance entre compressão e velocidade)
- **File Size**: Otimizado para 128MB-1GB por arquivo
- **Lifecycle**: Transição automática para IA após 30 dias

#### 2.2.2 Amazon S3 - Dados Refinados

**Estrutura Otimizada**:
```
s3://bucket-refined/
├── refined/
│   ├── year=2025/
│   │   ├── month=01/
│   │   │   ├── day=01/
│   │   │   │   ├── symbol=PETR4/
│   │   │   │   │   └── part-00000.parquet
│   │   │   │   ├── symbol=VALE3/
│   │   │   │   └── symbol=ITUB4/
│   │   │   └── day=02/
│   │   └── month=02/
│   └── year=2024/
└── summary/
    └── daily_aggregates/
```

### 2.3 Camada de Processamento

#### 2.3.1 AWS Lambda - Trigger Function

A função Lambda atua como orquestrador, sendo acionada por eventos S3:

```python
def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])
        
        # Extrair metadados do path
        year, month, day = extract_date_from_path(key)
        
        # Iniciar job Glue
        response = glue_client.start_job_run(
            JobName=job_name,
            Arguments={
                '--input_path': f's3://{bucket}/{key}',
                '--output_path': f's3://{refined_bucket}/refined/',
                '--year': year,
                '--month': month,
                '--day': day
            }
        )
```

#### 2.3.2 AWS Glue ETL - Transformações

O job Glue implementa as três transformações obrigatórias:

**Transformação A - Agrupamento Numérico**:
```python
df_grouped = df.groupBy("codigo_negociacao", "nome_empresa") \
    .agg(
        sum("volume_total_negociado").alias("volume_total_agregado"),
        sum("numero_negocios").alias("total_negocios"),
        sum("quantidade_papeis_negociados").alias("quantidade_total_papeis"),
        avg("preco_ultimo_negocio").alias("preco_medio_ponderado"),
        max("preco_maximo").alias("preco_maximo_dia"),
        min("preco_minimo").alias("preco_minimo_dia"),
        count("*").alias("numero_registros_agregados")
    )
```

**Transformação B - Renomeação de Colunas**:
```python
df_renamed = df_grouped \
    .withColumnRenamed("volume_total_agregado", "vol_financeiro_total") \
    .withColumnRenamed("quantidade_total_papeis", "qtd_acoes_negociadas")
```

**Transformação C - Cálculos com Datas**:
```python
df_with_dates = df_renamed \
    .withColumn("data_pregao", lit(f"{year:04d}-{month:02d}-{day:02d}").cast("date")) \
    .withColumn("dia_semana", dayofweek(col("data_pregao"))) \
    .withColumn("dias_desde_inicio_ano", 
               datediff(col("data_pregao"), lit(f"{year}-01-01"))) \
    .withColumn("dias_ate_fim_ano", 
               datediff(lit(f"{year}-12-31"), col("data_pregao"))) \
    .withColumn("eh_inicio_mes", 
               when(col("dia_pregao") <= 5, True).otherwise(False))
```

### 2.4 Camada de Catalogação

#### 2.4.1 AWS Glue Data Catalog

O Glue Data Catalog mantém metadados centralizados:

```sql
-- Schema da tabela principal
CREATE EXTERNAL TABLE cotacoes_b3_refined (
    codigo_negociacao string,
    nome_empresa string,
    vol_financeiro_total double,
    total_negocios bigint,
    qtd_acoes_negociadas bigint,
    preco_medio_ponderado double,
    variacao_percentual_dia double,
    volatilidade_relativa double,
    data_pregao date,
    dia_semana int,
    trimestre int
)
PARTITIONED BY (
    year int,
    month int,
    day int,
    symbol string
)
STORED AS PARQUET
LOCATION 's3://bucket-refined/refined/'
```

#### 2.4.2 Gestão de Partições

- **Descoberta Automática**: Via job Glue
- **Manutenção**: `MSCK REPAIR TABLE` quando necessário
- **Otimização**: Partition pruning automático no Athena

### 2.5 Camada de Análise

#### 2.5.1 Amazon Athena

Configuração otimizada para performance:

```sql
-- Configurações de sessão
SET hive.exec.dynamic.partition = true;
SET hive.exec.dynamic.partition.mode = nonstrict;
SET hive.exec.max.dynamic.partitions = 1000;
```

**Consultas Otimizadas**:
```sql
-- Uso eficiente de partições
SELECT codigo_negociacao, vol_financeiro_total
FROM cotacoes_b3_refined
WHERE year = 2025 AND month = 1 AND day = 15
  AND symbol IN ('PETR4', 'VALE3', 'ITUB4')
ORDER BY vol_financeiro_total DESC;
```

#### 2.5.2 Notebooks de Análise

Implementação em Python com bibliotecas especializadas:

```python
class B3AthenaAnalytics:
    def create_volume_analysis(self):
        # Análise de volume com visualizações
        top_volume = self.df.nlargest(10, 'vol_financeiro_total')
        
        # Gráfico interativo
        fig = px.bar(top_volume, 
                    x='codigo_negociacao', 
                    y='vol_financeiro_total',
                    title='Volume Financeiro por Ação')
        fig.show()
```

## 3. Aspectos de Segurança

### 3.1 Identity and Access Management (IAM)

#### 3.1.1 Roles e Políticas

**Lambda Execution Role**:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "glue:StartJobRun",
                "glue:GetJobRun"
            ],
            "Resource": "arn:aws:glue:*:*:job/tech-challenge-b3-*"
        }
    ]
}
```

**Glue Service Role**:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": [
                "arn:aws:s3:::tech-challenge-b3-*/*"
            ]
        }
    ]
}
```

#### 3.1.2 Princípios de Segurança

1. **Least Privilege**: Permissões mínimas necessárias
2. **Resource-Based**: Políticas específicas por recurso
3. **Temporary Credentials**: Uso de roles em vez de chaves
4. **Audit Trail**: CloudTrail para todas as ações

### 3.2 Criptografia

#### 3.2.1 Encryption at Rest

- **S3**: AES-256 server-side encryption
- **Glue**: Encryption habilitada por padrão
- **Athena**: Resultados encriptados no S3

#### 3.2.2 Encryption in Transit

- **HTTPS**: Todas as comunicações via TLS 1.2+
- **VPC Endpoints**: Tráfego interno à AWS
- **SSL/TLS**: Conexões de clientes externos

### 3.3 Network Security

#### 3.3.1 VPC Configuration

```yaml
# CloudFormation snippet
VPCEndpointS3:
  Type: AWS::EC2::VPCEndpoint
  Properties:
    VpcId: !Ref VPC
    ServiceName: !Sub 'com.amazonaws.${AWS::Region}.s3'
    VpcEndpointType: Gateway
```

## 4. Monitoramento e Observabilidade

### 4.1 CloudWatch Metrics

#### 4.1.1 Métricas Customizadas

```python
# Exemplo de métrica customizada
cloudwatch = boto3.client('cloudwatch')

cloudwatch.put_metric_data(
    Namespace='TechChallenge/B3',
    MetricData=[
        {
            'MetricName': 'RecordsProcessed',
            'Value': record_count,
            'Unit': 'Count',
            'Dimensions': [
                {
                    'Name': 'JobName',
                    'Value': job_name
                }
            ]
        }
    ]
)
```

#### 4.1.2 Dashboards

Métricas monitoradas:
- **Lambda**: Duração, erros, invocações
- **Glue**: DPU utilização, duração do job
- **S3**: Requests, storage utilizado
- **Athena**: Queries executadas, dados escaneados

### 4.2 Logging Strategy

#### 4.2.1 Structured Logging

```python
import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def log_structured(level, message, **kwargs):
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'level': level,
        'message': message,
        **kwargs
    }
    logger.info(json.dumps(log_entry))
```

#### 4.2.2 Log Aggregation

- **CloudWatch Logs**: Centralização de todos os logs
- **Log Groups**: Separados por serviço
- **Retention**: 14 dias para desenvolvimento, 30+ para produção
- **Filtering**: Queries para troubleshooting

### 4.3 Alerting

#### 4.3.1 CloudWatch Alarms

```yaml
# Exemplo de alarme
GlueJobFailureAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: !Sub '${ProjectName}-glue-job-failure'
    AlarmDescription: 'Glue job failure detection'
    MetricName: 'glue.driver.aggregate.numFailedTasks'
    Namespace: 'AWS/Glue'
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 1
    Threshold: 1
    ComparisonOperator: GreaterThanOrEqualToThreshold
```

## 5. Performance e Otimização

### 5.1 Otimizações de Storage

#### 5.1.1 Parquet Optimization

```python
# Configurações otimizadas para Parquet
df.write \
  .mode("overwrite") \
  .option("compression", "snappy") \
  .option("parquet.block.size", "134217728")  # 128MB \
  .partitionBy("year", "month", "day", "symbol") \
  .parquet(output_path)
```

#### 5.1.2 Partitioning Strategy

- **Cardinalidade**: Evitar partições muito pequenas (<10MB)
- **Pruning**: Filtros eficientes no Athena
- **Balance**: Entre granularidade e performance

### 5.2 Glue Job Optimization

#### 5.2.1 Resource Configuration

```python
# Configuração otimizada
job_config = {
    "GlueVersion": "3.0",
    "WorkerType": "G.1X",
    "NumberOfWorkers": 2,
    "MaxRetries": 1,
    "Timeout": 60
}
```

#### 5.2.2 Job Bookmarks

```python
# Habilitação de bookmarks
"--job-bookmark-option": "job-bookmark-enable"
```

### 5.3 Athena Query Optimization

#### 5.3.1 Best Practices

```sql
-- ✅ Bom: Usar filtros de partição
SELECT * FROM table 
WHERE year = 2025 AND month = 1;

-- ❌ Ruim: Filtro em coluna não particionada
SELECT * FROM table 
WHERE data_pregao = '2025-01-15';

-- ✅ Bom: Projeção de colunas
SELECT codigo_negociacao, volume 
FROM table;

-- ❌ Ruim: SELECT *
SELECT * FROM table;
```

## 6. Custos e Economia

### 6.1 Análise de Custos

#### 6.1.1 Breakdown por Serviço

| Serviço | Custo/Mês | % Total | Otimização |
|---------|-----------|---------|------------|
| **Glue** | $13.20 | 59.5% | Job bookmarks, workers otimizados |
| **S3** | $2.30 | 10.4% | Lifecycle policies |
| **Athena** | $5.00 | 22.5% | Particionamento eficiente |
| **Lambda** | $0.20 | 0.9% | Timeout otimizado |
| **CloudWatch** | $1.50 | 6.8% | Retention policies |

#### 6.1.2 Estratégias de Otimização

1. **Glue**: 
   - Usar G.1X workers (mais econômicos)
   - Job bookmarks para processamento incremental
   - Timeout adequado para evitar custos desnecessários

2. **S3**:
   - Lifecycle policies para transição IA/Glacier
   - Compressão eficiente (Snappy)
   - Limpeza de dados temporários

3. **Athena**:
   - Particionamento para reduzir dados escaneados
   - Compressão Parquet
   - Queries otimizadas

### 6.2 Cost Monitoring

#### 6.2.1 Budget Alerts

```yaml
# CloudFormation para budget
ProjectBudget:
  Type: AWS::Budgets::Budget
  Properties:
    Budget:
      BudgetName: !Sub '${ProjectName}-monthly-budget'
      BudgetLimit:
        Amount: 50
        Unit: USD
      TimeUnit: MONTHLY
      BudgetType: COST
```

## 7. Testes e Qualidade

### 7.1 Estratégia de Testes

#### 7.1.1 Testes Unitários

```python
import unittest
from src.b3_scraper import B3DataScraper

class TestB3Scraper(unittest.TestCase):
    def setUp(self):
        self.scraper = B3DataScraper()
    
    def test_parse_cotahist_data(self):
        sample_data = "01202501150112345..."
        result = self.scraper.parse_cotahist_data(sample_data)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertGreater(len(result), 0)
```

#### 7.1.2 Testes de Integração

```python
def test_end_to_end_pipeline():
    # 1. Upload arquivo de teste para S3
    # 2. Verificar trigger da Lambda
    # 3. Aguardar conclusão do Glue job
    # 4. Validar dados no Athena
    pass
```

### 7.2 Data Quality

#### 7.2.1 Validações Implementadas

```python
def validate_data_quality(df):
    checks = {
        'null_codes': df['codigo_negociacao'].isnull().sum(),
        'negative_prices': (df['preco_medio_ponderado'] <= 0).sum(),
        'zero_volume': (df['vol_financeiro_total'] == 0).sum(),
        'duplicate_records': df.duplicated().sum()
    }
    
    for check, count in checks.items():
        if count > 0:
            logger.warning(f"Data quality issue: {check} = {count}")
    
    return checks
```

#### 7.2.2 Métricas de Qualidade

- **Completeness**: % de campos não nulos
- **Accuracy**: Validação de ranges de valores
- **Consistency**: Verificação de duplicatas
- **Timeliness**: Dados processados no prazo

## 8. Deployment e DevOps

### 8.1 Infrastructure as Code

#### 8.1.1 CloudFormation

```yaml
# Template modular
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Tech Challenge B3 - Modular Infrastructure'

Parameters:
  Environment:
    Type: String
    AllowedValues: [dev, staging, prod]
    Default: dev

Mappings:
  EnvironmentConfig:
    dev:
      GlueWorkers: 2
      RetentionDays: 7
    prod:
      GlueWorkers: 5
      RetentionDays: 30
```

#### 8.1.2 Terraform Alternative

```hcl
# Configuração modular
module "s3_buckets" {
  source = "./modules/s3"
  
  project_name = var.project_name
  environment  = var.environment
}

module "glue_jobs" {
  source = "./modules/glue"
  
  raw_bucket     = module.s3_buckets.raw_bucket_name
  refined_bucket = module.s3_buckets.refined_bucket_name
}
```

### 8.2 CI/CD Pipeline

#### 8.2.1 GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy Tech Challenge B3

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: python -m pytest tests/
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to AWS
        run: |
          cd infrastructure
          ./deploy.sh --deploy
```

### 8.3 Environment Management

#### 8.3.1 Multi-Environment

```bash
# Scripts para diferentes ambientes
./deploy.sh --env dev
./deploy.sh --env staging  
./deploy.sh --env prod
```

#### 8.3.2 Configuration Management

```python
# config.py
import os

class Config:
    def __init__(self, environment='dev'):
        self.environment = environment
        self.s3_bucket = os.getenv(f'S3_BUCKET_{environment.upper()}')
        self.glue_job = os.getenv(f'GLUE_JOB_{environment.upper()}')
```

## 9. Troubleshooting Guide

### 9.1 Problemas Comuns

#### 9.1.1 Lambda Timeout

**Sintoma**: Lambda function timeout após 60 segundos
**Causa**: Job Glue demorado para iniciar
**Solução**: 
```python
# Implementar retry com backoff
import time
import random

def start_glue_job_with_retry(job_name, arguments, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = glue_client.start_job_run(
                JobName=job_name,
                Arguments=arguments
            )
            return response
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
            else:
                raise e
```

#### 9.1.2 Glue Job Failure

**Sintoma**: Job Glue falha com erro de memória
**Causa**: Dados muito grandes para worker configurado
**Solução**:
```python
# Aumentar número de workers ou usar workers maiores
job_config = {
    "WorkerType": "G.2X",  # Ao invés de G.1X
    "NumberOfWorkers": 4   # Ao invés de 2
}
```

#### 9.1.3 Athena Query Slow

**Sintoma**: Consultas Athena muito lentas
**Causa**: Não uso de filtros de partição
**Solução**:
```sql
-- ❌ Lento
SELECT * FROM cotacoes_b3_refined 
WHERE data_pregao = '2025-01-15';

-- ✅ Rápido  
SELECT * FROM cotacoes_b3_refined 
WHERE year = 2025 AND month = 1 AND day = 15;
```

### 9.2 Debugging Workflow

#### 9.2.1 Checklist de Diagnóstico

1. **Verificar CloudWatch Logs**:
   ```bash
   aws logs tail /aws/lambda/function-name --follow
   ```

2. **Validar Permissões IAM**:
   ```bash
   aws iam simulate-principal-policy \
     --policy-source-arn ROLE-ARN \
     --action-names s3:GetObject \
     --resource-arns BUCKET-ARN
   ```

3. **Testar Conectividade**:
   ```bash
   aws s3 ls s3://bucket-name/
   aws glue get-job --job-name job-name
   ```

4. **Verificar Dados**:
   ```sql
   SELECT COUNT(*) FROM cotacoes_b3_refined;
   SHOW PARTITIONS cotacoes_b3_refined;
   ```

## 10. Conclusão

### 10.1 Resultados Alcançados

A implementação do Tech Challenge B3 demonstra uma solução completa e robusta para processamento de dados financeiros, atendendo a todos os requisitos obrigatórios:

1. ✅ **Scraping automatizado** da B3 com formato Parquet
2. ✅ **Pipeline serverless** com triggers automáticos
3. ✅ **Transformações ETL** conforme especificações
4. ✅ **Catalogação automática** de metadados
5. ✅ **Análises SQL** via Athena
6. ✅ **Visualizações interativas** em notebooks

### 10.2 Benefícios da Arquitetura

- **Escalabilidade**: Cresce automaticamente com demanda
- **Custo-efetivo**: Pay-per-use, sem recursos ociosos
- **Manutenibilidade**: Componentes desacoplados e bem documentados
- **Observabilidade**: Monitoramento completo em todos os níveis
- **Segurança**: Controles de acesso e criptografia nativa

### 10.3 Lições Aprendidas

1. **Particionamento é crucial** para performance no Athena
2. **Job bookmarks** reduzem significativamente custos do Glue
3. **Monitoramento proativo** evita problemas em produção
4. **Testes automatizados** são essenciais para confiabilidade
5. **Documentação detalhada** facilita manutenção e evolução

### 10.4 Próximos Passos

Para evolução da solução:
1. Implementar streaming real-time com Kinesis
2. Adicionar machine learning para detecção de anomalias
3. Criar APIs REST para acesso programático
4. Implementar data lineage e governança
5. Expandir para outros mercados financeiros

Esta documentação técnica serve como referência completa para implementação, manutenção e evolução do pipeline de dados da B3, garantindo que todos os aspectos técnicos estejam adequadamente documentados e possam ser reproduzidos por outras equipes.

