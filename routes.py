from flask                  import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_file, current_app
from sqlalchemy.exc         import ProgrammingError, DataError
from extensions             import db
from tools                  import Tools
from models                 import Processo
from documento_word         import PreencheDocumentoWord
from ExportadorPDF          import ExportadorPDF
from forms                  import BuscaForm, ProcessoForm
from acreprevidencia_api    import DadosAcreprevidencia
from gemini                 import GeminiClient
import io, tempfile, os, mammoth

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET','POST'])
def index():
    form = BuscaForm()
    if form.validate_on_submit():
        return redirect(url_for('main.editar', numero=form.numero.data))
    return render_template('search.html', form=form)

@main_bp.route('/processo/<numero>', methods=['GET','POST'])
def editar(numero):
    proc = Processo.query.filter_by(processo=numero).first()
    if not proc:
        flash("Processo não encontrado.", "danger")
        return redirect(url_for('main.index'))

    form = ProcessoForm(obj=proc)
    if form.validate_on_submit():
        form.populate_obj(proc)
        proc.data_inicio_concessao = proc.data_inicio_concessao or proc.data_publicacao
        proc.atualizado = 1
        try:
            db.session.commit()
            flash("Processo atualizado com sucesso!", "success")
        except (ProgrammingError, DataError):
            db.session.rollback()
            flash("Erro ao salvar. Verifique os dados informados.", "danger")
        return redirect(url_for('main.editar', numero=numero))

    return render_template('edit.html', form=form, proc=proc)

@main_bp.get("/api/acreprev")
def api_acreprev():
    cpf = request.args.get("cpf", "").strip()
    if not cpf:
        return jsonify({"ok": False, "msg": "Informe o CPF."}), 400

    try:
        registro = DadosAcreprevidencia().getRegistroPorCPF(cpf)
        print(registro)
        if not registro:
            return jsonify({"ok": False, "msg": "Nenhum registro encontrado para este CPF."}), 404

        # mapeia para os nomes dos campos do formulário
        data = {
            "servidor": registro.get("Nome") or "",
            "matricula": str(registro.get("Matricula")) + "-" + str(registro.get("Contrato")) or "",
            "orgao": registro.get("Orgao") or "",
            "proventos": registro.get("Proventos") or "",
            "data_concessao": registro.get("Data_concessao") or "",
            "cargo": str(GeminiClient().get(str(registro), "Cargo da pessoa (somente o nome, classe e referência, sem comentários).")) or "",
            "fundamento_legal": str(GeminiClient().get(str(registro), "Fundamento legal contendo todos os artigos e leis que fundamentam o registro. (Sem qualquer outro comentários)")) or "",
            "tempo_anos": registro.get("Tempo_Contribuicao_Ano") or "",
            "tempo_dias": registro.get("Tempo_Contribuicao_Dias") or "",
        }
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 400


@main_bp.route('/processo/<numero>/gerar-certidao')
def gerar_certidao(numero):
    proc = Processo.query.filter_by(processo=numero).first_or_404()
    dados = Tools.PreencherCertidao(proc)
    caminho_modelo = os.path.join(current_app.root_path, 'modelos', 'modelo_base.docx')    
    
    doc = PreencheDocumentoWord(caminho_modelo)
    doc.substituir_campos(dados)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(doc.gerar_bytes())
        tmp_path = tmp.name

    pdf_path = ExportadorPDF(caminho_modelo).gerar_pdf(tmp_path)

    # lê em memória, depois exclui arquivos temporários
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    os.remove(tmp_path)
    os.remove(pdf_path)

    return send_file(
        io.BytesIO(pdf_bytes),
        as_attachment=True,
        download_name=f"certidao_{numero}.pdf",
        mimetype="application/pdf"
    )

@main_bp.route('/processo/<numero>/analise')
def analise_inatividade(numero):
    try:
        proc = Processo.query.filter_by(processo=numero).first_or_404()
        dados = Tools.PreencherCertidao(proc)
        caminho_modelo = os.path.join(current_app.root_path, 'modelos', 'modelo_relatorio.docx')

        doc = PreencheDocumentoWord(caminho_modelo)
        doc.substituir_campos(dados)
        docx_bytes = doc.gerar_bytes()
        
        result = mammoth.convert_to_html(io.BytesIO(docx_bytes))
        html_doc = result.value  # string HTML

        return render_template('analise_inatividade.html',
                            proc=proc,
                            doc_html=html_doc)
    except Exception as e:
        return f"Erro interno: {e}", 500