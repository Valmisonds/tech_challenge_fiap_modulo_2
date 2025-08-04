#!/bin/bash

# Tech Challenge B3 - Script de Deploy da Infraestrutura AWS
# Este script automatiza o deploy da infraestrutura usando CloudFormation

set -e  # Exit on any error

# Configurações
PROJECT_NAME="tech-challenge-b3"
ENVIRONMENT="dev"
REGION="us-east-1"
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções auxiliares
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se AWS CLI está instalado e configurado
check_aws_cli() {
    log_info "Verificando AWS CLI..."
    
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI não encontrado. Por favor, instale o AWS CLI."
        exit 1
    fi
    
    # Verificar credenciais
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS CLI não está configurado ou credenciais inválidas."
        log_info "Execute: aws configure"
        exit 1
    fi
    
    log_success "AWS CLI configurado corretamente"
}

# Validar template CloudFormation
validate_template() {
    log_info "Validando template CloudFormation..."
    
    if aws cloudformation validate-template --template-body file://cloudformation-template.yaml &> /dev/null; then
        log_success "Template CloudFormation válido"
    else
        log_error "Template CloudFormation inválido"
        exit 1
    fi
}

# Verificar se stack já existe
stack_exists() {
    aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &> /dev/null
}

# Deploy da stack
deploy_stack() {
    log_info "Iniciando deploy da infraestrutura..."
    
    if stack_exists; then
        log_info "Stack existente encontrada. Atualizando..."
        
        aws cloudformation update-stack \
            --stack-name "$STACK_NAME" \
            --template-body file://cloudformation-template.yaml \
            --parameters ParameterKey=ProjectName,ParameterValue="$PROJECT_NAME" \
                        ParameterKey=Environment,ParameterValue="$ENVIRONMENT" \
            --capabilities CAPABILITY_NAMED_IAM \
            --region "$REGION"
        
        log_info "Aguardando conclusão da atualização..."
        aws cloudformation wait stack-update-complete --stack-name "$STACK_NAME" --region "$REGION"
        
    else
        log_info "Criando nova stack..."
        
        aws cloudformation create-stack \
            --stack-name "$STACK_NAME" \
            --template-body file://cloudformation-template.yaml \
            --parameters ParameterKey=ProjectName,ParameterValue="$PROJECT_NAME" \
                        ParameterKey=Environment,ParameterValue="$ENVIRONMENT" \
            --capabilities CAPABILITY_NAMED_IAM \
            --region "$REGION"
        
        log_info "Aguardando conclusão da criação..."
        aws cloudformation wait stack-create-complete --stack-name "$STACK_NAME" --region "$REGION"
    fi
    
    log_success "Deploy da infraestrutura concluído!"
}

# Obter outputs da stack
get_stack_outputs() {
    log_info "Obtendo informações da stack..."
    
    echo ""
    echo "=== RECURSOS CRIADOS ==="
    
    # Obter outputs
    outputs=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs' \
        --output table)
    
    echo "$outputs"
    
    # Salvar outputs em arquivo
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs' \
        --output json > stack-outputs.json
    
    log_success "Outputs salvos em stack-outputs.json"
}

# Configurar variáveis de ambiente
setup_env_vars() {
    log_info "Configurando variáveis de ambiente..."
    
    # Extrair valores dos outputs
    RAW_BUCKET=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`RawDataBucketName`].OutputValue' \
        --output text)
    
    REFINED_BUCKET=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`RefinedDataBucketName`].OutputValue' \
        --output text)
    
    LAMBDA_FUNCTION=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`LambdaFunctionName`].OutputValue' \
        --output text)
    
    GLUE_JOB=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`GlueJobName`].OutputValue' \
        --output text)
    
    # Criar arquivo .env
    cat > ../.env << EOF
# Tech Challenge B3 - Variáveis de Ambiente
AWS_REGION=$REGION
S3_RAW_BUCKET=$RAW_BUCKET
S3_REFINED_BUCKET=$REFINED_BUCKET
LAMBDA_FUNCTION_NAME=$LAMBDA_FUNCTION
GLUE_JOB_NAME=$GLUE_JOB
PROJECT_NAME=$PROJECT_NAME
ENVIRONMENT=$ENVIRONMENT
EOF
    
    log_success "Arquivo .env criado com variáveis de ambiente"
}

# Função para deletar stack (opcional)
delete_stack() {
    log_warning "ATENÇÃO: Esta operação irá deletar toda a infraestrutura!"
    read -p "Tem certeza que deseja continuar? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deletando stack..."
        
        aws cloudformation delete-stack \
            --stack-name "$STACK_NAME" \
            --region "$REGION"
        
        log_info "Aguardando conclusão da deleção..."
        aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME" --region "$REGION"
        
        log_success "Stack deletada com sucesso!"
    else
        log_info "Operação cancelada."
    fi
}

# Menu principal
show_menu() {
    echo ""
    echo "=== TECH CHALLENGE B3 - DEPLOY INFRAESTRUTURA ==="
    echo "1. Deploy completo (criar/atualizar infraestrutura)"
    echo "2. Apenas validar template"
    echo "3. Mostrar outputs da stack"
    echo "4. Deletar infraestrutura"
    echo "5. Sair"
    echo ""
}

# Main
main() {
    cd "$(dirname "$0")"
    
    log_info "Tech Challenge B3 - Deploy da Infraestrutura AWS"
    log_info "Projeto: $PROJECT_NAME | Ambiente: $ENVIRONMENT | Região: $REGION"
    
    check_aws_cli
    
    if [ "$1" = "--delete" ]; then
        delete_stack
        exit 0
    fi
    
    if [ "$1" = "--deploy" ]; then
        validate_template
        deploy_stack
        get_stack_outputs
        setup_env_vars
        exit 0
    fi
    
    # Menu interativo
    while true; do
        show_menu
        read -p "Escolha uma opção: " choice
        
        case $choice in
            1)
                validate_template
                deploy_stack
                get_stack_outputs
                setup_env_vars
                ;;
            2)
                validate_template
                ;;
            3)
                get_stack_outputs
                ;;
            4)
                delete_stack
                ;;
            5)
                log_info "Saindo..."
                exit 0
                ;;
            *)
                log_error "Opção inválida!"
                ;;
        esac
        
        echo ""
        read -p "Pressione Enter para continuar..."
    done
}

# Executar main com argumentos
main "$@"

