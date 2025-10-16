# Configuração do Active Directory / LDAP

## ⚠️ IMPORTANTE - Apenas Autenticação LDAP

O sistema foi configurado para usar **APENAS** autenticação via Active Directory. Não há fallback para banco de dados local.

## Variáveis de Ambiente

Para configurar a autenticação via Active Directory, defina as seguintes variáveis de ambiente:

```bash
# Domínio do Active Directory
LDAP_DOMAIN=tceac

# Host do servidor LDAP
LDAP_HOST=172.20.12.86

# Porta do servidor LDAP (389 para LDAP, 636 para LDAPS)
LDAP_PORT=389

# DN base para busca de usuários
LDAP_DN=ou=TribunalContas,dc=tceac,dc=local

# Usar SSL/TLS (true/false)
LDAP_USE_SSL=false
```

## Como Funciona

1. **Autenticação**: O sistema autentica o usuário via Active Directory
2. **Criação de Usuário**: Se a autenticação for bem-sucedida e o usuário não existir no banco local, um novo usuário é criado automaticamente
3. **Sem Fallback**: Se a autenticação LDAP falhar, o login falha (sem tentativa de banco local)

## Instalação no Servidor RedHat

### Opção 1: Script Automático
```bash
chmod +x install_ldap.sh
./install_ldap.sh
```

### Opção 2: Manual
```bash
# Instalar pip se necessário
yum install -y python3-pip
# ou
dnf install -y python3-pip

# Instalar ldap3
pip3 install ldap3==2.9.1
```

## Teste de Produção

### Teste Básico
```bash
python3 test_production_ldap.py
```

### Teste com Credenciais
```bash
python3 test_production_ldap.py joao.passos "Ongame123.@amelia...."
```

## Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'ldap3'"
**Solução**: Execute o script de instalação:
```bash
./install_ldap.sh
```

### Erro: "pip: comando não encontrado"
**Solução**: Instale pip primeiro:
```bash
yum install -y python3-pip
# ou
dnf install -y python3-pip
```

### Erro de Conectividade LDAP
**Verifique**:
- Servidor LDAP está acessível (172.20.12.86:389)
- Firewall permite conexão na porta 389
- Credenciais do usuário estão corretas no Active Directory
