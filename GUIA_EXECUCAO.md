# Guia de Execução - Pipeline B3

## Pré-requisitos

Antes de começar, você precisa ter:

1. **Conta AWS** com permissões administrativas
2. **AWS CLI** instalado e configurado
3. **Python 3.9+** instalado
4. **Git** (opcional, para clonar)

## Configuração Inicial

### 1. Configurar AWS CLI

```bash
aws configure
# Digite suas credenciais:
# AWS Access Key ID: [sua-access-key]
# AWS Secret Access Key: [sua-secret-key]
# Default region name: us-east-1
# Default output format: json
```

### 2. Baixar o projeto

```bash
# Se você tem o ZIP
unzip tech-challenge-b3-entrega-final.zip
cd tech-challenge-b3

# Ou clone do repositório
git clone [url-do-repo]
cd tech-challenge-b3
```

### 3. Instalar dependências Python

```bash
pip install -r requirements.txt
```

## Execução Passo a Passo

### PASSO 1: Deploy da Infraestrutura AWS

```bash
cd infrastructure

# Tornar o script executável
chmod +x deploy.sh

# Fazer deploy (isso vai criar todos os recursos AWS)
./deploy.sh --deploy

# Aguardar conclusão (pode demorar 5-10 minutos)
```

**O que acontece aqui:**
- Cria buckets S3 (raw e refined)
- Cria função Lambda
- Cria job no Glue
- Configura IAM roles
- Configura triggers S3

### PASSO 2: Testar o Scraper Localmente

```bash
cd ../src

# Executar teste do scraper
python3 test_scraper.py
```

**Resultado esperado:**
```
Testando scraper da B3...
✓ Dados baixados com sucesso
✓ Arquivo Parquet criado: data/raw/year=2025/month=01/day=15/cotacoes_20250115.parquet
✓ Upload para S3 realizado
```

### PASSO 3: Executar Scraper Real

```bash
# Executar scraper principal
python3 b3_scraper.py
```

**O que acontece:**
1. Script baixa dados da B3
2. Converte para Parquet
3. Faz upload para S3 raw bucket
4. **AUTOMATICAMENTE** dispara Lambda
5. Lambda inicia job Glue
6. Glue processa dados e salva no refined bucket

### PASSO 4: Verificar Execução do Pipeline

```bash
# Verificar se arquivos foram criados no S3
aws s3 ls s3://tech-challenge-b3-raw-bucket-dev/raw/ --recursive

# Verificar job Glue
aws glue get-job-runs --job-name tech-challenge-b3-etl-job-dev

# Verificar dados processados
aws s3 ls s3://tech-challenge-b3-refined-bucket-dev/refined/ --recursive
```

### PASSO 5: Configurar Athena

```bash
# Abrir console AWS Athena
# https://console.aws.amazon.com/athena/

# 1. Configurar local de resultados:
#    s3://tech-challenge-b3-refined-bucket-dev/athena-results/

# 2. Selecionar database: tech_challenge_b3_database_dev

# 3. Verificar se tabela existe:
SHOW TABLES;

# 4. Testar consulta:
SELECT COUNT(*) FROM cotacoes_b3_refined;
```

### PASSO 6: Executar Análises

```bash
cd src

# Executar notebook de análises
python3 athena_notebook.py
```

**Resultado:**
- Gráficos salvos em `docs/`
- Dados exportados em `docs/results/`
- Dashboard HTML criado

### PASSO 7: Testar Consultas SQL

```bash
# Copiar consultas do arquivo
cat athena_queries.sql

# Executar no console Athena ou via CLI:
aws athena start-query-execution \
  --query-string "SELECT codigo_negociacao, vol_financeiro_total FROM cotacoes_b3_refined ORDER BY vol_financeiro_total DESC LIMIT 10;" \
  --result-configuration OutputLocation=s3://tech-challenge-b3-refined-bucket-dev/athena-results/ \
  --query-execution-context Database=tech_challenge_b3_database_dev
```

## Fluxo Completo em Ação

### Execução Automática (Produção)

1. **Trigger diário**: Configure um cron job ou EventBridge para executar o scraper
2. **Pipeline automático**: Cada upload no S3 dispara automaticamente o processamento
3. **Monitoramento**: CloudWatch logs mostram o progresso

```bash
# Exemplo de cron job (executar todo dia às 19h)
0 19 * * * cd /path/to/project/src && python3 b3_scraper.py
```

### Execução Manual (Desenvolvimento)

```bash
# 1. Executar scraper
python3 src/b3_scraper.py

# 2. Aguardar processamento (verificar CloudWatch)
aws logs tail /aws/lambda/tech-challenge-b3-trigger-lambda-dev --follow

# 3. Verificar dados processados
aws athena start-query-execution --query-string "SELECT COUNT(*) FROM cotacoes_b3_refined;" --result-configuration OutputLocation=s3://bucket/results/ --query-execution-context Database=tech_challenge_b3_database_dev

# 4. Executar análises
python3 src/athena_notebook.py
```

## Troubleshooting

### Problema 1: "Bucket não existe"

```bash
# Verificar se deploy foi feito
aws s3 ls | grep tech-challenge

# Se não existir, refazer deploy
cd infrastructure
./deploy.sh --deploy
```

### Problema 2: "Permissões negadas"

```bash
# Verificar credenciais AWS
aws sts get-caller-identity

# Verificar se tem permissões necessárias
aws iam list-attached-user-policies --user-name SEU-USUARIO
```

### Problema 3: "Job Glue falha"

```bash
# Verificar logs do Glue
aws logs describe-log-groups | grep glue

# Ver logs específicos
aws logs tail /aws-glue/jobs/tech-challenge-b3-etl-job-dev --follow
```

### Problema 4: "Tabela não aparece no Athena"

```bash
# Reparar partições
# No console Athena, executar:
MSCK REPAIR TABLE cotacoes_b3_refined;

# Ou verificar se Glue Catalog foi criado
aws glue get-table --database-name tech_challenge_b3_database_dev --name cotacoes_b3_refined
```

## Validação Final

Execute estes comandos para validar se tudo funcionou:

```bash
# 1. Verificar arquivos no S3
aws s3 ls s3://tech-challenge-b3-raw-bucket-dev/raw/ --recursive
aws s3 ls s3://tech-challenge-b3-refined-bucket-dev/refined/ --recursive

# 2. Verificar tabela no Athena
aws athena start-query-execution \
  --query-string "DESCRIBE cotacoes_b3_refined;" \
  --result-configuration OutputLocation=s3://tech-challenge-b3-refined-bucket-dev/athena-results/ \
  --query-execution-context Database=tech_challenge_b3_database_dev

# 3. Contar registros
aws athena start-query-execution \
  --query-string "SELECT COUNT(*) FROM cotacoes_b3_refined;" \
  --result-configuration OutputLocation=s3://tech-challenge-b3-refined-bucket-dev/athena-results/ \
  --query-execution-context Database=tech_challenge_b3_database_dev

# 4. Verificar transformações
aws athena start-query-execution \
  --query-string "SELECT codigo_negociacao, vol_financeiro_total, dias_desde_inicio_ano FROM cotacoes_b3_refined LIMIT 5;" \
  --result-configuration OutputLocation=s3://tech-challenge-b3-refined-bucket-dev/athena-results/ \
  --query-execution-context Database=tech_challenge_b3_database_dev
```

## Limpeza (Opcional)

Para remover todos os recursos e evitar custos:

```bash
cd infrastructure
./deploy.sh --destroy

# Confirmar quando solicitado
```

## Custos Esperados

- **Desenvolvimento/Teste**: ~$5-10/mês
- **Produção**: ~$20-30/mês (dependendo do volume)

## Próximos Passos

Após validar o funcionamento:

1. Configure alertas no CloudWatch
2. Implemente backup dos dados
3. Configure monitoramento de custos
4. Documente processos operacionais
5. Treine usuários finais

## Suporte

Se encontrar problemas:

1. Verifique logs no CloudWatch
2. Consulte a documentação em `docs/`
3. Execute testes unitários em `src/test_*.py`
4. Verifique permissões IAM

