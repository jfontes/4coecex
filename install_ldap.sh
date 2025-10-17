#!/bin/bash
# Script para instalar a dependência ldap3 no servidor RedHat

echo "🔧 Instalando dependência ldap3..."

# Tenta usar pip3 se pip não estiver disponível
if command -v pip3 &> /dev/null; then
    echo "📦 Usando pip3 para instalar ldap3..."
    pip3 install ldap3==2.9.1
elif command -v pip &> /dev/null; then
    echo "📦 Usando pip para instalar ldap3..."
    pip install ldap3==2.9.1
else
    echo "❌ pip/pip3 não encontrado. Instalando pip primeiro..."
    
    # Instala pip se não estiver disponível
    if command -v yum &> /dev/null; then
        yum install -y python3-pip
    elif command -v dnf &> /dev/null; then
        dnf install -y python3-pip
    else
        echo "❌ Gerenciador de pacotes não encontrado (yum/dnf)"
        exit 1
    fi
    
    # Tenta instalar novamente
    pip3 install ldap3==2.9.1
fi

echo "✅ Instalação concluída!"
echo "🧪 Testando importação..."
python3 -c "import ldap3; print('✅ ldap3 importado com sucesso!')"

if [ $? -eq 0 ]; then
    echo "🎉 ldap3 instalado e funcionando!"
else
    echo "❌ Erro ao importar ldap3"
    exit 1
fi
