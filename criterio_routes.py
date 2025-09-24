from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Analise
from forms import AnaliseForm

criterio_bp = Blueprint('criterio', __name__, url_prefix='/criterio')

# 2. Mova todas as rotas de 'Criterios' para cá, trocando @main_bp por @analysis_bp
@criterio_bp.route("/")
def listar():
    q = request.args.get("q", "", type=str).strip()
    query = Analise.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(Analise.nome.ilike(like), Analise.tag.ilike(like))
        )
    analises = query.order_by(Analise.id.desc()).all()
    # O template continua o mesmo
    return render_template("criterio_list.html", analises=analises, q=q)

@criterio_bp.route("/nova", methods=["GET", "POST"])
def nova():
    form = AnaliseForm()
    if form.validate_on_submit():
        obj = Analise(
            nome=form.nome.data.strip(),
            criterio=form.criterio.data.strip(),
            tag=form.tag.data.strip(),
            sugestao_documento=form.sugestao_documento.data.strip() if form.sugestao_documento.data else "Nenhuma sugestão.",
        )
        db.session.add(obj)
        db.session.commit()
        flash("Critério criado com sucesso!", "success")
        # O url_for agora aponta para '.listar' dentro deste mesmo blueprint
        return redirect(url_for(".listar"))
    return render_template("criterio_form.html", form=form, titulo="Novo critério")

@criterio_bp.route("/<int:analise_id>/editar", methods=["GET", "POST"])
def editar(analise_id):
    obj = Analise.query.get_or_404(analise_id)
    form = AnaliseForm(obj=obj)
    if form.validate_on_submit():
        form.populate_obj(obj)
        db.session.commit()
        flash("Critério atualizado com sucesso!", "success")
        return redirect(url_for(".listar"))
    return render_template("criterio_form.html", form=form, titulo=f"Editar critério #{obj.id}")

@criterio_bp.route("/<int:analise_id>/excluir", methods=["GET", "POST"])
def excluir(analise_id):
    obj = Analise.query.get_or_404(analise_id)
    if request.method == "POST":
        db.session.delete(obj)
        db.session.commit()
        flash("Critério excluído com sucesso!", "success")
        return redirect(url_for(".listar"))
    # O método GET mostra a página de confirmação
    return render_template("criterio_confirm_delete.html", obj=obj)