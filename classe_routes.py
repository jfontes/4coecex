# classe_routes.py
import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from extensions import db
from models import Classe
from forms import ClasseForm

# Crie um novo Blueprint para o CRUD de Classe
classe_bp = Blueprint('classe', __name__, url_prefix='/classes')

def obter_lista_modelos():
    """Lê a pasta /modelos e retorna uma lista de arquivos .docx."""
    caminho_modelos = os.path.join(current_app.root_path, 'modelos')
    try:
        # Lista apenas arquivos .docx e os ordena
        arquivos_docx = sorted([f for f in os.listdir(caminho_modelos) if f.lower().endswith('.docx')])
        # Formata para uso no SelectField: (valor, texto)
        opcoes = [('', 'Selecione um modelo...')] + [(arq, arq) for arq in arquivos_docx]
        return opcoes
    except FileNotFoundError:
        return [('', 'Pasta de modelos não encontrada')]

@classe_bp.route('/')
def listar():
    # ... (código existente)
    classes = Classe.query.order_by(Classe.nome).all()
    return render_template('classe_list.html', classes=classes)

@classe_bp.route('/nova', methods=['GET', 'POST'])
def nova():
    form = ClasseForm()
    # Popula o dropdown com os arquivos da pasta /modelos
    form.modelo_existente.choices = obter_lista_modelos()

    if form.validate_on_submit():
        nome_do_arquivo_final = None

        # PRIORIDADE 1: Novo upload de arquivo
        if form.novo_modelo.data:
            arquivo = form.novo_modelo.data
            nome_do_arquivo_final = secure_filename(arquivo.filename)
            caminho_salvar = os.path.join(current_app.root_path, 'modelos', nome_do_arquivo_final)
            arquivo.save(caminho_salvar)
        # PRIORIDADE 2: Modelo selecionado da lista
        elif form.modelo_existente.data:
            nome_do_arquivo_final = form.modelo_existente.data

        nova_classe = Classe(
            nome=form.nome.data,
            modelo_de_relatorio=nome_do_arquivo_final
        )
        db.session.add(nova_classe)
        db.session.commit()
        flash('Classe criada com sucesso!', 'success')
        return redirect(url_for('classe.listar'))
    
    return render_template('classe_form.html', form=form, titulo='Nova Classe', classe=None)

@classe_bp.route('/<int:classe_id>/editar', methods=['GET', 'POST'])
def editar(classe_id):
    classe = Classe.query.get_or_404(classe_id)
    form = ClasseForm(obj=classe)
    form.modelo_existente.choices = obter_lista_modelos()

    if form.validate_on_submit():
        form.populate_obj(classe)
        
        nome_do_arquivo_final = classe.modelo_de_relatorio # Mantém o valor antigo por padrão

        # PRIORIDADE 1: Novo upload de arquivo
        if form.novo_modelo.data:
            arquivo = form.novo_modelo.data
            nome_do_arquivo_final = secure_filename(arquivo.filename)
            caminho_salvar = os.path.join(current_app.root_path, 'modelos', nome_do_arquivo_final)
            arquivo.save(caminho_salvar)
        # PRIORIDADE 2: Modelo selecionado da lista (se for diferente de "Selecione...")
        elif form.modelo_existente.data:
            nome_do_arquivo_final = form.modelo_existente.data
        
        classe.modelo_de_relatorio = nome_do_arquivo_final
        db.session.commit()
        flash('Classe atualizada com sucesso!', 'success')
        return redirect(url_for('classe.listar'))

    # Pré-seleciona o valor do dropdown ao carregar a página de edição
    if classe.modelo_de_relatorio in [choice[0] for choice in form.modelo_existente.choices]:
        form.modelo_existente.data = classe.modelo_de_relatorio
        
    return render_template('classe_form.html', form=form, titulo=f'Editar Classe: {classe.nome}', classe=classe)

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