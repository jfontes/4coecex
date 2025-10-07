from flask_wtf import FlaskForm
from wtforms import (
    StringField, DecimalField, DateField, SelectMultipleField,
    IntegerField, TextAreaField, SubmitField, BooleanField, SelectField, PasswordField
)
from wtforms.validators import DataRequired, Regexp, Optional, NumberRange, Length
from models import OrgaoPrevidencia, Classe
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_wtf.file import FileField, FileAllowed
from models import Criterio

class LoginForm(FlaskForm):
    """Formulário de login."""
    username = StringField('Utilizador', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar-me')

class BuscaForm(FlaskForm):
    numero = StringField(
        'Número do Processo',
        validators=[DataRequired(), Regexp(r'^\d{6}$', message='Formato inválido. Use 123456')]
    )
    submit = SubmitField('Buscar')

class GrupoForm(FlaskForm):
    """Formulário para criar e editar Grupos."""
    nome = StringField('Nome do Grupo', validators=[DataRequired(), Length(max=100)])
    descricao = TextAreaField('Descrição', validators=[Optional()])

    # Campo de múltipla seleção para associar critérios
    criterios = SelectMultipleField(
        'Critérios associados',
        coerce=int, # Garante que os valores do formulário sejam convertidos para inteiros (IDs)
        validators=[DataRequired(message="Selecione ao menos um critério.")]
    )

    def __init__(self, *args, **kwargs):
        """Popula as opções do campo 'criterios' dinamicamente."""
        super(GrupoForm, self).__init__(*args, **kwargs)
        # Busca todos os critérios ativos e os ordena por nome
        self.criterios.choices = [
            (c.id, c.nome) for c in Criterio.query.filter_by(ativo=True).order_by(Criterio.nome).all()
        ]

class ClasseForm(FlaskForm):
    """Formulário para criar e editar Classes."""
    nome = StringField('Nome da Classe', validators=[DataRequired(), Length(max=100)])
    
    # NOVO CAMPO: Dropdown para selecionar um modelo já existente
    modelo_existente = SelectField(
        'Selecione um modelo existente',
        choices=[], # As opções serão populadas dinamicamente na rota
        coerce=str,
        validators=[Optional()],
        description="Escolha um modelo da lista para associar a esta classe."
    )

    # CAMPO DE UPLOAD: Permanece para enviar novos arquivos
    novo_modelo = FileField(
        'Ou envie um novo modelo (.docx)',
        validators=[
            Optional(), 
            FileAllowed(['docx'], 'Apenas arquivos .docx são permitidos!')
        ],
        description="Se um novo arquivo for enviado, ele terá prioridade sobre o modelo selecionado."
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
    rg = StringField('RG', filters=[lambda x: x.upper() if x else x], validators=[Optional()])
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
