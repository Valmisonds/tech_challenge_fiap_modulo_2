# Guia: Configuração do Job Glue no Modo Visual

Este guia detalha como configurar o job ETL do AWS Glue no modo visual conforme exigido pelo Tech Challenge.

## Pré-requisitos

1. Infraestrutura AWS provisionada (S3, IAM roles, etc.)
2. Dados de exemplo carregados no bucket raw
3. Acesso ao AWS Glue Console

## Passo a Passo: Criação do Job Visual

### 1. Acessar AWS Glue Studio

1. Faça login no AWS Console
2. Navegue para **AWS Glue**
3. No menu lateral, clique em **Jobs**
4. Clique em **Create job**
5. Selecione **Visual with a source and target**

### 2. Configurar Source (Origem dos Dados)

#### 2.1 Adicionar Data Source
1. No canvas visual, clique no nó **Data source - S3 bucket**
2. Configure as propriedades:
   - **S3 source type**: S3 location
   - **S3 URL**: `s3://SEU-BUCKET-RAW/raw/`
   - **Data format**: Parquet
   - **Compression type**: None
   - **Recurse**: True (para ler subpastas)

#### 2.2 Configurar Schema
1. Clique em **Infer schema**
2. Aguarde a inferência automática do schema
3. Verifique se as colunas foram detectadas corretamente:
   - `codigo_negociacao` (string)
   - `nome_empresa` (string)
   - `preco_abertura` (double)
   - `preco_maximo` (double)
   - `preco_minimo` (double)
   - `preco_ultimo_negocio` (double)
   - `volume_total_negociado` (double)
   - `numero_negocios` (long)
   - `year`, `month`, `day` (int)

### 3. Transformação A: Agrupamento e Sumarização

#### 3.1 Adicionar Transform - Aggregate
1. Clique no botão **+** após o Data source
2. Selecione **Transform** > **Aggregate**
3. Configure o agrupamento:

**Group by fields:**
- `codigo_negociacao`
- `nome_empresa`

**Aggregations:**
- `volume_total_negociado` → **Sum** → `volume_total_agregado`
- `numero_negocios` → **Sum** → `total_negocios`
- `quantidade_papeis_negociados` → **Sum** → `quantidade_total_papeis`
- `preco_ultimo_negocio` → **Avg** → `preco_medio_ponderado`
- `preco_maximo` → **Max** → `preco_maximo_dia`
- `preco_minimo` → **Min** → `preco_minimo_dia`
- `preco_abertura` → **First** → `preco_abertura_primeiro`
- `preco_ultimo_negocio` → **Last** → `preco_fechamento_ultimo`
- `*` → **Count** → `numero_registros_agregados`

### 4. Transformação B: Renomear Colunas

#### 4.1 Adicionar Transform - Rename Field
1. Adicione um novo nó **Transform** > **Rename Field**
2. Configure as renomeações:
   - `volume_total_agregado` → `vol_financeiro_total`
   - `quantidade_total_papeis` → `qtd_acoes_negociadas`

### 5. Transformação C: Cálculos com Datas

#### 5.1 Adicionar Transform - Derived Column
1. Adicione **Transform** > **Derived Column**
2. Configure as novas colunas:

**Colunas de Data Base:**
```sql
-- data_pregao
to_date(concat(year, '-', lpad(month, 2, '0'), '-', lpad(day, 2, '0')))

-- dia_semana
dayofweek(data_pregao)

-- dia_ano
dayofyear(data_pregao)

-- semana_ano
weekofyear(data_pregao)

-- trimestre
quarter(data_pregao)
```

**Cálculos de Diferença de Datas:**
```sql
-- dias_desde_inicio_ano
datediff(data_pregao, to_date(concat(year, '-01-01')))

-- dias_ate_fim_ano
datediff(to_date(concat(year, '-12-31')), data_pregao)

-- eh_inicio_mes
case when day <= 5 then true else false end

-- eh_fim_mes
case when day >= 25 then true else false end
```

#### 5.2 Adicionar Métricas Calculadas
Adicione outro nó **Derived Column** para métricas:

```sql
-- ticket_medio
vol_financeiro_total / total_negocios

-- variacao_percentual_dia
((preco_fechamento_ultimo - preco_abertura_primeiro) / preco_abertura_primeiro) * 100

-- amplitude_preco
preco_maximo_dia - preco_minimo_dia

-- volatilidade_relativa
(amplitude_preco / preco_medio_ponderado) * 100
```

### 6. Adicionar Colunas de Particionamento

#### 6.1 Transform - Derived Column (Partições)
Adicione colunas para particionamento S3:
```sql
-- symbol (para particionamento por ação)
codigo_negociacao

-- Manter year, month, day existentes
```

### 7. Configurar Target (Destino)

#### 7.1 Adicionar Data Target
1. Adicione **Data target - S3 bucket**
2. Configure:
   - **Format**: Parquet
   - **Compression type**: Snappy
   - **S3 target location**: `s3://SEU-BUCKET-REFINED/refined/`
   - **Data Catalog update options**: Create a table in the Data Catalog

#### 7.2 Configurar Particionamento
1. Em **Partition keys**, adicione:
   - `year`
   - `month` 
   - `day`
   - `symbol`

#### 7.3 Configurar Catalogação
1. **Database**: Selecione o database criado na infraestrutura
2. **Table name**: `cotacoes_b3_refined`
3. **Create a table in the Data Catalog**: ✅ Habilitado

### 8. Configurações do Job

#### 8.1 Job Details
1. Clique na aba **Job details**
2. Configure:
   - **Name**: `tech-challenge-b3-etl-job-dev`
   - **IAM Role**: Selecione o role criado na infraestrutura
   - **Glue version**: 3.0
   - **Language**: Python 3
   - **Worker type**: G.1X
   - **Number of workers**: 2
   - **Job timeout**: 60 minutes
   - **Number of retries**: 1

#### 8.2 Advanced Properties
```
--TempDir = s3://SEU-BUCKET-RAW/temp/
--job-bookmark-option = job-bookmark-enable
--enable-metrics = 
--enable-continuous-cloudwatch-log = true
--database_name = tech_challenge_b3_database_dev
```

### 9. Validação e Teste

#### 9.1 Validar Job
1. Clique em **Save** para salvar o job
2. Clique em **Run** para executar um teste
3. Monitore a execução na aba **Runs**

#### 9.2 Verificar Outputs
1. Verifique se os dados foram escritos no S3:
   ```bash
   aws s3 ls s3://SEU-BUCKET-REFINED/refined/ --recursive
   ```

2. Verifique se a tabela foi criada no Glue Catalog:
   ```bash
   aws glue get-table --database-name DATABASE-NAME --name cotacoes_b3_refined
   ```

### 10. Monitoramento

#### 10.1 CloudWatch Logs
- Acesse CloudWatch > Log groups
- Procure por `/aws-glue/jobs/tech-challenge-b3-etl-job-dev`
- Monitore logs de execução e erros

#### 10.2 Métricas do Job
- No console do Glue, vá para **Jobs** > **Monitoring**
- Visualize métricas de:
  - Duração da execução
  - Número de DPUs utilizadas
  - Taxa de sucesso/falha

## Troubleshooting

### Problemas Comuns

1. **Schema não inferido corretamente**:
   - Verifique se os dados estão no formato Parquet
   - Confirme se o caminho S3 está correto
   - Teste com um arquivo menor primeiro

2. **Erro de permissões**:
   - Verifique se o IAM role tem acesso aos buckets S3
   - Confirme permissões do Glue Catalog

3. **Job falha durante agregação**:
   - Verifique se todas as colunas existem nos dados
   - Confirme tipos de dados compatíveis
   - Teste com dataset menor

4. **Partições não criadas**:
   - Verifique se as colunas de partição existem
   - Confirme se os valores não são nulos
   - Execute `MSCK REPAIR TABLE` no Athena se necessário

### Comandos Úteis

```bash
# Verificar execuções do job
aws glue get-job-runs --job-name tech-challenge-b3-etl-job-dev

# Verificar tabela no catalog
aws glue get-table --database-name DATABASE-NAME --name cotacoes_b3_refined

# Listar partições
aws glue get-partitions --database-name DATABASE-NAME --table-name cotacoes_b3_refined

# Reparar partições no Athena
MSCK REPAIR TABLE cotacoes_b3_refined;
```

## Validação dos Requisitos

### ✅ Requisito 5A: Agrupamento numérico
- Implementado via nó **Aggregate**
- Agrupamento por `codigo_negociacao` e `nome_empresa`
- Sumarização de volumes, contagens e médias

### ✅ Requisito 5B: Renomear colunas
- Implementado via nó **Rename Field**
- Renomeadas: `volume_total_agregado` → `vol_financeiro_total`
- Renomeadas: `quantidade_total_papeis` → `qtd_acoes_negociadas`

### ✅ Requisito 5C: Cálculos com datas
- Implementado via nós **Derived Column**
- Cálculos de diferença entre datas
- Comparações e durações baseadas em data

### ✅ Requisito 6: Particionamento
- Dados salvos em formato Parquet
- Particionamento por `year`, `month`, `day`, `symbol`
- Estrutura: `refined/year=YYYY/month=MM/day=DD/symbol=ACAO/`

### ✅ Requisito 7: Catalogação automática
- Tabela criada automaticamente no Glue Catalog
- Database: `tech_challenge_b3_database_dev`
- Tabela: `cotacoes_b3_refined`

## Próximos Passos

Após configurar o job visual:
1. Testar com dados reais da B3
2. Configurar triggers automáticos via Lambda
3. Configurar Athena para consultas
4. Criar dashboards de monitoramento
5. Implementar alertas de falha

