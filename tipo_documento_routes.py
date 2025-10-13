from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import TipoDocumento, Criterio
from forms import TipoDocumentoForm
from flask_login import login_required
from decorators import permission_required

tipo_documento_bp = Blueprint('tipo_documento', __name__, url_prefix='/tipo_documento')

@tipo_documento_bp.route("/", methods=["GET", "POST"])
@login_required
@permission_required('gerenciar_tipos_documento')
def listar():
    form = TipoDocumentoForm()
    if form.validate_on_submit():
        # Lógica para criar um novo tipo de documento
        novo_tipo = TipoDocumento(nome=form.nome.data.strip())
        db.session.add(novo_tipo)
        db.session.commit()
        flash("Tipo de documento criado com sucesso!", "success")
        return redirect(url_for(".listar"))

    tipos = TipoDocumento.query.order_by(TipoDocumento.nome).all()
    return render_template("tipo_documento_management.html", tipos=tipos, form=form, obj_edit=None)

@tipo_documento_bp.route("/<int:obj_id>/editar", methods=["GET", "POST"])
@login_required
@permission_required('gerenciar_tipos_documento')
def editar(obj_id):
    obj = TipoDocumento.query.get_or_404(obj_id)
    form = TipoDocumentoForm(obj=obj) # Formulário para edição

    if form.validate_on_submit():
        form.populate_obj(obj)
        db.session.commit()
        flash("Tipo de documento atualizado com sucesso!", "success")
        return redirect(url_for(".listar"))

    # Se for GET ou o formulário de edição tiver erros, renderiza a página principal
    # passando o objeto a ser editado e a lista completa.
    tipos = TipoDocumento.query.order_by(TipoDocumento.nome).all()
    return render_template("tipo_documento_management.html", tipos=tipos, form=form, obj_edit=obj)

@tipo_documento_bp.route("/<int:obj_id>/excluir", methods=["GET", "POST"])
@login_required
@permission_required('gerenciar_tipos_documento')
def excluir(obj_id):
    obj = TipoDocumento.query.get_or_404(obj_id)
    # Verifica se o tipo de documento está em uso por algum critério
    criterio_associado = Criterio.query.filter(Criterio.tipos_documento.any(id=obj_id)).first()

    if request.method == "POST":
        if criterio_associado:
            flash("Este tipo de documento não pode ser excluído pois está associado a um ou mais critérios.", "danger")
            return redirect(url_for(".listar"))
        db.session.delete(obj)
        db.session.commit()
        flash("Tipo de documento excluído com sucesso!", "success")
        return redirect(url_for(".listar"))
    return render_template("tipo_documento_confirm_delete.html", obj=obj, criterio_associado=criterio_associado)