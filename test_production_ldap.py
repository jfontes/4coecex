#!/usr/bin/env python3
"""
Script de teste para produção - autenticação LDAP/Active Directory
Funciona sem dependências do Flask, apenas testa a conectividade LDAP
"""

import sys
import os

def test_ldap_import():
    """Testa se a biblioteca ldap3 pode ser importada"""
    try:
        from ldap3 import Server, Connection, ALL, SUBTREE
        print("✅ Biblioteca ldap3 importada com sucesso!")
        return True
    except ImportError as e:
        print(f"❌ Erro ao importar ldap3: {e}")
        print("💡 Execute: pip3 install ldap3==2.9.1")
        return False

def test_ldap_connection():
    """Testa a conexão com o servidor LDAP"""
    try:
        from ldap3 import Server, Connection, ALL, SUBTREE
        from ldap3.core.exceptions import LDAPException
        
        # Configurações LDAP
        LDAP_DOMAIN = "tceac"
        LDAP_HOST = "172.20.12.86"
        LDAP_PORT = 389
        LDAP_DN = "ou=TribunalContas,dc=tceac,dc=local"
        
        print(f"🔍 Testando conexão com {LDAP_HOST}:{LDAP_PORT}")
        
        # Testa conectividade básica
        server = Server(LDAP_HOST, port=LDAP_PORT, use_ssl=False)
        conn = Connection(server, auto_bind=True)
        print("✅ Conectividade OK!")
        conn.unbind()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro de conectividade: {e}")
        return False

def test_authentication(username, password):
    """Testa a autenticação com credenciais específicas"""
    try:
        from ldap3 import Server, Connection, ALL, SUBTREE
        from ldap3.core.exceptions import LDAPException
        
        # Configurações LDAP
        LDAP_DOMAIN = "tceac"
        LDAP_HOST = "172.20.12.86"
        LDAP_PORT = 389
        LDAP_DN = "ou=TribunalContas,dc=tceac,dc=local"
        
        print(f"🔐 Testando autenticação para: {username}")
        
        server = Server(LDAP_HOST, port=LDAP_PORT, use_ssl=False)
        conn = Connection(
            server,
            user=f"{username}@{LDAP_DOMAIN}",
            password=password,
            authentication='SIMPLE',
            auto_bind=True
        )
        
        print("✅ Autenticação bem-sucedida!")
        conn.unbind()
        return True
        
    except Exception as e:
        print(f"❌ Falha na autenticação: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Teste de Produção - LDAP/Active Directory")
    print("=" * 50)
    
    # Teste 1: Importação da biblioteca
    print("\n1️⃣ Testando importação da biblioteca ldap3...")
    if not test_ldap_import():
        print("\n❌ FALHA: Biblioteca ldap3 não está instalada!")
        print("💡 Solução: Execute o script install_ldap.sh")
        sys.exit(1)
    
    # Teste 2: Conectividade
    print("\n2️⃣ Testando conectividade com o servidor...")
    if not test_ldap_connection():
        print("\n❌ FALHA: Não foi possível conectar ao servidor LDAP!")
        sys.exit(1)
    
    # Teste 3: Autenticação (se credenciais fornecidas)
    if len(sys.argv) >= 3:
        username = sys.argv[1]
        password = sys.argv[2]
        
        print(f"\n3️⃣ Testando autenticação com usuário: {username}")
        if test_authentication(username, password):
            print("\n🎉 TODOS OS TESTES PASSARAM!")
            print("✅ O sistema está pronto para autenticação LDAP!")
        else:
            print("\n❌ FALHA: Autenticação falhou!")
            sys.exit(1)
    else:
        print("\n✅ Conectividade OK!")
        print("💡 Para testar autenticação, execute:")
        print("   python3 test_production_ldap.py <username> <password>")
    
    print("\n🎯 Sistema pronto para produção!")
