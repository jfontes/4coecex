from flask                  import Blueprint, session, render_template, request, jsonify, redirect, url_for, flash, send_file, current_app, abort
from sqlalchemy.exc         import ProgrammingError, DataError
from extensions             import db
from tools                  import Tools
from models                 import Processo, Criterio, Grupo
from documento_word         import PreencheDocumentoWord
from ExportadorPDF          import ExportadorPDF
from forms                  import BuscaForm, ProcessoForm
from acreprevidencia_api    import DadosAcreprevidencia, AcrePrevAPIError 
from ia_handler             import GenerativeAI
#from google    import Gemini
from google.genai           import types
import io, tempfile, os, mammoth, json
from flask_login            import login_required
from decorators             import permission_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET','POST'])
@login_required
def index():
    form = BuscaForm()
    if form.validate_on_submit():
        return redirect(url_for('main.editar', numero=form.numero.data))
    return render_template('search.html', form=form)

@main_bp.route('/processo/novo', methods=['GET', 'POST'])
@login_required
@permission_required('criar_processos')
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
@login_required
@permission_required('acessar_processos')
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
@login_required
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
@login_required
@permission_required('analisar_processos')
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
@login_required
@permission_required('analisar_processos')
def analise_inatividade(numero):
    proc = Processo.query.filter_by(processo=numero).first_or_404()

    # 1. Preenche os dados básicos da sessão a partir do banco
    session['analises'] = []
    
    session['dados'] = Tools.PreencherDados(proc)
    
    if proc.analises:
        session['dados'].update(proc.analises)
        analises_salvas = [{'tag': tag, 'texto': texto} for tag, texto in proc.analises.items()]
        session['analises'] = analises_salvas
    
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
        grupos = Grupo.query.order_by(Grupo.nome.asc()).all()
        criterios = []
        
        caminho_modelo = os.path.join(current_app.root_path, 'modelos', proc.classe.modelo_de_relatorio or 'modelo_relatorio.docx')
        doc = PreencheDocumentoWord(caminho_modelo)
        doc.substituir_campos(session.get('dados', {}))
        docx_bytes = doc.gerar_bytes()
        
        result = mammoth.convert_to_html(io.BytesIO(docx_bytes))
        html_doc = result.value[result.value.find("1. INTRODUÇÃO")-8:]

        return render_template('analise_inatividade.html', proc=numero, doc_html=html_doc, grupos=grupos, criterios=criterios)
    except Exception as e:
        current_app.logger.error(f"ERRO em analise_atividade: {e}")
        abort(500)

@main_bp.route('/api/grupo/<int:grupo_id>/criterios')
@login_required
def api_criterios_por_grupo(grupo_id):
    """Retorna uma lista de critérios (apenas os ativos) para um grupo específico."""
    grupo = Grupo.query.get_or_404(grupo_id)
    
    # Filtra os critérios para pegar apenas os que estão ativos
    criterios_ativos = [c for c in grupo.criterios if c.ativo]
    
    # Monta a lista de resultados em um formato que o JavaScript entende
    resultado = [
        {
            "id": criterio.id,
            "nome": criterio.nome,
            "sugestao_documento": criterio.sugestao_documento
        } 
        for criterio in criterios_ativos
    ]
    
    return jsonify(resultado)

@main_bp.post('/processo/<numero>/analise/processar')
@login_required
@permission_required('analisar_processos')
def processar_analise_inatividade(numero):
    files = request.files.getlist('pdfs[]')
    if not files:
        return jsonify({"ok": False, "msg": "Nenhum PDF enviado."}), 400

    dados = session.get('dados', {}) 
    criterio_id = request.form.get('criterio_id')
    contexto = request.form.get('contexto', '').strip()
    try:
        criterio = Criterio.query.get(criterio_id)
        parts = GenerativeAI.lerPDF(files)
        if contexto:
            parts.insert(0, types.Part(text=f"[OVERRIDE: Leve em consideração o seguinte contexto fornecido pelo usuário: '{contexto}'. IGNORE QUALQUER VALOR ANTERIOR.]"))
        
        parts.append(types.Part(text=json.dumps(dados, indent=2, ensure_ascii=False)))
        ai = GenerativeAI().get_structured_analysis(parts, criterio.prompt)
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
@login_required
@permission_required('analisar_processos')
def adicionar_no_relatorio(numero):
    try:
        proc = Processo.query.filter_by(processo=numero).first_or_404()

        dados = session.get('dados', {})
        analiseInteligente = request.form.get('analiseInteligente', '')
        print(analiseInteligente)
        criterio_id = request.form.get('criterio_id')
        criterio = Criterio.query.get(criterio_id)

        dados[criterio.tag] = f"{analiseInteligente}"
        session['dados'] = dados
        
        # 3. ACUMULA a análise na lista temporária 'analises'
        analises_temp = session.get('analises', [])
        encontrado = False
        for analise in analises_temp:
            if analise['tag'] == criterio.tag:
                analise['texto'] = analiseInteligente # Atualiza o texto
                encontrado = True
                break
        
        if not encontrado:
            analises_temp.append({
                'tag': criterio.tag,
                'texto': analiseInteligente
            })
        session['analises'] = analises_temp

        caminho_modelo = os.path.join(current_app.root_path, 'modelos', proc.classe.modelo_de_relatorio or 'modelo_relatorio.docx')
        doc = PreencheDocumentoWord(caminho_modelo)
        doc.substituir_campos(dados)
        docx_bytes = doc.gerar_bytes()
        
        result = mammoth.convert_to_html(io.BytesIO(docx_bytes))
        html_doc = result.value[result.value.find("1. INTRODUÇÃO")-8:]  # string HTML

        return jsonify({"ok": True, "doc_html": html_doc})
    except Exception as e:
        #return jsonify({"ok": False, "msg": f"Erro interno: {e}"}), 500
        current_app.logger.error(f"Erro ao adicionar no relatório: {e}")
        abort(500)
    
@main_bp.get('/processo/<numero>/salvar')
@login_required
@permission_required('analisar_processos')
def salvarAnalises(numero):
    current_app.logger.debug(f"Salvando análises no banco de dados.")
    try:
        proc = Processo.query.filter_by(processo=numero).first_or_404()
        
        # Pega a lista de análises da sessão
        analises = session.get('analises', [])

        if not analises:
            return jsonify({"warning": False, "msg": "Nenhuma nova análise para salvar."}), 400

        # Converte a lista de dicionários em um único dicionário para salvar
        dados_formatados = {item['tag']: item['texto'] for item in analises}

        proc.analises = dados_formatados

        # Salva o dicionário no campo JSON do banco
        #a = proc.analises or {}
        #a.update(dados_formatados)
        #proc.analises = a
        db.session.commit()
        
        return jsonify({"ok": True, "msg": "Análises salvas com sucesso!"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao salvar análises para o processo {numero}: {e}")
        return jsonify({"error": True, "msg": "Erro ao salvar as análises!"}), 200

@main_bp.get('/processo/<numero>/baixar')
@login_required
@permission_required('analisar_processos')
def baixar(numero):
    tipo = request.args.get('tipo', 'word')
    current_app.logger.debug(f"Solicitação de download para o processo {numero} no formato: {tipo}")
    try:
        proc = Processo.query.filter_by(processo=numero).first_or_404()

        dados = session.get('dados', {})
        caminho_modelo = os.path.join(current_app.root_path, 'modelos', proc.classe.modelo_de_relatorio or 'modelo_relatorio.docx')
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