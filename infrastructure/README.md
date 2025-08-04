# Infraestrutura AWS - Tech Challenge B3

Este diretório contém os templates e scripts para provisionar a infraestrutura AWS necessária para o pipeline de dados do pregão da B3.

## Visão Geral da Arquitetura

A infraestrutura é composta pelos seguintes componentes:

### Componentes Principais

1. **S3 Buckets**:
   - `raw-data`: Armazena dados brutos em formato parquet com particionamento diário
   - `refined-data`: Armazena dados processados pelo Glue ETL

2. **Lambda Function**:
   - Função trigger acionada por eventos S3
   - Inicia automaticamente o job Glue quando novos dados são carregados

3. **AWS Glue**:
   - Database para catalogação de metadados
   - Job ETL para processamento e transformação dos dados

4. **IAM Roles**:
   - Roles com permissões mínimas necessárias para cada serviço
   - Políticas de segurança seguindo princípios de menor privilégio

5. **CloudWatch**:
   - Log groups para monitoramento de Lambda e Glue
   - Métricas e alertas para observabilidade

## Opções de Deploy

### Opção 1: CloudFormation (Recomendado)

#### Pré-requisitos
- AWS CLI instalado e configurado
- Permissões adequadas na conta AWS
- Bash shell (Linux/macOS/WSL)

#### Deploy Automático
```bash
# Tornar script executável
chmod +x deploy.sh

# Deploy completo
./deploy.sh --deploy

# Ou usar menu interativo
./deploy.sh
```

#### Deploy Manual
```bash
# Validar template
aws cloudformation validate-template --template-body file://cloudformation-template.yaml

# Criar stack
aws cloudformation create-stack \
    --stack-name tech-challenge-b3-dev \
    --template-body file://cloudformation-template.yaml \
    --parameters ParameterKey=ProjectName,ParameterValue=tech-challenge-b3 \
                ParameterKey=Environment,ParameterValue=dev \
    --capabilities CAPABILITY_NAMED_IAM \
    --region us-east-1

# Aguardar conclusão
aws cloudformation wait stack-create-complete \
    --stack-name tech-challenge-b3-dev \
    --region us-east-1
```

### Opção 2: Terraform

#### Pré-requisitos
- Terraform >= 1.0 instalado
- AWS CLI configurado
- Provider AWS configurado

#### Deploy
```bash
# Inicializar Terraform
terraform init

# Planejar mudanças
terraform plan

# Aplicar infraestrutura
terraform apply

# Para destruir (cuidado!)
terraform destroy
```

#### Variáveis Terraform
```hcl
# terraform.tfvars
project_name = "tech-challenge-b3"
environment  = "dev"
aws_region   = "us-east-1"
```

## Configuração Pós-Deploy

### 1. Variáveis de Ambiente

Após o deploy, um arquivo `.env` será criado automaticamente com as variáveis necessárias:

```bash
# Exemplo de .env gerado
AWS_REGION=us-east-1
S3_RAW_BUCKET=tech-challenge-b3-raw-data-dev-123456789012
S3_REFINED_BUCKET=tech-challenge-b3-refined-data-dev-123456789012
LAMBDA_FUNCTION_NAME=tech-challenge-b3-trigger-glue-dev
GLUE_JOB_NAME=tech-challenge-b3-etl-job-dev
PROJECT_NAME=tech-challenge-b3
ENVIRONMENT=dev
```

### 2. Configurar Job Glue (Modo Visual)

O job Glue deve ser configurado manualmente no AWS Glue Studio:

1. Acesse o AWS Glue Console
2. Vá para "Jobs" > "Visual ETL"
3. Edite o job criado: `tech-challenge-b3-etl-job-dev`
4. Configure as transformações obrigatórias:
   - **Agrupamento**: Group by símbolo da ação
   - **Renomear colunas**: Renomear 2 colunas além das de agrupamento
   - **Cálculo de data**: Adicionar duração ou diferença entre datas

### 3. Testar Pipeline

```bash
# Carregar dados de teste no bucket raw
aws s3 cp ../data/raw/ s3://BUCKET-NAME/raw/ --recursive

# Verificar logs da Lambda
aws logs tail /aws/lambda/FUNCTION-NAME --follow

# Verificar execução do Glue
aws glue get-job-runs --job-name JOB-NAME
```

## Estrutura de Dados

### Bucket Raw Data
```
s3://bucket-raw/
├── raw/
│   ├── year=2025/
│   │   ├── month=01/
│   │   │   ├── day=01/
│   │   │   │   └── cotacoes_20250101.parquet
│   │   │   └── day=02/
│   │   └── month=02/
│   └── scripts/
│       └── etl_job.py
└── temp/
```

### Bucket Refined Data
```
s3://bucket-refined/
└── refined/
    ├── year=2025/
    │   ├── month=01/
    │   │   ├── day=01/
    │   │   │   ├── symbol=PETR4/
    │   │   │   │   └── data.parquet
    │   │   │   └── symbol=VALE3/
    │   │   └── day=02/
    │   └── month=02/
```

## Monitoramento e Logs

### CloudWatch Logs
- **Lambda**: `/aws/lambda/tech-challenge-b3-trigger-glue-dev`
- **Glue**: `/aws-glue/jobs/tech-challenge-b3-etl-job-dev`

### Métricas Importantes
- Taxa de sucesso da Lambda
- Duração dos jobs Glue
- Erros de processamento
- Volume de dados processados

### Comandos Úteis
```bash
# Ver logs da Lambda em tempo real
aws logs tail /aws/lambda/FUNCTION-NAME --follow

# Ver execuções do Glue
aws glue get-job-runs --job-name JOB-NAME --max-items 10

# Listar objetos no S3
aws s3 ls s3://BUCKET-NAME/raw/ --recursive

# Verificar status da stack
aws cloudformation describe-stacks --stack-name STACK-NAME
```

## Segurança

### IAM Policies
- Princípio de menor privilégio aplicado
- Roles específicos para cada serviço
- Acesso restrito aos buckets S3

### S3 Security
- Buckets privados (sem acesso público)
- Versionamento habilitado
- Lifecycle policies configuradas

### Encryption
- Encryption at rest habilitada por padrão
- Encryption in transit para todas as comunicações

## Custos Estimados

### Componentes de Custo (região us-east-1)
- **S3**: ~$0.023/GB/mês (Standard)
- **Lambda**: ~$0.20/1M requests + $0.0000166667/GB-second
- **Glue**: ~$0.44/DPU-hour (mínimo 2 DPUs)
- **CloudWatch**: ~$0.50/GB logs ingeridos

### Otimizações de Custo
- Lifecycle policies para S3
- Job bookmarks no Glue para processamento incremental
- Retenção limitada de logs (14 dias)
- Workers G.1X (mais econômicos)

## Troubleshooting

### Problemas Comuns

1. **Lambda não é acionada**:
   - Verificar configuração de notificação S3
   - Verificar permissões IAM
   - Verificar filtros de prefixo/sufixo

2. **Job Glue falha**:
   - Verificar logs no CloudWatch
   - Verificar permissões S3
   - Verificar formato dos dados de entrada

3. **Dados não aparecem no Athena**:
   - Verificar se tabela foi criada no Glue Catalog
   - Executar `MSCK REPAIR TABLE` se necessário
   - Verificar particionamento

### Comandos de Debug
```bash
# Testar Lambda manualmente
aws lambda invoke \
    --function-name FUNCTION-NAME \
    --payload file://test-event.json \
    response.json

# Verificar permissões IAM
aws iam simulate-principal-policy \
    --policy-source-arn ROLE-ARN \
    --action-names s3:GetObject \
    --resource-arns BUCKET-ARN

# Listar partições no Glue
aws glue get-partitions \
    --database-name DATABASE-NAME \
    --table-name TABLE-NAME
```

## Limpeza

### Deletar Infraestrutura

#### CloudFormation
```bash
# Usando script
./deploy.sh --delete

# Manual
aws cloudformation delete-stack --stack-name STACK-NAME
```

#### Terraform
```bash
terraform destroy
```

**⚠️ ATENÇÃO**: Certifique-se de fazer backup dos dados importantes antes de deletar a infraestrutura.

## Suporte

Para dúvidas ou problemas:
1. Verificar logs no CloudWatch
2. Consultar documentação AWS
3. Verificar configurações IAM
4. Revisar este README

## Próximos Passos

Após o deploy da infraestrutura:
1. Configurar job Glue no modo visual
2. Implementar transformações obrigatórias
3. Testar pipeline end-to-end
4. Configurar Athena para consultas
5. Criar dashboards de monitoramento

