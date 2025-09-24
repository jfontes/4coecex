from extensions import db

class Classe(db.Model):
    __tablename__ = 'classe'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.String(50), nullable=False)

class OrgaoPrevidencia(db.Model):
    __tablename__ = 'orgao_previdencia'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)

class Criterio(db.Model):
    __tablename__ = 'criterio'
    id = db.Column(db.SmallInteger, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(150), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    tag = db.Column(db.String(50), nullable=False)
    sugestao_documento = db.Column(db.String(150), nullable=True)
    ativo = db.Column(db.Boolean, nullable=False, default=True, server_default='1')

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