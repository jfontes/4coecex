import click
from flask.cli import with_appcontext
from extensions import db
from models import User, Role, Permission

@click.command(name='init-db')
@with_appcontext
def init_db_command():
    """Inicializa a base de dados com perfis e permissões padrão."""
    
    print("A iniciar a inicialização da base de dados...")

    # --- PERMISSÕES ---
    # Mapeie aqui todas as permissões do seu sistema.
    # O 'name' é usado no decorador @permission_required, a 'description' é para a tela de admin.
    permissions_list = [
        # Processos
        {'name': 'acessar_processos', 'description': 'Aceder à edição de processos'},
        {'name': 'criar_processos', 'description': 'Criar novos processos'},
        {'name': 'analisar_processos', 'description': 'Aceder à tela de análise de inatividade'},
        
        # Cadastros
        {'name': 'acessar_cadastro_criterios', 'description': 'Aceder ao cadastro de Critérios'},
        {'name': 'acessar_cadastro_classes', 'description': 'Aceder ao cadastro de Classes'},
        {'name': 'acessar_cadastro_grupos', 'description': 'Aceder ao cadastro de Grupos'},
        
        # Administração
        {'name': 'gerenciar_permissoes', 'description': 'Aceder à tela de gestão de permissões (apenas Admin)'}
    ]
    
    for p_data in permissions_list:
        p = Permission.query.filter_by(name=p_data['name']).first()
        if not p:
            p = Permission(name=p_data['name'], description=p_data['description'])
            db.session.add(p)
            print(f"Permissão '{p.name}' criada.")

    # --- PERFIS (ROLES) ---
    roles_list = ['Administrador', 'Auditor-chefe', 'Auditor']
    for role_name in roles_list:
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name)
            db.session.add(role)
            print(f"Perfil '{role.name}' criado.")
            
    db.session.commit()

    # --- UTILIZADOR ADMINISTRADOR PADRÃO ---
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_role = Role.query.filter_by(name='Administrador').first()
        admin_user = User(username='admin', role=admin_role)
        # DEFINA AQUI UMA SENHA PADRÃO FORTE
        admin_user.set_password('change-this-password')
        db.session.add(admin_user)
        print("Utilizador 'admin' criado com a senha padrão. Altere-a imediatamente!")

    db.session.commit()
    print("Inicialização da base de dados concluída.")

def register_commands(app):
    app.cli.add_command(init_db_command)
