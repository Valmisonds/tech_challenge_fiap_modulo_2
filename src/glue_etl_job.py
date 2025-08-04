#!/usr/bin/env python3
"""
Job ETL para dados da B3
Transformações: agrupamento, renomeação, cálculos de data
"""

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import *
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

args = getResolvedOptions(sys.argv, [
    'JOB_NAME', 'input_path', 'output_path', 'database_name', 'year', 'month', 'day'
])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

def read_data(path):
    """Lê dados do S3"""
    logger.info(f"Lendo: {path}")
    
    datasource = glueContext.create_dynamic_frame.from_options(
        format_options={"multiline": False},
        connection_type="s3",
        format="parquet",
        connection_options={"paths": [path], "recurse": True},
        transformation_ctx="datasource"
    )
    
    return datasource.toDF()

def transform_group_data(df):
    """Transformação A: Agrupamento numérico"""
    logger.info("Aplicando agrupamento")
    
    grouped = df.groupBy("codigo_negociacao", "nome_empresa").agg(
        sum("volume_total_negociado").alias("volume_total_agregado"),
        sum("numero_negocios").alias("total_negocios"),
        sum("quantidade_papeis_negociados").alias("quantidade_total_papeis"),
        avg("preco_ultimo_negocio").alias("preco_medio_ponderado"),
        max("preco_maximo").alias("preco_maximo_dia"),
        min("preco_minimo").alias("preco_minimo_dia"),
        first("preco_abertura").alias("preco_abertura_primeiro"),
        last("preco_ultimo_negocio").alias("preco_fechamento_ultimo"),
        count("*").alias("numero_registros_agregados"),
        first("year").alias("year"),
        first("month").alias("month"),
        first("day").alias("day")
    )
    
    return grouped

def transform_rename_columns(df):
    """Transformação B: Renomear colunas"""
    logger.info("Renomeando colunas")
    
    renamed = df.withColumnRenamed("volume_total_agregado", "vol_financeiro_total") \
               .withColumnRenamed("quantidade_total_papeis", "qtd_acoes_negociadas")
    
    return renamed

def transform_date_calculations(df):
    """Transformação C: Cálculos com datas"""
    logger.info("Calculando campos de data")
    
    year_val = int(args['year'])
    month_val = int(args['month'])
    day_val = int(args['day'])
    
    df_with_dates = df.withColumn("data_pregao", 
                                  to_date(lit(f"{year_val}-{month_val:02d}-{day_val:02d}"))) \
                      .withColumn("dia_semana", dayofweek(col("data_pregao"))) \
                      .withColumn("dia_ano", dayofyear(col("data_pregao"))) \
                      .withColumn("semana_ano", weekofyear(col("data_pregao"))) \
                      .withColumn("trimestre", quarter(col("data_pregao"))) \
                      .withColumn("dias_desde_inicio_ano", 
                                 datediff(col("data_pregao"), lit(f"{year_val}-01-01"))) \
                      .withColumn("dias_ate_fim_ano", 
                                 datediff(lit(f"{year_val}-12-31"), col("data_pregao"))) \
                      .withColumn("eh_inicio_mes", 
                                 when(col("day") <= 5, True).otherwise(False)) \
                      .withColumn("eh_fim_mes", 
                                 when(col("day") >= 25, True).otherwise(False))
    
    # Adicionar métricas calculadas
    df_final = df_with_dates.withColumn("ticket_medio", 
                                       col("vol_financeiro_total") / col("total_negocios")) \
                           .withColumn("variacao_percentual_dia",
                                      ((col("preco_fechamento_ultimo") - col("preco_abertura_primeiro")) / 
                                       col("preco_abertura_primeiro")) * 100) \
                           .withColumn("amplitude_preco", 
                                      col("preco_maximo_dia") - col("preco_minimo_dia")) \
                           .withColumn("volatilidade_relativa",
                                      (col("amplitude_preco") / col("preco_medio_ponderado")) * 100) \
                           .withColumn("symbol", col("codigo_negociacao"))
    
    return df_final

def write_data(df, output_path, database, table_name):
    """Escreve dados particionados no S3"""
    logger.info(f"Escrevendo em: {output_path}")
    
    # Converter para DynamicFrame
    dynamic_frame = DynamicFrame.fromDF(df, glueContext, "final_data")
    
    # Escrever no S3 com particionamento
    glueContext.write_dynamic_frame.from_options(
        frame=dynamic_frame,
        connection_type="s3",
        format="parquet",
        connection_options={
            "path": output_path,
            "partitionKeys": ["year", "month", "day", "symbol"]
        },
        transformation_ctx="datasink"
    )
    
    # Atualizar catálogo
    try:
        glueContext.write_dynamic_frame.from_catalog(
            frame=dynamic_frame,
            database=database,
            table_name=table_name,
            transformation_ctx="catalog_sink"
        )
    except Exception as e:
        logger.warning(f"Erro ao atualizar catálogo: {e}")

# Execução principal
try:
    df = read_data(args['input_path'])
    df = transform_group_data(df)
    df = transform_rename_columns(df)
    df = transform_date_calculations(df)
    
    write_data(df, args['output_path'], args['database_name'], "cotacoes_b3_refined")
    
    logger.info("Job concluído com sucesso")
    
except Exception as e:
    logger.error(f"Erro no job: {str(e)}")
    raise e

finally:
    job.commit()

