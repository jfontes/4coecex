#!/bin/bash

# Script de Deploy específico para Red Hat Enterprise Linux
# Uso: ./deploy-redhat.sh [environment]
# Exemplo: ./deploy-redhat.sh production

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Verificar se está rodando como root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        warn "Executando como root. Recomendado executar como usuário não-root com sudo."
    fi
}

# Verificar se Docker está instalado e rodando
check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker não está instalado. Execute: sudo dnf install -y docker"
    fi
    
    if ! systemctl is-active --quiet docker; then
        warn "Docker não está rodando. Iniciando..."
        sudo systemctl start docker
        sudo systemctl enable docker
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose não está instalado. Instale primeiro."
    fi
    
    log "Docker e Docker Compose estão funcionando"
}

# Verificar se o usuário está no grupo docker
check_docker_group() {
    if ! groups $USER | grep -q docker; then
        warn "Usuário $USER não está no grupo docker."
        warn "Execute: sudo usermod -aG docker $USER"
        warn "Depois faça logout e login novamente."
        read -p "Continuar mesmo assim? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Verificar arquivo de ambiente
check_env() {
    if [ ! -f ".env" ]; then
        warn "Arquivo .env não encontrado. Copiando do exemplo..."
        if [ -f "env.production.example" ]; then
            cp env.production.example .env
            warn "Arquivo .env criado a partir do exemplo."
            warn "IMPORTANTE: Ajuste as configurações antes de continuar!"
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
    sudo mkdir -p logs temp backup
    sudo chown -R $USER:$USER logs temp backup
    sudo chmod 755 logs temp backup
    log "Diretórios criados com sucesso"
}

# Verificar conectividade com banco de dados
check_database() {
    log "Verificando conectividade com banco de dados..."
    
    # Carregar variáveis do .env
    source .env
    
    # Testar conexão usando Python
    python3 -c "
import pyodbc
import os
from urllib.parse import quote_plus

# Carregar variáveis de ambiente
db_server = os.environ.get('DB_SERVER', '172.20.12.219')
db_name = os.environ.get('DB_NAME', 'ATOS')
db_user = os.environ.get('DB_USER', 'sis.atos')
db_password = os.environ.get('DB_PASSWORD', 'sisatos@TCEAC@2025')

odbc_str = (
    f'DRIVER={{ODBC Driver 17 for SQL Server}};'
    f'SERVER={db_server};'
    f'DATABASE={db_name};'
    f'UID={db_user};'
    f'PWD={db_password};'
    f'Trusted_Connection=no;'
)

try:
    conn = pyodbc.connect(odbc_str)
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    result = cursor.fetchone()
    conn.close()
    print('Conexão com banco de dados: OK')
except Exception as e:
    print(f'Erro na conexão com banco: {e}')
    exit(1)
" || error "Não foi possível conectar ao banco de dados. Verifique as configurações."
}

# Build da imagem usando Dockerfile específico para Red Hat
build_image() {
    log "Fazendo build da imagem Docker para Red Hat..."
    
    # Usar Dockerfile específico para Red Hat se existir
    if [ -f "Dockerfile.redhat" ]; then
        docker build -f Dockerfile.redhat -t atos-app:latest .
    else
        docker build -t atos-app:latest .
    fi
    
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
    sleep 15
    
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

# Configurar firewall (opcional)
configure_firewall() {
    if command -v firewall-cmd &> /dev/null; then
        log "Configurando firewall..."
        sudo firewall-cmd --permanent --add-port=80/tcp || true
        sudo firewall-cmd --reload || true
        log "Firewall configurado"
    else
        warn "firewall-cmd não encontrado. Configure o firewall manualmente se necessário."
    fi
}

# Mostrar informações do sistema
show_system_info() {
    log "Informações do sistema:"
    info "Sistema Operacional: $(cat /etc/redhat-release 2>/dev/null || echo 'Não é Red Hat')"
    info "Versão do Docker: $(docker --version)"
    info "Versão do Docker Compose: $(docker-compose --version)"
    info "Usuário atual: $USER"
    info "Diretório atual: $(pwd)"
}

# Função principal
main() {
    local environment=${1:-production}
    
    log "Iniciando deploy da aplicação ATOS no Red Hat (ambiente: $environment)"
    
    show_system_info
    check_root
    check_docker
    check_docker_group
    check_env
    create_directories
    check_database
    stop_containers
    build_image
    start_application
    health_check
    configure_firewall
    
    log "Deploy concluído com sucesso!"
    log "Aplicação disponível em: http://localhost:80"
    log "Para ver os logs: docker-compose logs -f"
    log "Para parar: docker-compose down"
    log "Para reiniciar: docker-compose restart"
}

# Verificar argumentos
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Uso: $0 [environment]"
    echo "Environments: production, development"
    echo "Exemplo: $0 production"
    echo ""
    echo "Este script é específico para Red Hat Enterprise Linux"
    echo "e inclui verificações e configurações específicas do RHEL."
    exit 0
fi

# Executar função principal
main "$@"
