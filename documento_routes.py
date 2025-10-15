import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory, abort, jsonify, session
from flask_login import login_required
from werkzeug.utils import secure_filename
from extensions import db
from models import Processo, Documento, TipoDocumento, Criterio
from forms import DocumentoForm

documento_bp = Blueprint('documento', __name__, url_prefix='/processo/<int:processo_id>/documentos')

@documento_bp.route('/', methods=['GET'])
@login_required
def gerenciar(processo_id):
    """Página para gerenciar documentos de um processo."""
    processo = Processo.query.get_or_404(processo_id)
    form = DocumentoForm()
    # Limpa a sessão de uploads temporários ao carregar a página
    session.pop(f'temp_uploads_{processo_id}', None)
    documentos = Documento.query.filter_by(processo_id=processo.id).order_by(Documento.id.desc()).all()
    tipos_documento = TipoDocumento.query.order_by(TipoDocumento.nome).all()
    return render_template('documentos_form.html', processo=processo, form=form, documentos=documentos, tipos_documento=tipos_documento)

@documento_bp.route('/upload-temporario', methods=['POST'])
@login_required
def upload_temporario(processo_id):
    processo = Processo.query.get_or_404(processo_id)
    files = request.files.getlist('arquivos')
    if not files or files[0].filename == '':
        return jsonify({'ok': False, 'msg': 'Nenhum arquivo selecionado.'}), 400

    temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp', str(processo.processo))
    os.makedirs(temp_dir, exist_ok=True)

    uploaded_files = []
    for file in files:
        filename = secure_filename(file.filename)
        temp_path = os.path.join(temp_dir, filename)
        file.save(temp_path)
        uploaded_files.append({'temp_path': temp_path, 'filename': filename})

    # Armazena na sessão
    session_key = f'temp_uploads_{processo_id}'
    temp_uploads = session.get(session_key, [])
    temp_uploads.extend(uploaded_files)
    session[session_key] = temp_uploads

    return jsonify({'ok': True, 'files': [{'filename': f['filename']} for f in uploaded_files]})

@documento_bp.route('/remover-temporario', methods=['POST'])
@login_required
def remover_temporario(processo_id):
    filename_to_remove = request.json.get('filename')
    if not filename_to_remove:
        return jsonify({'ok': False, 'msg': 'Nome do arquivo não fornecido.'}), 400

    session_key = f'temp_uploads_{processo_id}'
    temp_uploads = session.get(session_key, [])

    file_info = next((f for f in temp_uploads if f['filename'] == filename_to_remove), None)

    if file_info:
        # Remove o arquivo físico
        if os.path.exists(file_info['temp_path']):
            os.remove(file_info['temp_path'])
        
        # Remove da lista na sessão
        temp_uploads.remove(file_info)
        session[session_key] = temp_uploads
        return jsonify({'ok': True, 'msg': 'Arquivo removido da lista.'})
    
    return jsonify({'ok': False, 'msg': 'Arquivo não encontrado na sessão.'}), 404

@documento_bp.route('/salvar-documentos', methods=['POST'])
@login_required
def salvar_documentos(processo_id):
    processo = Processo.query.get_or_404(processo_id)
    documentos_para_salvar = request.json.get('documentos', [])
    if not documentos_para_salvar:
        return jsonify({'ok': False, 'msg': 'Nenhum documento para salvar.'}), 400

    session_key = f'temp_uploads_{processo_id}'
    temp_uploads = session.get(session_key, [])
    if not temp_uploads:
        return jsonify({'ok': False, 'msg': 'Sessão de upload expirada ou inválida.'}), 400

    final_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(processo.processo))
    os.makedirs(final_dir, exist_ok=True)

    try:
        for doc_data in documentos_para_salvar:
            filename = doc_data.get('filename')
            tipo_id = doc_data.get('tipo_id')

            # Encontra o arquivo na sessão e move
            temp_file_info = next((f for f in temp_uploads if f['filename'] == filename), None)
            if temp_file_info and os.path.exists(temp_file_info['temp_path']):
                final_path = os.path.join(final_dir, filename)
                os.rename(temp_file_info['temp_path'], final_path)

                novo_doc = Documento(nome_arquivo=filename, processo_id=processo_id, tipo_documento_id=tipo_id)
                db.session.add(novo_doc)

        db.session.commit()
        session.pop(session_key, None) # Limpa a sessão após o sucesso
        return jsonify({'ok': True, 'msg': f'{len(documentos_para_salvar)} documentos salvos com sucesso!'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao salvar documentos: {e}")
        return jsonify({'ok': False, 'msg': 'Ocorreu um erro interno ao salvar os arquivos.'}), 500

@documento_bp.route('/<int:documento_id>/atribuir-tipo', methods=['POST'])
@login_required
def atribuir_tipo(processo_id, documento_id):
    tipo_id = request.form.get('tipo_documento_id')
    if not tipo_id:
        flash('Selecione um tipo de documento.', 'danger')
        return redirect(url_for('.gerenciar', processo_id=processo_id))

    # Verifica se já existe um documento com este tipo no processo
    existe = Documento.query.filter_by(processo_id=processo_id, tipo_documento_id=tipo_id).first()
    if existe:
        flash(f'Já existe um documento do tipo selecionado neste processo. Não é permitido duplicidade.', 'danger')
    else:
        doc = Documento.query.get_or_404(documento_id)
        doc.tipo_documento_id = tipo_id
        db.session.commit()
        flash('Tipo de documento atribuído com sucesso!', 'success')
    
    return redirect(url_for('.gerenciar', processo_id=processo_id))

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
