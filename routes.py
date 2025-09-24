from flask                  import Blueprint, session, render_template, request, jsonify, redirect, url_for, flash, send_file, current_app, abort
from sqlalchemy.exc         import ProgrammingError, DataError
from extensions             import db
from tools                  import Tools
from models                 import Processo, Criterio
from documento_word         import PreencheDocumentoWord
from ExportadorPDF          import ExportadorPDF
from forms                  import BuscaForm, ProcessoForm
from acreprevidencia_api    import DadosAcreprevidencia, AcrePrevAPIError 
from gemini                 import Gemini
from google.genai           import types
import io, tempfile, os, mammoth, json

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET','POST'])
def index():
    form = BuscaForm()
    if form.validate_on_submit():
        return redirect(url_for('main.editar', numero=form.numero.data))
    return render_template('search.html', form=form)

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
        proc = Processo.query.filter_by(cpf=Tools.FormatarCPF(cpf)).first()

        if not proc.dados_previdencia:
            # Busca o registro na API
            registro = DadosAcreprevidencia().getRegistroPorCPF(cpf)
            if not registro:
                return jsonify({"ok": False, "msg": "Nenhum registro encontrado para este CPF."}), 404
            
            proc.dados_previdencia = registro
            db.session.commit()
        else:
            registro = proc.dados_previdencia

        # Continua o processo de extrair dados para o formulário
        cargo_fundamento = Gemini().extrairCargoFundamentoLegal(str(registro))
        data = {
            "servidor": registro.get("Nome") or "",
            "matricula": str(registro.get("Matricula")) + "-" + str(registro.get("Contrato")) or "",
            "orgao": registro.get("Orgao") or "",
            "proventos": registro.get("Proventos") or "",
            "data_concessao": registro.get("Data_concessao") or "",
            "cargo": cargo_fundamento[0],
            "fundamento_legal": cargo_fundamento[1],
            "tempo_anos": registro.get("Tempo_Contribuicao_Ano") or "",
            "tempo_dias": registro.get("Tempo_Contribuicao_Dias") or "",
        }
        
        # Atualiza a sessão também, para manter consistência
        dados = session.get('dados', {}) 
        dados.update({
            "Sexo": registro.get("Sexo"),
            "Idade": registro.get("Idade"),
            "Data_nascimento": registro.get("Nascimento"),
            "Data_ingresso_cargo": registro.get("Data_ingresso_cargo"),
            "Data_ingresso_servico_publico": registro.get("Data_ingresso_servico_publico"),
            "Observacoes": registro.get("Descricao", "") + registro.get("Fundamentacao", "")
        })
        session['dados'] = dados

        return jsonify({"ok": True, "data": data})
    except AcrePrevAPIError as e:
        return jsonify({"erro": False, "msg": "O serviço da Acreprevidência está indisponível. Tente novamente mais tarde."}), 503
    except Exception as e:
        return jsonify({"erro": False, "msg": str(e)}), 400

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
    proc = Processo.query.filter_by(processo=numero).first_or_404()
    session['analises'] = [] #Variável de sessão para armazenar as análises do usuário

    # 1. Preenche os dados básicos da sessão a partir do banco
    session['dados'] = Tools.PreencherDados(proc)
    
    # 2. Verifica se os dados da previdência já estão no banco
    dados_prev = proc.dados_previdencia
    if not dados_prev:
        # Se não estiverem, busca na API e salva no banco
        try:
            if not dados_prev:
                current_app.logger.info(f"Buscando dados da previdência para o CPF: {proc.cpf}")
                dados_prev = DadosAcreprevidencia().getRegistroPorCPF(proc.cpf)
                if dados_prev:
                    proc.dados_previdencia = dados_prev
                    db.session.commit()
        except AcrePrevAPIError:
            flash("Não foi possível conectar ao serviço da Acreprevidência. Alguns dados podem não estar disponíveis.", "warning")
            dados_prev = None # Garante que o código continue sem os dados da previdência

    # 3. Se houver dados da previdência (do banco ou da API), complementa a sessão
    if dados_prev:
        dados_sessao = session.get('dados', {})
        dados_sessao.update({
            "Sexo": dados_prev.get("Sexo"),
            "Idade": dados_prev.get("Idade"),
            "Data_nascimento": dados_prev.get("Nascimento"),
            "Data_ingresso_cargo": dados_prev.get("Data_ingresso_cargo"),
            "Data_ingresso_servico_publico": dados_prev.get("Data_ingresso_servico_publico"),
            "Observacoes": dados_prev.get("Descricao", "") + dados_prev.get("Fundamentacao", "")
        })
        session['dados'] = dados_sessao
    
    try:
        criterios = Criterio.query.filter_by(ativo=True).order_by(Criterio.nome.asc()).all()
        
        caminho_modelo = os.path.join(current_app.root_path, 'modelos', 'modelo_relatorio.docx')
        doc = PreencheDocumentoWord(caminho_modelo)
        doc.substituir_campos(session.get('dados', {}))
        docx_bytes = doc.gerar_bytes()
        
        result = mammoth.convert_to_html(io.BytesIO(docx_bytes))
        html_doc = result.value[result.value.find("1. INTRODUÇÃO")-8:]

        return render_template('analise_inatividade.html', proc=numero, doc_html=html_doc, criterios=criterios)
    except Exception as e:
        current_app.logger.error(f"ERRO em analise_atividade: {e}")
        abort(500)

@main_bp.post('/processo/<numero>/analise/processar')
def processar_analise_inatividade(numero):
    files = request.files.getlist('pdfs[]')
    if not files:
        return jsonify({"ok": False, "msg": "Nenhum PDF enviado."}), 400

    dados = session.get('dados', {}) 
    criterio_id = request.form.get('criterio_id')
    contexto = request.form.get('contexto', '').strip()
    try:
        criterio = Criterio.query.get(criterio_id)
        parts = Gemini().lerPDF(files)
        if contexto:
            parts.insert(0, types.Part(text=f"[OVERRIDE: Leve em consideração o seguinte contexto fornecido pelo usuário: '{contexto}'. IGNORE QUALQUER VALOR ANTERIOR.]"))
        
        parts.append(types.Part(text=json.dumps(dados, indent=2, ensure_ascii=False)))
        ai = Gemini().getAnaliseEstruturada(parts, criterio.prompt)
        analiseInteligente = ai.get("Analise")
    except Exception as e:
        current_app.logger.error(f"Erro ao processar análise inteligente: {e}")
        return jsonify({"erro": False, "msg": "Erro ao gerar resposta inteligente."}), 500
    
    if len(ai) > 1: #SE HOUVER METADADOS
        #PRECISA CONSTRUIR UMA LÓGICA DE IDENTIFICAR O TIPO DE METADADO E DAR O TRATAMENTO ADEQUADO
        #ATUALMENTE TRATA APENAS DOIS METADADOS, UM PARA CARGO E OUTRO PARA PROVENTOS, MAS DEPENDENDO DO PROMPT PODE RETORNAR OUTRAS INFORMAÇÕES
        if ai.get("Metadado1") == "SIM":
            dados["cargo"] = ai.get("Metadado2")
            dados["proventos"] = ai.get("Metadado3")

    dados[criterio.tag] = analiseInteligente
    session['dados'] = dados    
    
    return jsonify({"ok": True, "texto": analiseInteligente})
    
@main_bp.post('/processo/<numero>/adicionar_no_relatorio')
def adicionar_no_relatorio(numero):
    try:
        dados = session.get('dados', {})
        analiseInteligente = request.form.get('analiseInteligente', '')
        criterio_id = request.form.get('criterio_id')
        criterio = Criterio.query.get(criterio_id)

        dados[criterio.tag] = f"{analiseInteligente}"
        session['dados'] = dados
        
        caminho_modelo = os.path.join(current_app.root_path, 'modelos', 'modelo_relatorio.docx')
        doc = PreencheDocumentoWord(caminho_modelo)
        doc.substituir_campos(dados)
        docx_bytes = doc.gerar_bytes()
        
        result = mammoth.convert_to_html(io.BytesIO(docx_bytes))
        html_doc = result.value[result.value.find("1. INTRODUÇÃO")-8:]  # string HTML

        #Adiciona a análise à lista da sessão
        session['analises'].append({"criterio": criterio.id, "nome": criterio.nome, "processo": numero, "analise": analiseInteligente})

        return jsonify({"ok": True, "doc_html": html_doc})
    except Exception as e:
        #return jsonify({"ok": False, "msg": f"Erro interno: {e}"}), 500
        current_app.logger.error(f"Erro ao adicionar no relatório: {e}")
        abort(500)
    
@main_bp.get('/processo/<numero>/salvar')
def salvarAnalises(numero):
    current_app.logger.debug(f"Salvando análises no banco de dados.")
    try:
        print(session.get('analises'))
    except Exception as e:
        current_app.logger.error(f"Erro ao salvar análises: {e}")
        flash(f"Erro ao salvar análises", "danger")
    return redirect(url_for('main.analise_inatividade', numero=numero))


@main_bp.get('/processo/<numero>/baixar')
def baixar(numero):
    tipo = request.args.get('tipo', 'word')
    current_app.logger.debug(f"Solicitação de download para o processo {numero} no formato: {tipo}")
    try:
        dados = session.get('dados', {})
        caminho_modelo = os.path.join(current_app.root_path, 'modelos', 'modelo_relatorio.docx')
        doc = PreencheDocumentoWord(caminho_modelo)
        doc.substituir_campos(dados)
        docx_bytes = doc.gerar_bytes()

        if tipo == 'pdf':
            current_app.logger.info(f"Gerando PDF para o processo {numero}.")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                tmp.write(docx_bytes)
                tmp_path = tmp.name

            pdf_path = ExportadorPDF(caminho_modelo).gerar_pdf(tmp_path)
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
            os.remove(tmp_path)
            os.remove(pdf_path)

            current_app.logger.info("PDF gerado e enviado.")
            return send_file(
                io.BytesIO(pdf_bytes),
                as_attachment=True,
                download_name=f"relatorio_{numero}.pdf",
                mimetype="application/pdf"
            )
        else:
            current_app.logger.info(f"Gerando Word para o processo {numero}.")
            return send_file(
                io.BytesIO(docx_bytes),
                as_attachment=True,
                download_name=f"relatorio_{numero}.docx",
                mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
    except Exception as e:
        current_app.logger.error(f"Erro em routes.py. Ocorreu uma falha ao gerar arquivo para o processo {numero}: {e}")
        flash(f"Erro ao gerar o arquivo: {e}", "danger")
        return redirect(url_for('main.analise_inatividade', numero=numero))