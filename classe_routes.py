# classe_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Classe
from forms import ClasseForm

# Crie um novo Blueprint para o CRUD de Classe
classe_bp = Blueprint('classe', __name__, url_prefix='/classes')

@classe_bp.route('/')
def listar():
    """Mostra a lista de todas as classes, com filtro."""
    # Pega o termo de busca da URL, se existir
    q = request.args.get("q", "", type=str).strip()
    
    # Inicia a query base
    query = Classe.query

    # Se houver um termo de busca, aplica o filtro
    if q:
        like_query = f"%{q}%"
        # Busca no nome da classe ou no nome do arquivo de modelo
        query = query.filter(
            db.or_(
                Classe.nome.ilike(like_query),
                Classe.modelo_de_relatorio.ilike(like_query)
            )
        )
    
    # Ordena os resultados e executa a query
    classes = query.order_by(Classe.nome).all()
    
    # Passa o termo de busca (q) para o template
    return render_template('classe_list.html', classes=classes, q=q)

@classe_bp.route('/nova', methods=['GET', 'POST'])
def nova():
    """Cria uma nova classe."""
    form = ClasseForm()
    if form.validate_on_submit():
        nova_classe = Classe(
            nome=form.nome.data,
            modelo_de_relatorio=form.modelo_de_relatorio.data or None
        )
        db.session.add(nova_classe)
        db.session.commit()
        flash('Classe criada com sucesso!', 'success')
        return redirect(url_for('classe.listar'))
    return render_template('classe_form.html', form=form, titulo='Nova Classe')

@classe_bp.route('/<int:classe_id>/editar', methods=['GET', 'POST'])
def editar(classe_id):
    """Edita uma classe existente."""
    classe = Classe.query.get_or_404(classe_id)
    form = ClasseForm(obj=classe)
    if form.validate_on_submit():
        form.populate_obj(classe)
        db.session.commit()
        flash('Classe atualizada com sucesso!', 'success')
        return redirect(url_for('classe.listar'))
    return render_template('classe_form.html', form=form, titulo=f'Editar Classe: {classe.nome}')

@classe_bp.route('/<int:classe_id>/excluir', methods=['GET', 'POST'])
def excluir(classe_id):
    """Exclui uma classe."""
    classe = Classe.query.get_or_404(classe_id)
    if request.method == 'POST':
        db.session.delete(classe)
        db.session.commit()
        flash('Classe excluída com sucesso!', 'success')
        return redirect(url_for('classe.listar'))
    # Método GET mostra a confirmação
    return render_template('classe_confirm_delete.html', classe=classe)