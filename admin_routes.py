from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User, Role, Permission, CargoEnum
from auth import AuthenticationManager
from forms import LoginForm, UserForm
from decorators import permission_required
import json

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        auth_manager = AuthenticationManager()
        user = auth_manager.login(form.username.data, form.password.data)
        if user:
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('main.index'))
        else:
            flash('Usuário ou senha inválidos.', 'danger')
            
    return render_template('login.html', form=form)

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin.login'))

# --- ROTAS DE GESTÃO DE PERMISSÕES ---
@admin_bp.route('/permissions')
@login_required
@permission_required('gerenciar_permissoes')
def permission_management():
    roles = Role.query.order_by(Role.id).all()
    permissions = Permission.query.order_by(Permission.name).all()
    return render_template('admin/permission_management.html', roles=roles, permissions=permissions)

@admin_bp.route('/permissions/save', methods=['POST'])
@login_required
@permission_required('gerenciar_permissoes')
def save_permissions():
    data = request.get_json()
    role_id = data.get('role_id')
    permission_id = data.get('permission_id')
    checked = data.get('checked')
    role = Role.query.get(role_id)
    permission = Permission.query.get(permission_id)
    if role and permission:
        if checked:
            if permission not in role.permissions:
                role.permissions.append(permission)
        else:
            if permission in role.permissions:
                role.permissions.remove(permission)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

# --- ROTAS DE GESTÃO DE UTILIZADORES (CRUD) ---
@admin_bp.route('/users')
@login_required
@permission_required('gerenciar_utilizadores')
def list_users():
    users = User.query.order_by(User.nome).all()
    return render_template('admin/user_list.html', users=users)

@admin_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@permission_required('gerenciar_utilizadores')
def create_user():
    form = UserForm()
    if form.validate_on_submit():
        new_user = User(
            username=form.username.data,
            nome=form.nome.data,
            cargo=CargoEnum[form.cargo.data],
            role_id=form.role.data
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash('Utilizador criado com sucesso!', 'success')
        return redirect(url_for('admin.list_users'))
    return render_template('admin/user_form.html', form=form, title='Novo Utilizador')

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('gerenciar_utilizadores')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user, original_username=user.username)

    if form.validate_on_submit():
        user.username = form.username.data
        user.nome = form.nome.data
        user.cargo = CargoEnum[form.cargo.data]
        user.role_id = form.role.data
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash('Utilizador atualizado com sucesso!', 'success')
        return redirect(url_for('admin.list_users'))

    # Pré-seleciona os valores dos dropdowns ao carregar a página
    form.cargo.data = user.cargo.name
    form.role.data = user.role_id
    
    return render_template('admin/user_form.html', form=form, title='Editar Utilizador')

@admin_bp.route('/users/<int:user_id>/delete', methods=['GET', 'POST'])
@login_required
@permission_required('gerenciar_utilizadores')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Você não pode excluir a sua própria conta.', 'danger')
        return redirect(url_for('admin.list_users'))
    if request.method == 'POST':
        db.session.delete(user)
        db.session.commit()
        flash('Utilizador excluído com sucesso.', 'success')
        return redirect(url_for('admin.list_users'))
    return render_template('admin/user_confirm_delete.html', user_to_delete=user)