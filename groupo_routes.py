# grupo_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Grupo, Criterio
from forms import GrupoForm
from flask_login import login_required
from decorators import permission_required

grupo_bp = Blueprint('grupo', __name__, url_prefix='/grupos')

@grupo_bp.route('/')
@login_required
@permission_required('acessar_cadastro_grupos')
def listar():
    """Mostra a lista de todos os grupos."""
    grupos = Grupo.query.order_by(Grupo.nome).all()
    return render_template('grupo_list.html', grupos=grupos)

@grupo_bp.route('/novo', methods=['GET', 'POST'])
@login_required
@permission_required('acessar_cadastro_grupos')
def novo():
    """Cria um novo grupo e suas associações."""
    form = GrupoForm()
    if form.validate_on_submit():
        # Cria a instância do novo grupo
        novo_grupo = Grupo(nome=form.nome.data)
        
        # Busca os objetos Criterio com base nos IDs selecionados no formulário
        criterios_selecionados = Criterio.query.filter(Criterio.id.in_(form.criterios.data)).all()
        
        # Associa os critérios ao novo grupo
        novo_grupo.criterios.extend(criterios_selecionados)
        
        db.session.add(novo_grupo)
        db.session.commit()
        flash('Grupo criado com sucesso!', 'success')
        return redirect(url_for('grupo.listar'))
        
    return render_template('grupo_form.html', form=form, titulo='Novo Grupo')

@grupo_bp.route('/<int:grupo_id>/editar', methods=['GET', 'POST'])
@login_required
@permission_required('acessar_cadastro_grupos')
def editar(grupo_id):
    """Edita um grupo existente."""
    grupo = Grupo.query.get_or_404(grupo_id)
    form = GrupoForm(obj=grupo)
    
    if form.validate_on_submit():
        # Atualiza o nome do grupo
        grupo.nome = form.nome.data
        
        # Limpa as associações existentes
        grupo.criterios.clear()
        
        # Adiciona as novas associações
        criterios_selecionados = Criterio.query.filter(Criterio.id.in_(form.criterios.data)).all()
        grupo.criterios.extend(criterios_selecionados)
        
        db.session.commit()
        flash('Grupo atualizado com sucesso!', 'success')
        return redirect(url_for('grupo.listar'))

    # Pré-seleciona os critérios atuais ao carregar a página
    form.criterios.data = [c.id for c in grupo.criterios]
    
    return render_template('grupo_form.html', form=form, titulo=f'Editar Grupo: {grupo.nome}')

@grupo_bp.route('/<int:grupo_id>/excluir', methods=['GET', 'POST'])
@login_required
@permission_required('acessar_cadastro_grupos')
def excluir(grupo_id):
    """Exclui um grupo."""
    grupo = Grupo.query.get_or_404(grupo_id)
    if request.method == 'POST':
        db.session.delete(grupo)
        db.session.commit()
        flash('Grupo excluído com sucesso!', 'success')
        return redirect(url_for('grupo.listar'))
    return render_template('grupo_confirm_delete.html', grupo=grupo)