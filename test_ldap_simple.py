#!/usr/bin/env python3
"""
Script de teste simples para autenticação LDAP/Active Directory
Testa apenas a conectividade sem dependências do Flask
"""

from ldap3 import Server, Connection, ALL, SUBTREE
from ldap3.core.exceptions import LDAPException

# Configurações LDAP (baseadas no seu código Java)
LDAP_DOMAIN = "tceac"
LDAP_HOST = "172.20.12.86"
LDAP_PORT = 389
LDAP_DN = "ou=TribunalContas,dc=tceac,dc=local"
LDAP_ATTRIBUTE_FOR_USER = "sAMAccountName"

def test_ldap_authentication(username, password):
    """Testa a autenticação LDAP"""
    try:
        print(f"🔍 Testando autenticação para usuário: {username}")
        print(f"🌐 Conectando ao servidor: {LDAP_HOST}:{LDAP_PORT}")
        
        # Configura o servidor LDAP
        server = Server(
            LDAP_HOST, 
            port=LDAP_PORT, 
            use_ssl=False,
            get_info=ALL
        )
        
        print("✅ Servidor LDAP configurado")
        
        # Cria a conexão LDAP
        conn = Connection(
            server,
            user=f"{username}@{LDAP_DOMAIN}",
            password=password,
            authentication='SIMPLE',
            auto_bind=True
        )
        
        print("✅ Conexão LDAP estabelecida com sucesso!")
        print("✅ Autenticação bem-sucedida!")
        
        # Busca informações do usuário
        print("🔍 Buscando informações do usuário...")
        search_filter = f"(&(objectClass=user)({LDAP_ATTRIBUTE_FOR_USER}={username}))"
        returned_attributes = ["sAMAccountName", "memberOf", "name", "displayName", "mail"]
        
        conn.search(
            search_base=LDAP_DN,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=returned_attributes
        )
        
        if conn.entries:
            entry = conn.entries[0]
            print("✅ Informações do usuário encontradas:")
            print(f"   Nome: {str(entry.name) if hasattr(entry, 'name') else 'N/A'}")
            print(f"   Display Name: {str(entry.displayName) if hasattr(entry, 'displayName') else 'N/A'}")
            print(f"   Email: {str(entry.mail) if hasattr(entry, 'mail') else 'N/A'}")
            print(f"   Grupos: {len(entry.memberOf) if hasattr(entry, 'memberOf') else 0} grupos")
        else:
            print("⚠️  Usuário autenticado, mas informações não encontradas")
        
        conn.unbind()
        return True
        
    except LDAPException as e:
        print(f"❌ Erro LDAP: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def test_connection_only():
    """Testa apenas a conectividade com o servidor"""
    try:
        print(f"🌐 Testando conectividade com {LDAP_HOST}:{LDAP_PORT}")
        
        server = Server(LDAP_HOST, port=LDAP_PORT, use_ssl=False)
        conn = Connection(server, auto_bind=True)
        
        print("✅ Conectividade OK!")
        conn.unbind()
        return True
        
    except Exception as e:
        print(f"❌ Erro de conectividade: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Teste de Autenticação LDAP/Active Directory")
    print("=" * 50)
    
    # Teste com as credenciais fornecidas
    username = "joao.passos"
    password = "Ongame123.@amelia...."
    
    print(f"📋 Testando com usuário: {username}")
    print("=" * 30)
    
    # Primeiro testa conectividade
    print("\n1️⃣ Testando conectividade...")
    if not test_connection_only():
        print("❌ Falha na conectividade. Verifique se o servidor está acessível.")
        exit(1)
    
    # Depois testa autenticação
    print("\n2️⃣ Testando autenticação...")
    success = test_ldap_authentication(username, password)
    
    if success:
        print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("✅ A autenticação LDAP está funcionando corretamente.")
    else:
        print("\n❌ TESTE FALHOU!")
        print("❌ Verifique as credenciais e configurações do servidor LDAP.")
