import json
import boto3
import os
import logging
from urllib.parse import unquote_plus

logger = logging.getLogger()
logger.setLevel(logging.INFO)

glue_client = boto3.client('glue')

def lambda_handler(event, context):
    """
    Lambda function triggered by S3 events to start Glue ETL job
    """
    try:
        # Parse S3 event
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = unquote_plus(record['s3']['object']['key'])
            
            logger.info(f"Processing file: s3://{bucket}/{key}")
            
            # Extract date from key for job parameters
            # Expected format: raw/year=YYYY/month=MM/day=DD/filename.parquet
            path_parts = key.split('/')
            year = month = day = None
            
            for part in path_parts:
                if part.startswith('year='):
                    year = part.split('=')[1]
                elif part.startswith('month='):
                    month = part.split('=')[1]
                elif part.startswith('day='):
                    day = part.split('=')[1]
            
            if not all([year, month, day]):
                logger.error(f"Could not extract date from key: {key}")
                continue
            
            # Start Glue job
            job_name = os.environ['GLUE_JOB_NAME']
            refined_bucket = os.environ['REFINED_BUCKET']
            
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
            
            job_run_id = response['JobRunId']
            logger.info(f"Started Glue job {job_name} with run ID: {job_run_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps('Glue job started successfully')
        }
        
    except Exception as e:
        logger.error(f"Error starting Glue job: {str(e)}")
        raise e

