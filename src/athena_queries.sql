-- Tech Challenge B3 - Consultas Athena
-- Consultas SQL para análise dos dados processados do pregão da B3

-- =====================================================
-- 1. CONSULTAS BÁSICAS DE VERIFICAÇÃO
-- =====================================================

-- Verificar se a tabela foi criada corretamente
DESCRIBE cotacoes_b3_refined;

-- Contar total de registros
SELECT COUNT(*) as total_registros 
FROM cotacoes_b3_refined;

-- Verificar partições disponíveis
SELECT DISTINCT year, month, day, symbol
FROM cotacoes_b3_refined
ORDER BY year, month, day, symbol;

-- =====================================================
-- 2. ANÁLISES BÁSICAS POR AÇÃO
-- =====================================================

-- Top 10 ações por volume financeiro
SELECT 
    codigo_negociacao,
    nome_empresa,
    vol_financeiro_total,
    total_negocios,
    qtd_acoes_negociadas,
    preco_medio_ponderado
FROM cotacoes_b3_refined
ORDER BY vol_financeiro_total DESC
LIMIT 10;

-- Ações com maior variação percentual (positiva e negativa)
SELECT 
    codigo_negociacao,
    nome_empresa,
    variacao_percentual_dia,
    preco_abertura_primeiro,
    preco_fechamento_ultimo,
    vol_financeiro_total
FROM cotacoes_b3_refined
ORDER BY variacao_percentual_dia DESC
LIMIT 5;

-- Ações com maior volatilidade
SELECT 
    codigo_negociacao,
    nome_empresa,
    volatilidade_relativa,
    amplitude_preco,
    preco_maximo_dia,
    preco_minimo_dia
FROM cotacoes_b3_refined
ORDER BY volatilidade_relativa DESC
LIMIT 10;

-- =====================================================
-- 3. ANÁLISES AGREGADAS DO MERCADO
-- =====================================================

-- Resumo geral do mercado por dia
SELECT 
    data_pregao,
    COUNT(*) as total_acoes,
    SUM(vol_financeiro_total) as volume_total_mercado,
    AVG(preco_medio_ponderado) as preco_medio_mercado,
    SUM(total_negocios) as negocios_totais,
    SUM(qtd_acoes_negociadas) as acoes_negociadas_total
FROM cotacoes_b3_refined
GROUP BY data_pregao
ORDER BY data_pregao;

-- Distribuição de ações por faixa de preço
SELECT 
    CASE 
        WHEN preco_medio_ponderado < 10 THEN 'Até R$ 10'
        WHEN preco_medio_ponderado < 25 THEN 'R$ 10 - R$ 25'
        WHEN preco_medio_ponderado < 50 THEN 'R$ 25 - R$ 50'
        WHEN preco_medio_ponderado < 100 THEN 'R$ 50 - R$ 100'
        ELSE 'Acima de R$ 100'
    END as faixa_preco,
    COUNT(*) as quantidade_acoes,
    AVG(vol_financeiro_total) as volume_medio
FROM cotacoes_b3_refined
GROUP BY 
    CASE 
        WHEN preco_medio_ponderado < 10 THEN 'Até R$ 10'
        WHEN preco_medio_ponderado < 25 THEN 'R$ 10 - R$ 25'
        WHEN preco_medio_ponderado < 50 THEN 'R$ 25 - R$ 50'
        WHEN preco_medio_ponderado < 100 THEN 'R$ 50 - R$ 100'
        ELSE 'Acima de R$ 100'
    END
ORDER BY 
    CASE 
        WHEN faixa_preco = 'Até R$ 10' THEN 1
        WHEN faixa_preco = 'R$ 10 - R$ 25' THEN 2
        WHEN faixa_preco = 'R$ 25 - R$ 50' THEN 3
        WHEN faixa_preco = 'R$ 50 - R$ 100' THEN 4
        ELSE 5
    END;

-- =====================================================
-- 4. ANÁLISES TEMPORAIS
-- =====================================================

-- Análise por dia da semana
SELECT 
    dia_semana,
    CASE dia_semana
        WHEN 1 THEN 'Segunda-feira'
        WHEN 2 THEN 'Terça-feira'
        WHEN 3 THEN 'Quarta-feira'
        WHEN 4 THEN 'Quinta-feira'
        WHEN 5 THEN 'Sexta-feira'
        WHEN 6 THEN 'Sábado'
        WHEN 7 THEN 'Domingo'
    END as nome_dia,
    COUNT(*) as total_acoes,
    AVG(vol_financeiro_total) as volume_medio,
    AVG(variacao_percentual_dia) as variacao_media
FROM cotacoes_b3_refined
GROUP BY dia_semana
ORDER BY dia_semana;

-- Análise por trimestre
SELECT 
    trimestre,
    COUNT(*) as total_acoes,
    SUM(vol_financeiro_total) as volume_total,
    AVG(variacao_percentual_dia) as variacao_media,
    AVG(volatilidade_relativa) as volatilidade_media
FROM cotacoes_b3_refined
GROUP BY trimestre
ORDER BY trimestre;

-- Análise de início vs fim de mês
SELECT 
    CASE 
        WHEN eh_inicio_mes THEN 'Início do Mês'
        WHEN eh_fim_mes THEN 'Fim do Mês'
        ELSE 'Meio do Mês'
    END as periodo_mes,
    COUNT(*) as total_acoes,
    AVG(vol_financeiro_total) as volume_medio,
    AVG(variacao_percentual_dia) as variacao_media
FROM cotacoes_b3_refined
GROUP BY 
    CASE 
        WHEN eh_inicio_mes THEN 'Início do Mês'
        WHEN eh_fim_mes THEN 'Fim do Mês'
        ELSE 'Meio do Mês'
    END;

-- =====================================================
-- 5. ANÁLISES AVANÇADAS
-- =====================================================

-- Ranking de ações por múltiplas métricas
SELECT 
    codigo_negociacao,
    nome_empresa,
    vol_financeiro_total,
    variacao_percentual_dia,
    volatilidade_relativa,
    ticket_medio,
    -- Rankings
    ROW_NUMBER() OVER (ORDER BY vol_financeiro_total DESC) as rank_volume,
    ROW_NUMBER() OVER (ORDER BY ABS(variacao_percentual_dia) DESC) as rank_variacao,
    ROW_NUMBER() OVER (ORDER BY volatilidade_relativa DESC) as rank_volatilidade
FROM cotacoes_b3_refined
ORDER BY vol_financeiro_total DESC;

-- Correlação entre volume e variação de preço
SELECT 
    CASE 
        WHEN vol_financeiro_total < 1000000 THEN 'Volume Baixo'
        WHEN vol_financeiro_total < 5000000 THEN 'Volume Médio'
        ELSE 'Volume Alto'
    END as categoria_volume,
    AVG(ABS(variacao_percentual_dia)) as variacao_media_absoluta,
    AVG(volatilidade_relativa) as volatilidade_media,
    COUNT(*) as quantidade_acoes
FROM cotacoes_b3_refined
GROUP BY 
    CASE 
        WHEN vol_financeiro_total < 1000000 THEN 'Volume Baixo'
        WHEN vol_financeiro_total < 5000000 THEN 'Volume Médio'
        ELSE 'Volume Alto'
    END
ORDER BY 
    CASE 
        WHEN categoria_volume = 'Volume Baixo' THEN 1
        WHEN categoria_volume = 'Volume Médio' THEN 2
        ELSE 3
    END;

-- =====================================================
-- 6. CONSULTAS PARA MONITORAMENTO
-- =====================================================

-- Verificar qualidade dos dados
SELECT 
    'Registros com preço zero' as metrica,
    COUNT(*) as quantidade
FROM cotacoes_b3_refined
WHERE preco_medio_ponderado = 0

UNION ALL

SELECT 
    'Registros com volume zero' as metrica,
    COUNT(*) as quantidade
FROM cotacoes_b3_refined
WHERE vol_financeiro_total = 0

UNION ALL

SELECT 
    'Registros com variação extrema (>50%)' as metrica,
    COUNT(*) as quantidade
FROM cotacoes_b3_refined
WHERE ABS(variacao_percentual_dia) > 50;

-- Estatísticas gerais por partição
SELECT 
    year,
    month,
    day,
    COUNT(*) as total_registros,
    COUNT(DISTINCT symbol) as acoes_unicas,
    SUM(vol_financeiro_total) as volume_total,
    AVG(preco_medio_ponderado) as preco_medio,
    MIN(data_pregao) as data_min,
    MAX(data_pregao) as data_max
FROM cotacoes_b3_refined
GROUP BY year, month, day
ORDER BY year, month, day;

-- =====================================================
-- 7. CONSULTAS PARA DASHBOARD
-- =====================================================

-- Dados para gráfico de volume por ação (Top 10)
SELECT 
    codigo_negociacao,
    vol_financeiro_total / 1000000 as volume_milhoes
FROM cotacoes_b3_refined
ORDER BY vol_financeiro_total DESC
LIMIT 10;

-- Dados para gráfico de variação percentual
SELECT 
    codigo_negociacao,
    variacao_percentual_dia,
    CASE 
        WHEN variacao_percentual_dia > 0 THEN 'Positiva'
        WHEN variacao_percentual_dia < 0 THEN 'Negativa'
        ELSE 'Neutra'
    END as tipo_variacao
FROM cotacoes_b3_refined
ORDER BY variacao_percentual_dia DESC;

-- Dados para gráfico de distribuição de preços
SELECT 
    FLOOR(preco_medio_ponderado / 10) * 10 as faixa_preco_inicio,
    FLOOR(preco_medio_ponderado / 10) * 10 + 10 as faixa_preco_fim,
    COUNT(*) as quantidade_acoes
FROM cotacoes_b3_refined
GROUP BY FLOOR(preco_medio_ponderado / 10)
ORDER BY faixa_preco_inicio;

-- =====================================================
-- 8. MANUTENÇÃO E OTIMIZAÇÃO
-- =====================================================

-- Reparar partições (executar se necessário)
MSCK REPAIR TABLE cotacoes_b3_refined;

-- Verificar partições
SHOW PARTITIONS cotacoes_b3_refined;

-- Estatísticas da tabela
SHOW TABLE EXTENDED LIKE 'cotacoes_b3_refined';

-- Verificar schema atual
SHOW CREATE TABLE cotacoes_b3_refined;

