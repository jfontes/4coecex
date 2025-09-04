from flask                  import Blueprint, session, render_template, request, jsonify, redirect, url_for, flash, send_file, current_app
from sqlalchemy.exc         import ProgrammingError, DataError
from extensions             import db
from tools                  import Tools
from models                 import Processo
from models                 import Analise
from documento_word         import PreencheDocumentoWord
from ExportadorPDF          import ExportadorPDF
from forms                  import BuscaForm, ProcessoForm, AnaliseForm
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

@main_bp.get("/analises")
def listar_analises():
    q = request.args.get("q", "", type=str).strip()
    query = Analise.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(Analise.nome.ilike(like), Analise.tag.ilike(like))
        )
    analises = query.order_by(Analise.id.desc()).all()
    return render_template("analise_list.html", analises=analises, q=q)

# CRIAR
@main_bp.route("/analises/nova", methods=["GET", "POST"])
def nova_analise():
    form = AnaliseForm()
    if form.validate_on_submit():
        obj = Analise(
            nome=form.nome.data.strip(),
            criterio=form.criterio.data.strip(),
            tag=form.tag.data.strip(),
        )
        db.session.add(obj)
        db.session.commit()
        flash("Análise criada com sucesso!", "success")
        return redirect(url_for("main.listar_analises"))
    return render_template("analise_form.html", form=form, titulo="Nova análise")

# EDITAR
@main_bp.route("/analises/<int:analise_id>/editar", methods=["GET", "POST"])
def editar_analise(analise_id):
    obj = Analise.query.get_or_404(analise_id)
    form = AnaliseForm(obj=obj)
    if form.validate_on_submit():
        form.populate_obj(obj)
        db.session.commit()
        flash("Análise atualizada com sucesso!", "success")
        return redirect(url_for("main.listar_analises"))
    return render_template("analise_form.html", form=form, titulo=f"Editar análise #{obj.id}")

# EXCLUIR (confirmação)
@main_bp.get("/analises/<int:analise_id>/excluir")
def excluir_analise_confirm(analise_id):
    obj = Analise.query.get_or_404(analise_id)
    return render_template("analise_confirm_delete.html", obj=obj)

@main_bp.post("/analises/<int:analise_id>/excluir")
def excluir_analise(analise_id):
    obj = Analise.query.get_or_404(analise_id)
    db.session.delete(obj)
    db.session.commit()
    flash("Análise excluída com sucesso!", "success")
    return redirect(url_for("main.listar_analises"))

@main_bp.route('/processo/novo', methods=['GET', 'POST'])
def novo_processo():
    form = ProcessoForm()

    # garanta que o Select de órgão previdência está populado (se não fizer isso no __init__ do form)
    try:
        from models import OrgaoPrevidencia
        form.orgao_previdencia.choices = [
            (op.id, op.nome) for op in OrgaoPrevidencia.query.order_by(OrgaoPrevidencia.nome)
        ]
    except Exception:
        pass

    if form.validate_on_submit():
        # valida número do processo obrigatoriamente na criação
        numero = (form.processo.data or '').strip()
        if not numero or len(numero) != 6 or not numero.isdigit():
            flash('Informe o Número do Processo com 6 dígitos (ex.: 123456).', 'danger')
            return render_template('edit.html', form=form, proc=None)

        # checa duplicidade
        existente = Processo.query.filter_by(processo=numero).first()
        if existente:
            flash('Já existe um processo com esse número.', 'danger')
            return render_template('edit.html', form=form, proc=None)

        # cria o objeto e popula
        proc = Processo()
        form.populate_obj(proc)

        # mapeia o select para a FK corretamente (se seu campo no model for *_id)
        try:
            proc.orgao_previdencia_id = form.orgao_previdencia.data or None
        except Exception:
            pass

        # garante que o número vai para o model (nome do campo no model é 'processo')
        proc.processo = numero

        db.session.add(proc)
        db.session.commit()
        flash('Processo criado com sucesso!', 'success')
        return redirect(url_for('main.editar', numero=proc.processo))

    # GET ou form com erros → renderiza usando o mesmo edit.html
    return render_template('edit.html', form=form, proc=None)

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
        dados["Observacoes"] = registro.get("Descricao") + registro.get("Fundamentacao")
        session['dados'] = dados
        print(dados)

        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 400

@main_bp.route('/processo/<numero>/gerar-certidao')
def gerar_certidao(numero):
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
    proc = Processo.query.filter_by(processo=numero).first()
    if not proc:
        flash("Processo não encontrado.", "danger")
        return redirect(url_for('main.index'))
    session['dados'] = Tools.PreencherDados(proc)
    
    try:
        analises = Analise.query.all()
        
        caminho_modelo = os.path.join(current_app.root_path, 'modelos', 'modelo_relatorio.docx')
        doc = PreencheDocumentoWord(caminho_modelo)
        doc.substituir_campos(session.get('dados', {}))
        docx_bytes = doc.gerar_bytes()
        
        result = mammoth.convert_to_html(io.BytesIO(docx_bytes))
        html_doc = result.value[result.value.find("RELATÓRIO CONCLUSIVO")-8:]  # string HTML

        return render_template('analise_inatividade.html', proc=numero, doc_html=html_doc, analises=analises)
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
    
    dados = session.get('dados', {}) 
    texto += f"\n\n{str(dados)}"

    analise_id = request.form.get('analise_id')
    analise = Analise.query.get(analise_id)

    prompt = analise.criterio

    analiseInteligente = str(GeminiClient().get(texto, prompt))
    dados[analise.tag] = analiseInteligente
    session['dados'] = dados    
    
    return jsonify({"ok": True, "texto": analiseInteligente})
    
@main_bp.post('/processo/adicionar_no_relatorio')
def adicionar_no_relatorio():
    try:
        dados = session.get('dados', {})
        analiseInteligente = request.form.get('analiseInteligente', '')
        analise_id = request.form.get('analise_id')
        analise = Analise.query.get(analise_id)

        dados[analise.tag] = analiseInteligente
        
        caminho_modelo = os.path.join(current_app.root_path, 'modelos', 'modelo_relatorio.docx')
        doc = PreencheDocumentoWord(caminho_modelo)
        doc.substituir_campos(dados)
        docx_bytes = doc.gerar_bytes()
        
        result = mammoth.convert_to_html(io.BytesIO(docx_bytes))
        html_doc = result.value[result.value.find("RELATÓRIO CONCLUSIVO")-8:]  # string HTML

        return jsonify({"ok": True, "doc_html": html_doc})
    except Exception as e:
        return jsonify({"ok": False, "msg": f"Erro interno: {e}"}), 500
    
@main_bp.get('/processo/<numero>/baixar')
def baixar(numero):
    tipo = request.args.get('tipo', 'word')
    print(f"Tipo solicitado: {tipo}")
    try:
        dados = session.get('dados', {})
        caminho_modelo = os.path.join(current_app.root_path, 'modelos', 'modelo_relatorio.docx')
        doc = PreencheDocumentoWord(caminho_modelo)
        doc.substituir_campos(dados)
        docx_bytes = doc.gerar_bytes()

        if tipo == 'pdf':
            print("Gerando PDF...")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                tmp.write(docx_bytes)
                tmp_path = tmp.name

            pdf_path = ExportadorPDF(caminho_modelo).gerar_pdf(tmp_path)
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
            os.remove(tmp_path)
            os.remove(pdf_path)

            print("PDF gerado e enviado.")
            return send_file(
                io.BytesIO(pdf_bytes),
                as_attachment=True,
                download_name=f"relatorio_{numero}.pdf",
                mimetype="application/pdf"
            )
        else:
            print("Gerando Word...")
            return send_file(
                io.BytesIO(docx_bytes),
                as_attachment=True,
                download_name=f"relatorio_{numero}.docx",
                mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
    except Exception as e:
        print(f"Erro ao gerar o arquivo: {e}")
        flash(f"Erro ao gerar o arquivo: {e}", "danger")
        return redirect(url_for('main.analise_inatividade', numero=numero))