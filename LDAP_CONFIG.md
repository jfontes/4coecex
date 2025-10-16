# Configuração do Active Directory / LDAP

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

1. **Autenticação**: O sistema primeiro tenta autenticar o usuário via Active Directory
2. **Criação de Usuário**: Se a autenticação for bem-sucedida e o usuário não existir no banco local, um novo usuário é criado automaticamente
3. **Fallback**: Se a autenticação LDAP falhar, o sistema tenta autenticar via banco de dados local

## Instalação da Dependência

Execute o comando abaixo para instalar a biblioteca LDAP3:

```bash
pip install ldap3==2.9.1
```

## Teste

Para testar a autenticação, use as credenciais de um usuário válido do Active Directory no formulário de login.
