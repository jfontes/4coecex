from flask                  import Blueprint, session, render_template, request, jsonify, redirect, url_for, flash, send_file, current_app
from sqlalchemy.exc         import ProgrammingError, DataError
from extensions             import db
from tools                  import Tools
from models                 import Processo
from documento_word         import PreencheDocumentoWord
from ExportadorPDF          import ExportadorPDF
from forms                  import BuscaForm, ProcessoForm
from acreprevidencia_api    import DadosAcreprevidencia
from gemini                 import GeminiClient
from leitorPDF              import LeitorPDF
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
    
    session['dados'] = Tools.PreencherDados(proc)
    return render_template('edit.html', form=form, proc=proc)

@main_bp.get("/api/acreprev")
def api_acreprev():
    cpf = request.args.get("cpf", "").strip()
    if not cpf:
        return jsonify({"ok": False, "msg": "Informe o CPF."}), 400

    try:
        registro = DadosAcreprevidencia().getRegistroPorCPF(cpf)
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

        dados = session.get('dados', {}) 
        dados["sexo"] = registro.get("Sexo")
        dados["Idade"] = registro.get("Idade")
        dados["Data_nascimento"] = registro.get("Nascimento")
        dados["Data_ingresso_cargo"] = registro.get("Data_ingresso_cargo")
        dados["Data_ingresso_servico_publico"] = registro.get("Data_ingresso_servico_publico")
        session['dados'] = dados
        print(dados)

        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 400

@main_bp.route('/processo/<numero>/gerar-certidao')
def gerar_certidao(numero):
    proc = Processo.query.filter_by(processo=numero).first_or_404()
    session['dados'] = Tools.PreencherDados(proc)
    caminho_modelo = os.path.join(current_app.root_path, 'modelos', 'modelo_base.docx')    
    
    doc = PreencheDocumentoWord(caminho_modelo)
    doc.substituir_campos(session.get('dados', {}))

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
        session['dados'] = Tools.PreencherDados(proc)
        caminho_modelo = os.path.join(current_app.root_path, 'modelos', 'modelo_relatorio.docx')

        doc = PreencheDocumentoWord(caminho_modelo)
        doc.substituir_campos(session.get('dados', {}))
        docx_bytes = doc.gerar_bytes()
        
        result = mammoth.convert_to_html(io.BytesIO(docx_bytes))
        html_doc = result.value  # string HTML

        return render_template('analise_inatividade.html', proc=proc, doc_html=html_doc)
    except Exception as e:
        return f"Erro interno: {e}", 500

@main_bp.post('/processo/<numero>/analise/processar')
def processar_analise_inatividade(numero):
    files = request.files.getlist('pdfs[]')
    if not files:
        return jsonify({"ok": False, "msg": "Nenhum PDF enviado."}), 400

    leitor = LeitorPDF()
    try:
        texto = leitor.extrair_textos(files)
    except Exception as e:
        return f"Erro interno: {e}", 500
    
    prompt = """[PERSONA: Você é Auditor de Controle Externo do Tribunal de Contas do Estado do Acre (TCE-AC), especialista na análise de atos de inatividade (aposentadoria, reforma, reserva, pensão e etc). Fundamente suas avaliações na Constituição Federal, na Constituição Estadual, na legislação complementar aplicável (LCE nº 164/2006, LCE nº 197/2009, LCE nº 324/2016, LCE nº 349/2018, EC nº 103/2019) e em precedentes do STF e dos Tribunais de Contas.]
    [TONE: formal]
    [STYLE]
    Redija em linguagem técnica e objetiva. Cite de forma explícita dispositivos legais e jurisprudência (informando artigo, inciso, número de acórdão ou decisão). Estruture o relatório de acordo com o padrão do TCE-AC demonstrado no modelo fornecido.  
    [AUDIENCE: Procuradores e Juízes Conselheiros]
    [CONTEXT]
    Você recebeu para exame um processo de inatividade de militar, contendo os seguintes documentos o histórico funcional e, eventualmente, a certidão de contribuição previdenciária.
    Hipóteses especiais a verificar no caso concreto:  
    1. Quando o servidor foi admitido?
    2. Em qual cargo e órgão se deu a admissão?
    3. A admissão ocorreu com ou sem concurso público?
    4. Qual documento materializou a admissão?
    [OBJETIVO]
    Redigir parágrafo simples, formal e técnico, contendo uma análise sobre a admissão do servidor.
    [INSTRUCTIONS]
    Não acrescente texto nenhum além daquele previsto em SAÍDA.
    [SAÍDA]
    Produza um único parágrafo contendo uma análise com base no seguinte modelo:
    O (A) servidor(a) foi admitido(a) pela [órgão que admitiu o servidor], [com ou sem aprovação em concurso público], através de [documento de admissão do servidor, exemplo: contrato, carteira de trabalho e outros], para exercer o cargo de [cargo no qual o servidor foi admitido], na data de [data de admissão], conforme [documento analisado, por exemplo: relatório ou ficha de assentamento funcional]."""

    analise = str(GeminiClient().get(texto, prompt))
    dados = session.get('dados', {}) 
    dados["admissao"] = analise 
    session['dados'] = dados    
    
    return jsonify({"ok": True, "texto": analise})
    
@main_bp.post('/processo/adicionar_no_relatorio')
def adicionar_no_relatorio():
    try:
        dados = session.get('dados', {})
        admissao = request.form.get('admissao', '')
        dados["admissao"] = admissao
        
        caminho_modelo = os.path.join(current_app.root_path, 'modelos', 'modelo_relatorio.docx')
        doc = PreencheDocumentoWord(caminho_modelo)
        doc.substituir_campos(dados)
        docx_bytes = doc.gerar_bytes()
        
        result = mammoth.convert_to_html(io.BytesIO(docx_bytes))
        html_doc = result.value  # string HTML

        return jsonify({"ok": True, "doc_html": html_doc})
    except Exception as e:
        return jsonify({"ok": False, "msg": f"Erro interno: {e}"}), 500
    
@main_bp.get('/processo/<numero>/baixar-docx')
def baixar_docx(numero):
    try:
        dados = session.get('dados', {})
        caminho_modelo = os.path.join(current_app.root_path, 'modelos', 'modelo_relatorio.docx')
        doc = PreencheDocumentoWord(caminho_modelo)
        doc.substituir_campos(dados)
        docx_bytes = doc.gerar_bytes()
        return send_file(
            io.BytesIO(docx_bytes),
            as_attachment=True,
            download_name=f"relatorio_{numero}.docx",
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        flash(f"Erro ao gerar o arquivo: {e}", "danger")
        return redirect(url_for('main.analise_inatividade', numero=numero))