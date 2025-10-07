from functools import wraps
from flask_login import current_user
from flask import abort

def permission_required(permission_name):
    """
    Verifica se o usuário logado tem a permissão necessária.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                # Se o usuário não estiver logado, o Flask-Login já redireciona
                # para a página de login.
                abort(401)
            
            # O Administrador tem acesso a tudo
            if current_user.role.name == 'Administrador':
                return f(*args, **kwargs)
            
            # Verifica se o perfil do usuário tem a permissão
            if not current_user.role.has_permission(permission_name):
                # Acesso negado
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
