from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class Classe(db.Model):
    __tablename__ = 'classe'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.String(50), nullable=False)
    modelo_de_relatorio = db.Column(db.String(50), nullable=False)

class OrgaoPrevidencia(db.Model):
    __tablename__ = 'orgao_previdencia'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)

criterio_grupo = db.Table('criterio_grupo',
    db.Column('criterio_id', db.Integer, db.ForeignKey('criterio.id'), primary_key=True),
    db.Column('grupo_id', db.Integer, db.ForeignKey('grupo.id'), primary_key=True)
)

class Grupo(db.Model):
    __tablename__ = 'grupo'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text, nullable=True)
    # O relacionamento 'back_populates' cria uma via de mão dupla entre os modelos
    criterios = db.relationship(
        'Criterio', 
        secondary=criterio_grupo, 
        back_populates='grupos'
    )
    def __repr__(self):
        return f'<Grupo {self.nome}>'
    
class Criterio(db.Model):
    __tablename__ = 'criterio'
    id = db.Column(db.SmallInteger, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(150), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    tag = db.Column(db.String(50), nullable=False)
    sugestao_documento = db.Column(db.String(150), nullable=True)
    ativo = db.Column(db.Boolean, nullable=False, default=True, server_default='1')
    grupos = db.relationship(
        'Grupo', 
        secondary=criterio_grupo, 
        back_populates='criterios'
    )
    def __repr__(self):
        return f"<Critério {self.id} - {self.nome}>"

class Processo(db.Model):
    __tablename__ = 'processo'
    id = db.Column(db.Integer, primary_key=True)
    servidor = db.Column(db.String(150))
    matricula = db.Column(db.String(15))
    cpf = db.Column(db.String(14))
    cargo = db.Column(db.String(150))
    orgao = db.Column(db.String(150))
    proventos = db.Column(db.Numeric(12, 2))
    ato_concessorio = db.Column(db.String(100))
    data_ato_concessorio = db.Column(db.Date)
    publicacao = db.Column(db.String(150))
    data_publicacao = db.Column(db.Date)
    processo = db.Column(db.String(6))
    autuacao_processo = db.Column(db.Date)
    fundamento_legal = db.Column(db.Text)
    anos_tempo_de_contribuicao = db.Column(db.Integer)
    dias_tempo_de_contribuicao = db.Column(db.Integer)
    folha_ato_concessorio = db.Column(db.String(20))
    folha_ato_fixacao = db.Column(db.String(20))
    atualizado = db.Column(db.Integer)
    data_inicio_concessao = db.Column(db.Date)
    dados_previdencia = db.Column(db.JSON)
    analises = db.Column(db.JSON)
    rg = db.Column(db.String(20))
    orgao_previdencia_id = db.Column(
        db.Integer,
        db.ForeignKey('orgao_previdencia.id'),
        nullable=True
    )
    orgao_previdencia = db.relationship(
        'OrgaoPrevidencia',
        backref=db.backref('processos', lazy='dynamic'),
        lazy='joined'
    )
    classe_id = db.Column(
        db.Integer,
        db.ForeignKey('classe.id'),
        nullable=True
    )
    classe = db.relationship(
        'Classe',
        backref=db.backref('processos', lazy='dynamic'),
        lazy='joined'
    )

roles_permissions = db.Table('roles_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    role = db.relationship('Role', back_populates='users')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    users = db.relationship('User', back_populates='role')
    permissions = db.relationship('Permission', secondary=roles_permissions, backref=db.backref('roles', lazy='dynamic'))

    def has_permission(self, permission_name):
        return any(p.name == permission_name for p in self.permissions)

class Permission(db.Model):
    __tablename__ = 'permission'
    id = db.Column(db.Integer, primary_key=True)
    # Nome da permissão, ex: 'acessar_cadastro_criterios'
    name = db.Column(db.String(100), unique=True, nullable=False)
    # Descrição amigável para a tela do admin, ex: 'Acessar o menu de Cadastro de Critérios'
    description = db.Column(db.String(255))