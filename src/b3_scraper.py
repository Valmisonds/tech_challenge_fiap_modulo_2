#!/usr/bin/env python3
"""
Scraper para dados históricos da B3
Baixa arquivos COTAHIST e converte para parquet
"""

import requests
import pandas as pd
import os
from datetime import datetime, timedelta
import zipfile
import io
import logging
from pathlib import Path
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class B3Scraper:
    """Extrai dados históricos da B3"""
    
    def __init__(self, s3_bucket=None, local_path="./data/raw"):
        self.s3_bucket = s3_bucket
        self.local_path = Path(local_path)
        self.local_path.mkdir(parents=True, exist_ok=True)
        
        if self.s3_bucket:
            self.s3_client = boto3.client('s3')
    
    def get_cotahist_url(self, date):
        """URL do arquivo COTAHIST para a data"""
        date_str = date.strftime("%d%m%Y")
        filename = f"COTAHIST_{date_str}.ZIP"
        return f"https://bvmf.bmfbovespa.com.br/InstDados/SerHist/{filename}"
    
    def download_data(self, date):
        """Baixa e extrai dados do COTAHIST"""
        try:
            url = self.get_cotahist_url(date)
            logger.info(f"Baixando {date.strftime('%Y-%m-%d')}")
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                txt_files = [f for f in zip_file.namelist() if f.endswith('.TXT')]
                if not txt_files:
                    return None
                
                with zip_file.open(txt_files[0]) as txt_file:
                    content = txt_file.read().decode('latin-1')
                    
            return content
            
        except Exception as e:
            logger.error(f"Erro ao baixar {date}: {e}")
            return None
    
    def parse_cotahist(self, content):
        """Converte dados COTAHIST para DataFrame"""
        lines = content.strip().split('\n')
        data = []
        
        for line in lines:
            if len(line) < 245 or line[0:2] != '01':
                continue
                
            try:
                record = {
                    'codigo_negociacao': line[12:24].strip(),
                    'nome_empresa': line[27:39].strip(),
                    'preco_abertura': float(line[56:69].strip()) / 100 if line[56:69].strip() else 0,
                    'preco_maximo': float(line[69:82].strip()) / 100 if line[69:82].strip() else 0,
                    'preco_minimo': float(line[82:95].strip()) / 100 if line[82:95].strip() else 0,
                    'preco_ultimo_negocio': float(line[108:121].strip()) / 100 if line[108:121].strip() else 0,
                    'numero_negocios': int(line[147:152].strip()) if line[147:152].strip() else 0,
                    'quantidade_papeis_negociados': int(line[152:170].strip()) if line[152:170].strip() else 0,
                    'volume_total_negociado': float(line[170:188].strip()) / 100 if line[170:188].strip() else 0,
                }
                data.append(record)
            except:
                continue
        
        return pd.DataFrame(data)
    
    def save_parquet(self, df, date):
        """Salva dados em parquet particionado"""
        if df.empty:
            return None
            
        df['year'] = date.year
        df['month'] = date.month
        df['day'] = date.day
        
        partition_path = self.local_path / f"year={date.year}" / f"month={date.month:02d}" / f"day={date.day:02d}"
        partition_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"cotacoes_{date.strftime('%Y%m%d')}.parquet"
        file_path = partition_path / filename
        
        df.to_parquet(file_path, index=False)
        logger.info(f"Salvo: {file_path}")
        
        return file_path
    
    def upload_s3(self, local_file, date):
        """Upload para S3"""
        if not self.s3_bucket:
            return None
            
        try:
            s3_key = f"raw/year={date.year}/month={date.month:02d}/day={date.day:02d}/cotacoes_{date.strftime('%Y%m%d')}.parquet"
            self.s3_client.upload_file(str(local_file), self.s3_bucket, s3_key)
            logger.info(f"Upload S3: s3://{self.s3_bucket}/{s3_key}")
            return s3_key
        except Exception as e:
            logger.error(f"Erro upload S3: {e}")
            return None
    
    def process_date(self, date):
        """Processa uma data específica"""
        if date.weekday() >= 5:  # Skip weekends
            return None
            
        content = self.download_data(date)
        if not content:
            return None
            
        df = self.parse_cotahist(content)
        if df.empty:
            return None
            
        local_file = self.save_parquet(df, date)
        s3_key = self.upload_s3(local_file, date)
        
        return {
            'date': date,
            'records': len(df),
            'local_file': local_file,
            's3_key': s3_key
        }

def main():
    """Executa scraper para últimos dias úteis"""
    bucket = os.getenv('S3_BUCKET_NAME', 'tech-challenge-b3-raw-bucket-dev')
    
    scraper = B3Scraper(s3_bucket=bucket)
    
    # Últimos 5 dias úteis
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=10)
    
    results = []
    current = start_date
    
    while current <= end_date:
        result = scraper.process_date(current)
        if result:
            results.append(result)
        current += timedelta(days=1)
    
    total_records = sum(r['records'] for r in results)
    logger.info(f"Concluído: {len(results)} arquivos, {total_records} registros")
    
    return results

if __name__ == "__main__":
    main()

