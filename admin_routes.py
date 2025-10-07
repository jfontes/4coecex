from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User, Role, Permission
from auth import AuthenticationManager
from forms import LoginForm # Supondo que você criará este formulário
from decorators import permission_required

admin_bp = Blueprint('admin', __name__)
auth_manager = AuthenticationManager()

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = auth_manager.login(form.username.data, form.password.data)
        if user:
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('main.index'))
        else:
            flash('Login inválido. Verifique seu usuário e senha.', 'danger')
            
    return render_template('login.html', form=form)

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin.login'))

@admin_bp.route('/admin/permissions', methods=['GET', 'POST'])
@login_required
@permission_required('gerenciar_permissoes') # Apenas quem tem essa permissão pode acessar
def manage_permissions():
    # Garante que apenas o Administrador acesse esta página específica
    if current_user.role.name != 'Administrador':
        abort(403)

    if request.method == 'POST':
        # Pega todos os dados do formulário
        permissions_data = request.form.to_dict()
        roles = Role.query.filter(Role.name != 'Administrador').all()
        
        for role in roles:
            # Limpa as permissões antigas
            role.permissions.clear()
            # Pega as permissões selecionadas para este perfil
            selected_permissions_ids = request.form.getlist(f'role_{role.id}')
            if selected_permissions_ids:
                permissions = Permission.query.filter(Permission.id.in_(selected_permissions_ids)).all()
                role.permissions.extend(permissions)
        
        db.session.commit()
        flash('Permissões atualizadas com sucesso!', 'success')
        return redirect(url_for('admin.manage_permissions'))

    roles = Role.query.filter(Role.name != 'Administrador').order_by(Role.name).all()
    permissions = Permission.query.order_by(Permission.description).all()
    
    return render_template('admin/permission_management.html', roles=roles, permissions=permissions)
