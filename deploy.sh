#!/bin/bash

# Script de Deploy para ATOS Application
# Uso: ./deploy.sh [environment]
# Exemplo: ./deploy.sh production

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Verificar se Docker está instalado
check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker não está instalado. Instale o Docker primeiro."
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose não está instalado. Instale o Docker Compose primeiro."
    fi
    
    log "Docker e Docker Compose encontrados"
}

# Verificar arquivo de ambiente
check_env() {
    if [ ! -f ".env" ]; then
        warn "Arquivo .env não encontrado. Copiando do exemplo..."
        if [ -f "env.production.example" ]; then
            cp env.production.example .env
            warn "Arquivo .env criado a partir do exemplo. Ajuste as configurações antes de continuar."
            read -p "Pressione Enter para continuar após ajustar o .env..."
        else
            error "Arquivo env.production.example não encontrado."
        fi
    fi
    log "Arquivo .env encontrado"
}

# Criar diretórios necessários
create_directories() {
    log "Criando diretórios necessários..."
    mkdir -p logs temp backup
    chmod 755 logs temp backup
    log "Diretórios criados com sucesso"
}

# Build da imagem
build_image() {
    log "Fazendo build da imagem Docker..."
    docker-compose build --no-cache
    log "Build concluído com sucesso"
}

# Parar containers existentes
stop_containers() {
    log "Parando containers existentes..."
    docker-compose down || true
    log "Containers parados"
}

# Iniciar aplicação
start_application() {
    log "Iniciando aplicação..."
    docker-compose up -d
    log "Aplicação iniciada"
}

# Verificar saúde da aplicação
health_check() {
    log "Verificando saúde da aplicação..."
    sleep 10
    
    # Tentar conectar na aplicação
    for i in {1..30}; do
        if curl -f http://localhost:80/ &> /dev/null; then
            log "Aplicação está respondendo corretamente"
            return 0
        fi
        log "Tentativa $i/30 - Aguardando aplicação inicializar..."
        sleep 2
    done
    
    error "Aplicação não está respondendo após 60 segundos"
}

# Mostrar logs
show_logs() {
    log "Mostrando logs da aplicação..."
    docker-compose logs -f --tail=50
}

# Função principal
main() {
    local environment=${1:-production}
    
    log "Iniciando deploy da aplicação ATOS (ambiente: $environment)"
    
    check_docker
    check_env
    create_directories
    stop_containers
    build_image
    start_application
    health_check
    
    log "Deploy concluído com sucesso!"
    log "Aplicação disponível em: http://localhost:80"
    log "Para ver os logs: docker-compose logs -f"
    log "Para parar: docker-compose down"
}

# Verificar argumentos
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Uso: $0 [environment]"
    echo "Environments: production, development"
    echo "Exemplo: $0 production"
    exit 0
fi

# Executar função principal
main "$@"
