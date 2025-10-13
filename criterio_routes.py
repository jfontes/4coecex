from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Criterio, TipoDocumento
from forms import CriterioForm
from flask_login import login_required
from decorators import permission_required

criterio_bp = Blueprint('criterio', __name__, url_prefix='/criterio')

# 2. Mova todas as rotas de 'Criterios' para cá, trocando @main_bp por @analysis_bp
@criterio_bp.route("/")
@login_required
@permission_required('acessar_cadastro_criterios')
def listar():
    q = request.args.get("q", "", type=str).strip()
    query = Criterio.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(Criterio.nome.ilike(like), Criterio.tag.ilike(like))
        )
    criterios = query.order_by(Criterio.id.desc()).all()
    # O template continua o mesmo
    return render_template("criterio_list.html", criterios=criterios, q=q)

@criterio_bp.route("/nova", methods=["GET", "POST"])
@login_required
@permission_required('acessar_cadastro_criterios')
def nova():
    form = CriterioForm()
    # Pré-seleciona os tipos de documento se o formulário for reenviado com erro
    if request.method == 'POST':
        form.tipos_documento.data = [int(x) for x in form.tipos_documento.data]

    if form.validate_on_submit():
        obj = Criterio()
        # Remove o campo de relacionamento para que o populate_obj não tente preenchê-lo
        del form.tipos_documento
        form.populate_obj(obj) # Popula nome, prompt, tag, ativo
        
        # Limpa e adiciona os tipos de documento selecionados
        obj.tipos_documento.clear()
        # Busca os dados diretamente da requisição, pois o campo foi removido do form
        documentos_selecionados = TipoDocumento.query.filter(TipoDocumento.id.in_(request.form.getlist('tipos_documento'))).all()
        obj.tipos_documento.extend(documentos_selecionados)
        db.session.add(obj)
        db.session.commit()
        flash("Critério criado com sucesso!", "success")
        # O url_for agora aponta para '.listar' dentro deste mesmo blueprint
        return redirect(url_for(".listar"))
    return render_template("criterio_form.html", form=form, titulo="Novo critério")

@criterio_bp.route("/<int:criterio_id>/editar", methods=["GET", "POST"])
@login_required
@permission_required('acessar_cadastro_criterios')
def editar(criterio_id):
    obj = Criterio.query.get_or_404(criterio_id)
    form = CriterioForm(obj=obj)

    if request.method == 'GET':
        # Pré-seleciona os tipos de documento associados ao critério
        form.tipos_documento.data = [td.id for td in obj.tipos_documento]

    if form.validate_on_submit():
        # Remove o campo de relacionamento para que o populate_obj não tente preenchê-lo
        del form.tipos_documento
        form.populate_obj(obj)

        # Limpa e atualiza os tipos de documento selecionados
        obj.tipos_documento.clear()
        # Busca os dados diretamente da requisição, pois o campo foi removido do form
        documentos_selecionados = TipoDocumento.query.filter(TipoDocumento.id.in_(request.form.getlist('tipos_documento'))).all()
        obj.tipos_documento.extend(documentos_selecionados)
        db.session.commit()
        flash("Critério atualizado com sucesso!", "success")
        return redirect(url_for(".listar"))
    return render_template("criterio_form.html", form=form, titulo=f"Editar critério #{obj.id}")

@criterio_bp.route("/<int:criterio_id>/excluir", methods=["GET", "POST"])
@login_required
@permission_required('acessar_cadastro_criterios')
def excluir(criterio_id):
    obj = Criterio.query.get_or_404(criterio_id)
    if request.method == "POST":
        db.session.delete(obj)
        db.session.commit()
        flash("Critério excluído com sucesso!", "success")
        return redirect(url_for(".listar"))
    # O método GET mostra a página de confirmação
    return render_template("criterio_confirm_delete.html", obj=obj)