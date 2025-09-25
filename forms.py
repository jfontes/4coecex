from flask_wtf import FlaskForm
from wtforms import (
    StringField, DecimalField, DateField,
    IntegerField, TextAreaField, SubmitField, BooleanField
)
from wtforms.validators import DataRequired, Regexp, Optional, NumberRange
from models import OrgaoPrevidencia, Classe
from wtforms_sqlalchemy.fields import QuerySelectField

class BuscaForm(FlaskForm):
    numero = StringField(
        'Número do Processo',
        validators=[DataRequired(), Regexp(r'^\d{6}$', message='Formato inválido. Use 123456')]
    )
    submit = SubmitField('Buscar')

class ClasseForm(FlaskForm):
    nome = StringField('Nome da Classe', validators=[DataRequired()])
    modelo_de_relatorio = StringField(
        'Arquivo do Modelo de Relatório', validators=[Optional()],
        description="Ex: modelo_aposentadoria_voluntaria.docx"
    )

class ProcessoForm(FlaskForm):
    processo = StringField(
        'Número do Processo',
        validators=[Optional(), Regexp(r'^\d{6}$', message='Use 6 dígitos, ex.: 123456')]
    )
    autuacao_processo = DateField('Data de Autuação', format='%Y-%m-%d', validators=[Optional()])
    classe = QuerySelectField(
        'Classe',
        query_factory = lambda: Classe.query.order_by(Classe.nome),
        get_label = 'nome',
        allow_blank = False
    )
    servidor = StringField('Servidor', filters=[lambda x: x.upper() if x else x], validators=[Optional()])
    matricula = StringField('Matrícula', filters=[lambda x: x.upper() if x else x], validators=[Optional()])
    cpf = StringField('CPF', validators=[Optional()])
    cargo = StringField('Cargo', filters=[lambda x: x.upper() if x else x], validators=[Optional()])
    orgao = StringField('Órgão', filters=[lambda x: x.upper() if x else x], validators=[Optional()])
    orgao_previdencia = QuerySelectField(
        'Órgão previdenciário',
        query_factory = lambda: OrgaoPrevidencia.query.order_by(OrgaoPrevidencia.id),
        get_label = 'nome',
        allow_blank = False
    )
    proventos = DecimalField('Proventos', validators=[Optional()])
    folha_ato_fixacao = StringField('Folha(s) do ato de fixação', validators=[Optional()])    
    ato_concessorio = StringField('Ato Concessório', filters=[lambda x: x.upper() if x else x], validators=[Optional()])
    data_ato_concessorio = DateField('Data do Ato Concessório', validators=[Optional()])
    folha_ato_concessorio = StringField('Folha(s) do ato concessório', validators=[Optional()])    
    data_inicio_concessao = DateField('Data do Início da Concessão', validators=[Optional()])
    publicacao = StringField('Publicação', filters=[lambda x: x.upper() if x else x], validators=[Optional()])
    data_publicacao = DateField('Data da Publicação', validators=[Optional()])
    fundamento_legal = TextAreaField('Fundamento Legal', render_kw={"rows":5}, validators=[Optional()])
    anos_tempo_de_contribuicao = IntegerField('Anos de Contribuição', validators=[Optional(), NumberRange(min=0)])
    dias_tempo_de_contribuicao = IntegerField('Dias de Contribuição', validators=[Optional(), NumberRange(min=0, max=364)])
    submit = SubmitField('Salvar Alterações')

class CriterioForm(FlaskForm):
    nome = StringField("Nome", validators=[DataRequired()])
    prompt = TextAreaField("Prompt de análise IA", validators=[DataRequired()])
    tag = StringField("Tag (marcador do arquivo no word)", validators=[DataRequired()])
    sugestao_documento = StringField("Sugestão de documento", validators=[DataRequired()])
    ativo = BooleanField("Ativo", default=True)
    submit = SubmitField("Salvar")
