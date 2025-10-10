# Deploy da Aplicação ATOS

Este documento descreve como fazer o deploy da aplicação ATOS em um servidor Red Hat Enterprise Linux usando Docker.

## Pré-requisitos

### No Servidor Red Hat

1. **Docker Engine**
   ```bash
   # Instalar Docker
   sudo dnf install -y docker
   sudo systemctl enable docker
   sudo systemctl start docker
   sudo usermod -aG docker $USER
   ```

2. **Docker Compose**
   ```bash
   # Instalar Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

3. **Ferramentas adicionais**
   ```bash
   sudo dnf install -y curl wget git
   ```

## Configuração

### 1. Preparar o Ambiente

```bash
# Clonar o repositório (ou copiar os arquivos)
git clone <seu-repositorio> atos-app
cd atos-app

# Copiar arquivo de configuração
cp env.production.example .env

# Editar configurações
nano .env
```

### 2. Configurar Variáveis de Ambiente

Edite o arquivo `.env` com as configurações do seu ambiente:

```env
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=sua-chave-secreta-muito-segura

# Database Configuration
DB_SERVER=172.20.12.219
DB_NAME=ATOS
DB_USER=sis.atos
DB_PASSWORD=sua-senha-do-banco

# Gemini API Key
GEMINI_API_KEY=sua-chave-da-api-gemini

# LibreOffice Path (container)
LIBREOFFICE_PATH=/usr/lib64/libreoffice/program/soffice
```

## Deploy

### Opção 1: Deploy Automático (Recomendado)

```bash
# Tornar o script executável
chmod +x deploy.sh

# Executar deploy
./deploy.sh production
```

### Opção 2: Deploy Manual

```bash
# 1. Criar diretórios necessários
mkdir -p logs temp backup

# 2. Fazer build da imagem
docker-compose build

# 3. Iniciar aplicação
docker-compose up -d

# 4. Verificar logs
docker-compose logs -f
```

### Opção 3: Deploy com Proxy Reverso (Produção)

```bash
# A aplicação está configurada para trabalhar com proxy reverso existente
# Configure seu proxy reverso para apontar para localhost:80

# Verificar status
docker-compose ps
```

## Verificação

### 1. Health Check

```bash
# Verificar se a aplicação está respondendo
curl http://localhost:80/

# Verificar health check específico
curl http://localhost:80/health
```

### 2. Logs

```bash
# Ver logs da aplicação
docker-compose logs -f atos-app
```

### 3. Status dos Containers

```bash
# Ver status dos containers
docker-compose ps

# Ver uso de recursos
docker stats
```

## Gerenciamento

### Comandos Úteis

```bash
# Parar aplicação
docker-compose down

# Reiniciar aplicação
docker-compose restart

# Atualizar aplicação
docker-compose pull
docker-compose up -d

# Ver logs em tempo real
docker-compose logs -f

# Acessar container
docker-compose exec atos-app bash

# Backup do banco (se necessário)
docker-compose exec atos-app python -c "from app import app; from extensions import db; app.app_context().push(); db.create_all()"
```

### Monitoramento

```bash
# Verificar uso de recursos
docker stats

# Verificar espaço em disco
docker system df

# Limpar imagens não utilizadas
docker system prune -a
```

## Troubleshooting

### Problemas Comuns

1. **Erro de conexão com banco de dados**
   - Verificar se o servidor de banco está acessível
   - Verificar credenciais no arquivo `.env`
   - Verificar se o driver ODBC está instalado

2. **Aplicação não inicia**
   - Verificar logs: `docker-compose logs atos-app`
   - Verificar se todas as dependências estão instaladas
   - Verificar se as portas estão disponíveis

3. **Erro de permissões**
   - Verificar se os diretórios têm as permissões corretas
   - Verificar se o usuário tem acesso ao Docker

4. **Problemas de memória**
   - Ajustar limites no `docker-compose.yml`
   - Verificar se há recursos suficientes no servidor

### Logs Importantes

```bash
# Logs da aplicação
docker-compose logs atos-app

# Logs do sistema Docker
journalctl -u docker.service

# Logs do sistema
tail -f /var/log/messages
```

## Segurança

### Recomendações

1. **Alterar senhas padrão** no arquivo `.env`
2. **Usar HTTPS** em produção (configurar certificados SSL)
3. **Configurar firewall** para permitir apenas portas necessárias
4. **Fazer backups regulares** dos dados
5. **Monitorar logs** para detectar problemas

### Firewall (RHEL/CentOS)

```bash
# Permitir porta 80 (aplicação)
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --reload

# Se estiver usando proxy reverso, configure-o para apontar para localhost:80
```

## Backup e Restore

### Backup

```bash
# Backup dos arquivos da aplicação
tar -czf atos-backup-$(date +%Y%m%d).tar.gz \
    --exclude=venv \
    --exclude=__pycache__ \
    --exclude=.git \
    .

# Backup do banco de dados (se necessário)
# (Configure conforme seu sistema de banco)
```

### Restore

```bash
# Restaurar arquivos
tar -xzf atos-backup-YYYYMMDD.tar.gz

# Reconfigurar e reiniciar
cp env.production.example .env
# Editar .env com as configurações corretas
./deploy.sh production
```

## Suporte

Para suporte técnico, entre em contato com a equipe de desenvolvimento:
- Email: sistemas@tce.ac.gov.br
- Documentação: [Link para documentação interna]
