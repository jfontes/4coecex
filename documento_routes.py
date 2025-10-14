import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory, abort
from flask_login import login_required
from werkzeug.utils import secure_filename
from extensions import db
from models import Processo, Documento, TipoDocumento
from forms import DocumentoForm

documento_bp = Blueprint('documento', __name__, url_prefix='/processo/<int:processo_id>/documentos')

@documento_bp.route('/', methods=['GET', 'POST'])
@login_required
def gerenciar(processo_id):
    """Página para ver e adicionar novos documentos a um processo."""
    processo = Processo.query.get_or_404(processo_id)
    form = DocumentoForm()
    
    if form.validate_on_submit():
        arquivo = form.arquivo_pdf.data
        if arquivo:
            filename = secure_filename(arquivo.filename)
            
            # Cria um subdiretório para o processo, se não existir
            caminho_upload = os.path.join(current_app.config['UPLOAD_FOLDER'], str(processo.processo))
            os.makedirs(caminho_upload, exist_ok=True)
            
            caminho_final = os.path.join(caminho_upload, filename)
            arquivo.save(caminho_final)

            novo_documento = Documento(
                nome_arquivo=filename,
                processo_id=processo.id,
                tipo_documento_id=form.tipo_documento.data
            )
            db.session.add(novo_documento)
            db.session.commit()
            flash('Documento enviado com sucesso!', 'success')
            return redirect(url_for('documento.gerenciar', processo_id=processo.id))

    documentos = Documento.query.filter_by(processo_id=processo.id).order_by(Documento.id.desc()).all()
    return render_template('documentos_form.html', processo=processo, form=form, documentos=documentos)

@documento_bp.route('/<int:documento_id>/excluir', methods=['POST'])
@login_required
def excluir(processo_id, documento_id):
    """Exclui um documento do processo."""
    documento = Documento.query.get_or_404(documento_id)
    
    if documento.processo_id != processo_id:
        abort(403)
        
    try:
        caminho_arquivo = os.path.join(current_app.config['UPLOAD_FOLDER'], str(documento.processo.processo), documento.nome_arquivo)
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)
        
        db.session.delete(documento)
        db.session.commit()
        flash('Documento excluído com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir o documento: {e}', 'danger')
        
    return redirect(url_for('documento.gerenciar', processo_id=processo_id))

@documento_bp.route('/<int:documento_id>/ver')
@login_required
def ver(processo_id, documento_id):
    """Permite visualizar o PDF no navegador."""
    documento = Documento.query.get_or_404(documento_id)
    if documento.processo_id != processo_id:
        abort(403)
    
    directory = os.path.join(current_app.config['UPLOAD_FOLDER'], str(documento.processo.processo))
    return send_from_directory(directory, documento.nome_arquivo, as_attachment=False)

