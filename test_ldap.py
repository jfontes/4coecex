#!/usr/bin/env python3
"""
Script de teste para autenticação LDAP/Active Directory
Execute este script para testar a conectividade com o servidor LDAP
"""

import sys
import os

# Adiciona o diretório atual ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth import AuthenticationManager

def test_ldap_connection():
    """Testa a conexão com o servidor LDAP"""
    print("=== Teste de Conectividade LDAP ===")
    
    auth_manager = AuthenticationManager()
    
    # Solicita credenciais do usuário
    username = input("Digite o nome de usuário: ").strip()
    password = input("Digite a senha: ").strip()
    
    if not username or not password:
        print("❌ Username e senha são obrigatórios!")
        return False
    
    print(f"\n🔍 Testando autenticação para usuário: {username}")
    print("⏳ Aguarde...")
    
    try:
        # Testa a autenticação LDAP
        is_authenticated = auth_manager.authenticate_ldap(username, password)
        
        if is_authenticated:
            print("✅ Autenticação LDAP bem-sucedida!")
            
            # Tenta obter informações do usuário
            print("🔍 Buscando informações do usuário...")
            user_info = auth_manager.get_ldap_user_info(username, password)
            
            if user_info:
                print("✅ Informações do usuário obtidas com sucesso!")
                print(f"   Nome: {user_info.get('name', 'N/A')}")
                print(f"   Display Name: {user_info.get('display_name', 'N/A')}")
                print(f"   Email: {user_info.get('email', 'N/A')}")
                print(f"   Grupos: {len(user_info.get('groups', []))} grupos encontrados")
            else:
                print("⚠️  Autenticação OK, mas não foi possível obter informações do usuário")
            
            return True
        else:
            print("❌ Falha na autenticação LDAP")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False

def test_full_login():
    """Testa o fluxo completo de login"""
    print("\n=== Teste do Fluxo Completo de Login ===")
    
    auth_manager = AuthenticationManager()
    
    # Solicita credenciais do usuário
    username = input("Digite o nome de usuário: ").strip()
    password = input("Digite a senha: ").strip()
    
    if not username or not password:
        print("❌ Username e senha são obrigatórios!")
        return False
    
    print(f"\n🔍 Testando fluxo completo de login para usuário: {username}")
    print("⏳ Aguarde...")
    
    try:
        # Testa o fluxo completo de login
        user = auth_manager.login(username, password)
        
        if user:
            print("✅ Login bem-sucedido!")
            print(f"   Usuário: {user.username}")
            print(f"   Nome: {user.name}")
            print(f"   Email: {user.email}")
            print(f"   Ativo: {user.is_active}")
            return True
        else:
            print("❌ Falha no login")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Teste de Autenticação LDAP/Active Directory")
    print("=" * 50)
    
    while True:
        print("\nEscolha uma opção:")
        print("1. Testar apenas conectividade LDAP")
        print("2. Testar fluxo completo de login")
        print("3. Sair")
        
        choice = input("\nDigite sua escolha (1-3): ").strip()
        
        if choice == "1":
            test_ldap_connection()
        elif choice == "2":
            test_full_login()
        elif choice == "3":
            print("👋 Saindo...")
            break
        else:
            print("❌ Opção inválida!")
