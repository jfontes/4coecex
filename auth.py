from models import User

class AuthenticationManager:
    """
    Classe modular para gerenciar a autenticação de usuários.
    Projetada para ser facilmente adaptada para o Active Directory.
    """
    def login(self, username, password):
        """
        Valida as credenciais do usuário.
        Retorna o objeto User em caso de sucesso, ou None em caso de falha.
        """
        # --- LÓGICA DE TESTE ATUAL (VALIDAÇÃO VIA BANCO DE DADOS) ---
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            return user
        
        # --- FUTURA LÓGICA DO ACTIVE DIRECTORY ---
        # No futuro, você substituiria o código acima por algo como:
        #
        # if ad_service.validate_credentials(username, password):
        #     user = User.query.filter_by(username=username).first()
        #     # Se o usuário não existir no banco local, você pode criá-lo aqui
        #     if not user:
        #         # Lógica para sincronizar/criar usuário do AD
        #         pass
        #     return user
        # 
        # return None
        # ---------------------------------------------------------

        return None