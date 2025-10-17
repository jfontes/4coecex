from models import User
from ldap3 import Server, Connection, ALL, SUBTREE
from ldap3.core.exceptions import LDAPException
import config

class AuthenticationManager:
    """
    Classe modular para gerenciar a autenticação de usuários.
    Projetada para ser facilmente adaptada para o Active Directory.
    """
    
    def authenticate_ldap(self, username, password):
        """
        Autentica o usuário via Active Directory/LDAP.
        Retorna True se as credenciais forem válidas, False caso contrário.
        """
        #return True
        try:
            # Configura o servidor LDAP
            server = Server(
                config.LDAP_HOST, 
                port=config.LDAP_PORT, 
                use_ssl=config.LDAP_USE_SSL,
                get_info=ALL
            )
            
            # Cria a conexão LDAP
            conn = Connection(
                server,
                user=f"{username}@{config.LDAP_DOMAIN}",
                password=password,
                authentication='SIMPLE',
                auto_bind=True
            )
            
            # Se chegou até aqui, a autenticação foi bem-sucedida
            conn.unbind()
            return True
            
        except LDAPException as e:
            print(f"Erro na autenticação LDAP: {e}")
            return False
        except Exception as e:
            print(f"Erro inesperado na autenticação LDAP: {e}")
            return False
    
    def get_ldap_user_info(self, username, password):
        """
        Obtém informações do usuário do Active Directory.
        Retorna um dicionário com as informações do usuário ou None se não encontrar.
        """
        try:
            # Configura o servidor LDAP
            server = Server(
                config.LDAP_HOST, 
                port=config.LDAP_PORT, 
                use_ssl=config.LDAP_USE_SSL,
                get_info=ALL
            )
            
            # Cria a conexão LDAP
            conn = Connection(
                server,
                user=f"{username}@{config.LDAP_DOMAIN}",
                password=password,
                authentication='SIMPLE',
                auto_bind=True
            )
            
            # Busca informações do usuário
            search_filter = f"(&(objectClass=user)({config.LDAP_ATTRIBUTE_FOR_USER}={username}))"
            returned_attributes = ["sAMAccountName", "memberOf", "name", "displayName", "mail"]
            
            conn.search(
                search_base=config.LDAP_DN,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=returned_attributes
            )
            
            if conn.entries:
                entry = conn.entries[0]
                user_info = {
                    'username': str(entry.sAMAccountName) if hasattr(entry, 'sAMAccountName') else username,
                    'name': str(entry.name) if hasattr(entry, 'name') else username,
                    'display_name': str(entry.displayName) if hasattr(entry, 'displayName') else username,
                    'email': str(entry.mail) if hasattr(entry, 'mail') else None,
                    'groups': [str(group) for group in entry.memberOf] if hasattr(entry, 'memberOf') else []
                }
                conn.unbind()
                return user_info
            
            conn.unbind()
            return None
            
        except LDAPException as e:
            print(f"Erro ao buscar informações do usuário LDAP: {e}")
            return None
        except Exception as e:
            print(f"Erro inesperado ao buscar informações do usuário LDAP: {e}")
            return None
    
    def login(self, username, password):
        """
        Valida as credenciais do usuário APENAS via Active Directory.
        Retorna o objeto User em caso de sucesso, ou None em caso de falha.
        """
        # --- AUTENTICAÇÃO VIA ACTIVE DIRECTORY ---
        if self.authenticate_ldap(username, password):
            # Busca o usuário no banco local ou cria um novo se não existir
            user = User.query.filter_by(username=username).first()
            
            if not user:
                # Obtém informações do usuário do AD
                ldap_info = self.get_ldap_user_info(username, password)
                
                # Cria um novo usuário no banco local
                from models import CargoEnum
                user = User(
                    username=username,
                    nome=ldap_info['display_name'] if ldap_info else username,
                    cargo=CargoEnum.TECNICO,  # Valor padrão para novos usuários
                    matricula=None
                )
                # Define uma senha aleatória (não será usada, pois a autenticação é via AD)
                user.set_password("ldap_authenticated_user")
                
                from extensions import db
                db.session.add(user)
                db.session.commit()
            
            return user

        # --- APENAS AUTENTICAÇÃO LDAP - SEM FALLBACK ---
        return None