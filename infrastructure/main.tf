# Tech Challenge B3 - Infraestrutura Terraform
# Pipeline de dados completo para pregão da B3

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Configuração do provider AWS
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Variáveis
variable "project_name" {
  description = "Nome do projeto"
  type        = string
  default     = "tech-challenge-b3"
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "Região AWS"
  type        = string
  default     = "us-east-1"
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# S3 Bucket para dados brutos
resource "aws_s3_bucket" "raw_data" {
  bucket = "${var.project_name}-raw-data-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "raw_data_versioning" {
  bucket = aws_s3_bucket.raw_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "raw_data_pab" {
  bucket = aws_s3_bucket.raw_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "raw_data_lifecycle" {
  bucket = aws_s3_bucket.raw_data.id

  rule {
    id     = "delete_old_versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# S3 Bucket para dados refinados
resource "aws_s3_bucket" "refined_data" {
  bucket = "${var.project_name}-refined-data-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "refined_data_versioning" {
  bucket = aws_s3_bucket.refined_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "refined_data_pab" {
  bucket = aws_s3_bucket.refined_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# IAM Role para Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_role.name
}

resource "aws_iam_role_policy" "lambda_glue_policy" {
  name = "GlueJobStartPolicy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "glue:StartJobRun",
          "glue:GetJobRun",
          "glue:GetJobRuns"
        ]
        Resource = aws_glue_job.etl_job.arn
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_s3_policy" {
  name = "S3AccessPolicy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion"
        ]
        Resource = [
          "${aws_s3_bucket.raw_data.arn}/*"
        ]
      }
    ]
  })
}

# IAM Role para Glue
resource "aws_iam_role" "glue_role" {
  name = "${var.project_name}-glue-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "glue_service" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
  role       = aws_iam_role.glue_role.name
}

resource "aws_iam_role_policy" "glue_s3_policy" {
  name = "S3DataAccessPolicy"
  role = aws_iam_role.glue_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.raw_data.arn,
          "${aws_s3_bucket.raw_data.arn}/*",
          aws_s3_bucket.refined_data.arn,
          "${aws_s3_bucket.refined_data.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "glue_catalog_policy" {
  name = "GlueCatalogPolicy"
  role = aws_iam_role.glue_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "glue:CreateDatabase",
          "glue:CreateTable",
          "glue:UpdateTable",
          "glue:GetDatabase",
          "glue:GetTable",
          "glue:GetTables",
          "glue:GetPartitions",
          "glue:CreatePartition",
          "glue:UpdatePartition"
        ]
        Resource = "*"
      }
    ]
  })
}

# Lambda Function
resource "aws_lambda_function" "trigger_glue" {
  filename         = "lambda_function.zip"
  function_name    = "${var.project_name}-trigger-glue-${var.environment}"
  role            = aws_iam_role.lambda_role.arn
  handler         = "index.lambda_handler"
  runtime         = "python3.9"
  timeout         = 60

  environment {
    variables = {
      GLUE_JOB_NAME    = aws_glue_job.etl_job.name
      REFINED_BUCKET   = aws_s3_bucket.refined_data.bucket
    }
  }

  depends_on = [data.archive_file.lambda_zip]
}

# Criar arquivo ZIP para Lambda
data "archive_file" "lambda_zip" {
  type        = "zip"
  output_path = "lambda_function.zip"
  
  source {
    content = templatefile("${path.module}/lambda_function.py", {
      glue_job_name    = "${var.project_name}-etl-job-${var.environment}"
      refined_bucket   = "${var.project_name}-refined-data-${var.environment}-${data.aws_caller_identity.current.account_id}"
    })
    filename = "index.py"
  }
}

# S3 Bucket Notification
resource "aws_s3_bucket_notification" "raw_data_notification" {
  bucket = aws_s3_bucket.raw_data.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.trigger_glue.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "raw/"
    filter_suffix       = ".parquet"
  }

  depends_on = [aws_lambda_permission.s3_invoke]
}

# Permission for S3 to invoke Lambda
resource "aws_lambda_permission" "s3_invoke" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.trigger_glue.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.raw_data.arn
}

# Glue Database
resource "aws_glue_catalog_database" "database" {
  name        = "${var.project_name}_database_${var.environment}"
  description = "Database for B3 stock market data"
}

# Glue Job
resource "aws_glue_job" "etl_job" {
  name         = "${var.project_name}-etl-job-${var.environment}"
  role_arn     = aws_iam_role.glue_role.arn
  glue_version = "3.0"
  
  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.raw_data.bucket}/scripts/etl_job.py"
    python_version  = "3"
  }

  default_arguments = {
    "--TempDir"                          = "s3://${aws_s3_bucket.raw_data.bucket}/temp/"
    "--job-bookmark-option"              = "job-bookmark-enable"
    "--enable-metrics"                   = ""
    "--enable-continuous-cloudwatch-log" = "true"
    "--database_name"                    = aws_glue_catalog_database.database.name
  }

  max_retries      = 1
  timeout          = 60
  number_of_workers = 2
  worker_type      = "G.1X"
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.trigger_glue.function_name}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "glue_logs" {
  name              = "/aws-glue/jobs/${aws_glue_job.etl_job.name}"
  retention_in_days = 14
}

# Outputs
output "raw_data_bucket_name" {
  description = "Nome do bucket S3 para dados brutos"
  value       = aws_s3_bucket.raw_data.bucket
}

output "refined_data_bucket_name" {
  description = "Nome do bucket S3 para dados refinados"
  value       = aws_s3_bucket.refined_data.bucket
}

output "lambda_function_name" {
  description = "Nome da função Lambda"
  value       = aws_lambda_function.trigger_glue.function_name
}

output "glue_job_name" {
  description = "Nome do job Glue ETL"
  value       = aws_glue_job.etl_job.name
}

output "glue_database_name" {
  description = "Nome do database Glue"
  value       = aws_glue_catalog_database.database.name
}

output "glue_service_role_arn" {
  description = "ARN do role de serviço do Glue"
  value       = aws_iam_role.glue_role.arn
}

