# Guia de Configuração do Amazon Athena

Este guia detalha como configurar e usar o Amazon Athena para consultar os dados processados pelo pipeline da B3.

## Pré-requisitos

1. Infraestrutura AWS provisionada
2. Job Glue executado com sucesso
3. Dados refinados disponíveis no S3
4. Tabela catalogada no Glue Data Catalog

## 1. Configuração Inicial do Athena

### 1.1 Acessar o Console do Athena

1. Faça login no AWS Console
2. Navegue para **Amazon Athena**
3. Se for o primeiro acesso, configure o local de resultados das consultas

### 1.2 Configurar Local de Resultados

1. Clique em **Settings** (Configurações)
2. Em **Query result location**, configure:
   ```
   s3://SEU-BUCKET-REFINED/athena-results/
   ```
3. Opcionalmente, configure encryption para os resultados
4. Clique em **Save**

### 1.3 Selecionar Database

1. No painel esquerdo, em **Database**, selecione:
   ```
   tech_challenge_b3_database_dev
   ```
2. Verifique se a tabela `cotacoes_b3_refined` aparece na lista

## 2. Verificação da Tabela

### 2.1 Verificar Schema da Tabela

```sql
DESCRIBE cotacoes_b3_refined;
```

**Resultado esperado:**
```
codigo_negociacao        string
nome_empresa            string
vol_financeiro_total    double
total_negocios          bigint
qtd_acoes_negociadas    bigint
preco_medio_ponderado   double
preco_maximo_dia        double
preco_minimo_dia        double
preco_abertura_primeiro double
preco_fechamento_ultimo double
variacao_percentual_dia double
volatilidade_relativa   double
ticket_medio            double
amplitude_preco         double
data_pregao             date
dia_semana              int
dia_ano                 int
semana_ano              int
trimestre               int
dias_desde_inicio_ano   int
dias_ate_fim_ano        int
eh_inicio_mes           boolean
eh_fim_mes              boolean
symbol                  string
year                    int
month                   int
day                     int
```

### 2.2 Verificar Partições

```sql
SHOW PARTITIONS cotacoes_b3_refined;
```

### 2.3 Contar Registros

```sql
SELECT COUNT(*) as total_registros 
FROM cotacoes_b3_refined;
```

## 3. Consultas Básicas de Validação

### 3.1 Verificar Dados por Partição

```sql
SELECT 
    year, month, day, symbol,
    COUNT(*) as registros
FROM cotacoes_b3_refined
GROUP BY year, month, day, symbol
ORDER BY year, month, day, symbol;
```

### 3.2 Verificar Qualidade dos Dados

```sql
-- Verificar valores nulos ou inválidos
SELECT 
    'Preços zero ou negativos' as problema,
    COUNT(*) as quantidade
FROM cotacoes_b3_refined
WHERE preco_medio_ponderado <= 0

UNION ALL

SELECT 
    'Volume zero' as problema,
    COUNT(*) as quantidade
FROM cotacoes_b3_refined
WHERE vol_financeiro_total = 0

UNION ALL

SELECT 
    'Códigos de negociação nulos' as problema,
    COUNT(*) as quantidade
FROM cotacoes_b3_refined
WHERE codigo_negociacao IS NULL;
```

### 3.3 Verificar Transformações Aplicadas

```sql
-- Verificar se agrupamento foi aplicado (deve ter 1 registro por ação por dia)
SELECT 
    codigo_negociacao,
    COUNT(*) as registros_por_acao
FROM cotacoes_b3_refined
WHERE year = 2025 AND month = 1 AND day = 15
GROUP BY codigo_negociacao
HAVING COUNT(*) > 1;
```

## 4. Consultas de Análise

### 4.1 Top 10 Ações por Volume

```sql
SELECT 
    codigo_negociacao,
    nome_empresa,
    vol_financeiro_total / 1000000 as volume_milhoes,
    total_negocios,
    variacao_percentual_dia
FROM cotacoes_b3_refined
ORDER BY vol_financeiro_total DESC
LIMIT 10;
```

### 4.2 Análise de Performance

```sql
SELECT 
    codigo_negociacao,
    variacao_percentual_dia,
    volatilidade_relativa,
    vol_financeiro_total,
    CASE 
        WHEN variacao_percentual_dia > 5 THEN 'Alta Positiva'
        WHEN variacao_percentual_dia > 0 THEN 'Baixa Positiva'
        WHEN variacao_percentual_dia > -5 THEN 'Baixa Negativa'
        ELSE 'Alta Negativa'
    END as categoria_performance
FROM cotacoes_b3_refined
ORDER BY variacao_percentual_dia DESC;
```

### 4.3 Análise Temporal

```sql
SELECT 
    dia_semana,
    CASE dia_semana
        WHEN 1 THEN 'Segunda'
        WHEN 2 THEN 'Terça'
        WHEN 3 THEN 'Quarta'
        WHEN 4 THEN 'Quinta'
        WHEN 5 THEN 'Sexta'
    END as nome_dia,
    COUNT(*) as total_acoes,
    AVG(vol_financeiro_total) as volume_medio,
    AVG(variacao_percentual_dia) as variacao_media
FROM cotacoes_b3_refined
GROUP BY dia_semana
ORDER BY dia_semana;
```

## 5. Otimização de Performance

### 5.1 Usar Filtros de Partição

**❌ Consulta ineficiente:**
```sql
SELECT * FROM cotacoes_b3_refined 
WHERE data_pregao = '2025-01-15';
```

**✅ Consulta otimizada:**
```sql
SELECT * FROM cotacoes_b3_refined 
WHERE year = 2025 AND month = 1 AND day = 15;
```

### 5.2 Limitar Colunas Selecionadas

**❌ Ineficiente:**
```sql
SELECT * FROM cotacoes_b3_refined;
```

**✅ Eficiente:**
```sql
SELECT codigo_negociacao, vol_financeiro_total, variacao_percentual_dia
FROM cotacoes_b3_refined;
```

### 5.3 Usar LIMIT para Testes

```sql
SELECT * FROM cotacoes_b3_refined 
LIMIT 100;
```

## 6. Manutenção e Troubleshooting

### 6.1 Reparar Partições

Se novas partições não aparecem automaticamente:

```sql
MSCK REPAIR TABLE cotacoes_b3_refined;
```

### 6.2 Atualizar Estatísticas

```sql
-- Verificar informações da tabela
SHOW TABLE EXTENDED LIKE 'cotacoes_b3_refined';

-- Verificar partições específicas
SHOW PARTITIONS cotacoes_b3_refined 
PARTITION (year=2025, month=1, day=15);
```

### 6.3 Problemas Comuns

#### Erro: "Table not found"
- Verificar se o database está selecionado
- Confirmar se a tabela foi criada pelo Glue
- Verificar permissões IAM

#### Erro: "No data found"
- Verificar se o job Glue foi executado
- Confirmar se os dados estão no S3
- Executar `MSCK REPAIR TABLE`

#### Performance lenta
- Usar filtros de partição
- Limitar colunas selecionadas
- Verificar formato dos dados (Parquet é mais eficiente)

## 7. Athena Notebooks (Opcional)

### 7.1 Criar Notebook

1. No console do Athena, vá para **Notebooks**
2. Clique em **Create notebook**
3. Configure:
   - **Name**: `b3-analysis-notebook`
   - **Description**: `Análise de dados da B3`

### 7.2 Configurar Kernel

1. Selecione **Python 3**
2. Configure instance type (recomendado: `ml.t3.medium`)
3. Clique em **Create**

### 7.3 Exemplo de Código para Notebook

```python
import pandas as pd
import boto3
import matplotlib.pyplot as plt

# Configurar cliente Athena
athena = boto3.client('athena')

# Executar consulta
query = """
SELECT codigo_negociacao, vol_financeiro_total, variacao_percentual_dia
FROM cotacoes_b3_refined
ORDER BY vol_financeiro_total DESC
LIMIT 10
"""

# Função para executar consulta
def run_athena_query(query, database='tech_challenge_b3_database_dev'):
    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': database},
        ResultConfiguration={'OutputLocation': 's3://SEU-BUCKET/athena-results/'}
    )
    return response['QueryExecutionId']

# Executar e obter resultados
query_id = run_athena_query(query)
# ... código para aguardar e obter resultados
```

## 8. Monitoramento e Custos

### 8.1 Monitorar Uso

1. No console do Athena, vá para **Query history**
2. Monitore:
   - Tempo de execução das consultas
   - Dados escaneados
   - Custos por consulta

### 8.2 Otimizar Custos

- Use particionamento efetivo
- Comprima dados (Parquet + Snappy)
- Limite o escopo das consultas
- Use LIMIT para testes
- Monitore dados escaneados

### 8.3 Alertas CloudWatch

Configure alertas para:
- Consultas com alto custo
- Consultas com longa duração
- Falhas frequentes

## 9. Integração com Ferramentas BI

### 9.1 Amazon QuickSight

1. No QuickSight, crie novo dataset
2. Selecione **Athena** como fonte
3. Configure conexão com database
4. Selecione tabela `cotacoes_b3_refined`

### 9.2 Tableau/Power BI

Use driver JDBC/ODBC do Athena:
- **JDBC URL**: `jdbc:awsathena://athena.us-east-1.amazonaws.com:443`
- **Driver**: Amazon Athena JDBC Driver

## 10. Validação Final

### 10.1 Checklist de Validação

- [ ] Tabela visível no Athena
- [ ] Partições carregadas corretamente
- [ ] Consultas básicas funcionando
- [ ] Dados consistentes com expectativas
- [ ] Performance aceitável
- [ ] Custos dentro do esperado

### 10.2 Consulta de Validação Completa

```sql
-- Validação completa dos requisitos
SELECT 
    'Requisito 8: Dados legíveis no Athena' as validacao,
    CASE 
        WHEN COUNT(*) > 0 THEN '✅ PASSOU'
        ELSE '❌ FALHOU'
    END as status,
    COUNT(*) as registros_encontrados
FROM cotacoes_b3_refined

UNION ALL

SELECT 
    'Transformação A: Agrupamento aplicado' as validacao,
    CASE 
        WHEN COUNT(DISTINCT codigo_negociacao) = COUNT(*) THEN '✅ PASSOU'
        ELSE '❌ FALHOU'
    END as status,
    COUNT(*) as registros_por_acao
FROM cotacoes_b3_refined
WHERE year = 2025 AND month = 1 AND day = 15

UNION ALL

SELECT 
    'Transformação B: Colunas renomeadas' as validacao,
    CASE 
        WHEN COUNT(*) > 0 THEN '✅ PASSOU'
        ELSE '❌ FALHOU'
    END as status,
    COUNT(*) as registros_com_colunas_renomeadas
FROM cotacoes_b3_refined
WHERE vol_financeiro_total IS NOT NULL 
  AND qtd_acoes_negociadas IS NOT NULL

UNION ALL

SELECT 
    'Transformação C: Cálculos de data' as validacao,
    CASE 
        WHEN COUNT(*) > 0 THEN '✅ PASSOU'
        ELSE '❌ FALHOU'
    END as status,
    COUNT(*) as registros_com_calculos_data
FROM cotacoes_b3_refined
WHERE dias_desde_inicio_ano IS NOT NULL 
  AND dia_semana IS NOT NULL;
```

## Próximos Passos

Após configurar o Athena:
1. Criar dashboards no QuickSight
2. Configurar alertas de monitoramento
3. Documentar consultas frequentes
4. Treinar usuários finais
5. Implementar governança de dados

