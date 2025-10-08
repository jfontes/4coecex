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

        return None