# models.py (VERSÃO FINAL COMPLETA E VERIFICADA)

from datetime import date, datetime, time
from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ==============================================================================
# TABELA DE USUÁRIOS E PERMISSÕES (RBAC)
# ==============================================================================
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))

    # Roles: 'admin', 'gerente', 'compras', 'operador'
    role = db.Column(db.String(20), nullable=False, default='operador')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # === REGRAS DE PERMISSÃO ===
    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def can_see_money(self):
        # Quem pode VER valores financeiros: Admin, Gerente e Compras
        return self.role in ['admin', 'gerente', 'compras']

    @property
    def can_edit_general(self):
        # Quem pode editar CADASTRO (Cliente, Datas, Escopo):
        # Apenas Admin e Gerente. (Compras e Operador NÃO editam isso)
        return self.role in ['admin', 'gerente']

    @property
    def can_edit_predicted(self):
        # Quem pode editar o valor PREVISTO das despesas?
        # Compras NÃO pode (ele só lança o realizado).
        return self.role in ['admin', 'gerente']

# ==============================================================================
# TABELAS DE ORDEM DE SERVIÇO (OS)
# ==============================================================================
class OS(db.Model):
    __tablename__ = 'os'
    id = db.Column(db.Integer, primary_key=True)

    # Dados Principais
    numero = db.Column(db.String(50), unique=True, nullable=False)
    cliente = db.Column(db.String(150), nullable=False)
    fase = db.Column(db.String(20), default='OS') # Pré-OS ou OS
    status = db.Column(db.String(20), nullable=False, default='Aberta')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    empresa = db.Column(db.String(50), nullable=True) # Reconlog Brasil, etc.

    # Datas
    data_emissao = db.Column(db.Date, nullable=False, default=date.today)
    data_inicio = db.Column(db.Date, nullable=True)
    data_termino = db.Column(db.Date, nullable=True) # Data Prevista
    data_entrega = db.Column(db.Date, nullable=True)
    data_conclusao = db.Column(db.Date, nullable=True)
    data_carregamento = db.Column(db.Date, nullable=True) # Mantido por compatibilidade

    # Contrato e Valores
    tipo_contrato = db.Column(db.String(50), nullable=True)
    valor = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal('0.00'))

    # Detalhes Técnicos
    TipoLoc = db.Column(db.String(15), nullable=True)
    Tipo_OS = db.Column(db.String(15), nullable=True)
    Modelo = db.Column(db.String(15), nullable=True)
    qtde = db.Column(db.Numeric(10, 3), nullable=True)
    largura = db.Column(db.Numeric(10, 5), nullable=True)
    comprim = db.Column(db.Numeric(10, 5), nullable=True)
    Pedireito = db.Column(db.Numeric(10, 5), nullable=True)
    Piso = db.Column(db.String(15), nullable=True)
    Acessorios = db.Column(db.String(60), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    Obs2 = db.Column(db.String(60), nullable=True)

    # Dados do Cliente
    Razao = db.Column(db.String(30), nullable=True)
    CNPJ = db.Column(db.String(14), nullable=True)
    Insc = db.Column(db.String(15), nullable=True)
    email = db.Column(db.String(30), nullable=True)
    telefone = db.Column(db.String(30), nullable=True)

    # Responsáveis
    Segtrab = db.Column(db.String(20), nullable=True)
    integracao = db.Column(db.String(20), nullable=True)
    vendedo = db.Column(db.String(40), nullable=True)

    # Endereço Principal
    endereco = db.Column(db.String(40), nullable=True)
    Bairro = db.Column(db.String(40), nullable=True)
    Cidade = db.Column(db.String(40), nullable=True)
    UF = db.Column(db.String(2), nullable=True)
    CEP = db.Column(db.String(8), nullable=True)

    # === Endereço Faturamento ===
    fat_endereco = db.Column(db.String(100), nullable=True)
    fat_bairro = db.Column(db.String(50), nullable=True)
    fat_cidade = db.Column(db.String(50), nullable=True)
    fat_uf = db.Column(db.String(2), nullable=True)
    fat_cep = db.Column(db.String(10), nullable=True)
    fat_emails = db.Column(db.String(100), nullable=True)

    # === Endereço Montagem ===
    mont_endereco = db.Column(db.String(100), nullable=True)
    mont_bairro = db.Column(db.String(50), nullable=True)
    mont_cidade = db.Column(db.String(50), nullable=True)
    mont_uf = db.Column(db.String(2), nullable=True)
    mont_cep = db.Column(db.String(10), nullable=True)

    # Histórico de Versão
    revisao = db.Column(db.Integer, default=0, nullable=False)

    # Relacionamentos
    ordens_producao = db.relationship('OrdemProducao', backref='os', lazy=True, cascade="all, delete-orphan")
    custos_operacionais = db.relationship('CustoOperacional', backref='os', lazy='select', cascade="all, delete-orphan")
    custos_visitas = db.relationship('CustoVisita', backref='os', lazy='select', cascade="all, delete-orphan")
    carregamentos = db.relationship('Carregamento', backref='os', lazy=True, cascade="all, delete-orphan")
    versoes = db.relationship('OSVersao', backref='os_pai', lazy=True, order_by="desc(OSVersao.numero_revisao)", cascade="all, delete-orphan")

    def __repr__(self):
         return f"OS {self.numero}"

class OSVersao(db.Model):
    __tablename__ = 'os_versao'
    id = db.Column(db.Integer, primary_key=True)
    os_id = db.Column(db.Integer, db.ForeignKey('os.id'), nullable=False)
    numero_revisao = db.Column(db.Integer, nullable=False)
    data_arquivamento = db.Column(db.DateTime, default=datetime.now)
    usuario_responsavel = db.Column(db.String(50))
    motivo = db.Column(db.String(100))
    dados_snapshot = db.Column(db.Text, nullable=False) # JSON completo

class Carregamento(db.Model):
    __tablename__ = 'carregamento'
    id = db.Column(db.Integer, primary_key=True)
    os_id = db.Column(db.Integer, db.ForeignKey('os.id'), nullable=False)
    data = db.Column(db.Date, nullable=False, default=date.today)
    placa_caminhao = db.Column(db.String(20), nullable=True)
    documento_referencia = db.Column(db.String(100), nullable=True)
    observacao = db.Column(db.String(200), nullable=True)

# ==============================================================================
# TABELAS FINANCEIRAS (CUSTOS)
# ==============================================================================
class Despesa(db.Model):
    __tablename__ = 'despesa'
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(100), unique=True, nullable=False)
    tipo = db.Column(db.String(20), nullable=False) # 'Operacional' ou 'Visita'
    custos_operacionais = db.relationship('CustoOperacional', backref='despesa', lazy=True)
    custos_visitas = db.relationship('CustoVisita', backref='despesa', lazy=True)
    def __repr__(self): return f"<Despesa {self.descricao}>"

class CustoOperacional(db.Model):
    __tablename__ = 'custo_operacional'
    id = db.Column(db.Integer, primary_key=True)
    os_id = db.Column(db.Integer, db.ForeignKey('os.id'), nullable=False)
    despesa_id = db.Column(db.Integer, db.ForeignKey('despesa.id'), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    valor_realizado = db.Column(db.Numeric(10, 2), nullable=True)
    data = db.Column(db.Date, nullable=False, default=date.today)
    observacao = db.Column(db.String(200), nullable=True)
    responsavel = db.Column(db.String(20), nullable=False, default='Reconlog')

class CustoVisita(db.Model):
    __tablename__ = 'custo_visita'
    id = db.Column(db.Integer, primary_key=True)
    os_id = db.Column(db.Integer, db.ForeignKey('os.id'), nullable=False)
    despesa_id = db.Column(db.Integer, db.ForeignKey('despesa.id'), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    valor_realizado = db.Column(db.Numeric(10, 2), nullable=True)
    data = db.Column(db.Date, nullable=False, default=date.today)
    observacao = db.Column(db.String(200), nullable=True)
    responsavel = db.Column(db.String(20), nullable=False, default='Reconlog')

# ==============================================================================
# TABELAS DE ORDEM DE PRODUÇÃO (OP)
# ==============================================================================
class OrdemProducao(db.Model):
    __tablename__ = 'ordem_producao'
    id = db.Column(db.Integer, primary_key=True)
    numero_sequencial = db.Column(db.Integer, unique=True, nullable=False)
    os_id = db.Column(db.Integer, db.ForeignKey('os.id'), nullable=False)

    status = db.Column(db.String(15), nullable=False, default='Aberto')
    departamento = db.Column(db.String(50), nullable=False)
    cliente = db.Column(db.String(60), nullable=False)
    codigo = db.Column(db.String(8), nullable=False)

    # Detalhes do Produto
    part_number_produto = db.Column(db.String(40), nullable=True)
    quantidade = db.Column(db.Numeric(7, 2), nullable=False)
    largura = db.Column(db.Numeric(6, 2), nullable=False)
    comprimento = db.Column(db.Numeric(4, 0), nullable=False)
    pe_direito = db.Column(db.Numeric(4, 0), nullable=False)
    piso = db.Column(db.String(10), nullable=True)
    acessorios = db.Column(db.Text, nullable=True)

    # Datas e Prazos
    data_emissao = db.Column(db.Date, nullable=False)
    data_inicio_previsto = db.Column(db.Date, nullable=False)
    data_termino_previsto = db.Column(db.Date, nullable=False)
    data_carregamento = db.Column(db.Date, nullable=False)
    data_fechamento = db.Column(db.Date, nullable=True)
    data_encerramento = db.Column(db.Date, nullable=True)
    data_entrega_expedicao = db.Column(db.Date, nullable=True)

    # Outros
    tipo_contrato = db.Column(db.String(8), nullable=False)
    tipo_op = db.Column(db.String(5), nullable=False)
    setor = db.Column(db.String(20), nullable=False)
    observacoes = db.Column(db.Text, nullable=True)
    assinatura_responsavel = db.Column(db.String(50), nullable=True)

    # Relacionamentos
    controles_producao = db.relationship('ControleProducao', backref='ordem_producao', lazy=True, cascade="all, delete-orphan")
    romaneios = db.relationship('Romaneio', backref='ordem_producao', lazy=True, cascade="all, delete-orphan")
    apontamentos = db.relationship('Apontamento', backref='ordem_producao', lazy=True, cascade="all, delete-orphan")
    paradas = db.relationship('ParadaNaoPlanejada', backref='ordem_producao', lazy=True, cascade="all, delete-orphan")

class Produto(db.Model):
    __tablename__ = 'produto'
    id = db.Column(db.Integer, primary_key=True)
    part_number = db.Column(db.String(40), unique=True, nullable=False)
    sku = db.Column(db.String(8), nullable=True)
    descricao = db.Column(db.String(40), nullable=False)
    tipo_de_material = db.Column(db.String(15), nullable=True)
    custo = db.Column(db.Numeric(15, 3), nullable=False, default=Decimal('0.0'))

    def to_dict(self):
        return {
            'id': self.id,
            'part_number': self.part_number,
            'sku': self.sku,
            'descricao': self.descricao,
            'tipo_de_material': self.tipo_de_material,
            'custo': str(self.custo)
        }

class ControleProducao(db.Model):
    __tablename__ = 'controle_producao'
    id = db.Column(db.Integer, primary_key=True)
    ordem_producao_id = db.Column(db.Integer, db.ForeignKey('ordem_producao.id'), nullable=False)
    turno = db.Column(db.String(5), nullable=True)
    departamento = db.Column(db.String(50), nullable=True)
    obs_prod = db.Column(db.Text, nullable=True)
    processo = db.Column(db.String(100), nullable=True)
    maquina = db.Column(db.String(100), nullable=True)
    operador = db.Column(db.String(100), nullable=True)
    data_inicio = db.Column(db.Date, nullable=True)
    hora_inicio = db.Column(db.Time, nullable=True)
    data_pausa = db.Column(db.Date, nullable=True)
    motivo_pausa = db.Column(db.String(255), nullable=True)
    data_termino = db.Column(db.Date, nullable=True)
    hora_termino = db.Column(db.Time, nullable=True)
    qualidade = db.Column(db.String(20), nullable=True)

class Romaneio(db.Model):
    __tablename__ = 'romaneio'
    id = db.Column(db.Integer, primary_key=True)
    ordem_producao_id = db.Column(db.Integer, db.ForeignKey('ordem_producao.id'), nullable=False)
    id_item = db.Column(db.Integer, nullable=True)
    descricao = db.Column(db.String(60), nullable=True)
    quantidade = db.Column(db.Integer, nullable=True)
    materia_prima_utilizada = db.Column(db.String(50), nullable=True)

class Apontamento(db.Model):
    __tablename__ = 'apontamento'
    id = db.Column(db.Integer, primary_key=True)
    ordem_producao_id = db.Column(db.Integer, db.ForeignKey('ordem_producao.id'), nullable=False)
    departamento = db.Column(db.String(50), nullable=True)
    obs_prod = db.Column(db.Text, nullable=True)
    turno = db.Column(db.String(5), nullable=False)
    processo = db.Column(db.String(10), nullable=False)
    maquina_operacao = db.Column(db.String(10), nullable=False)
    operador = db.Column(db.String(50), nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    hora_inicio = db.Column(db.Time, nullable=False)
    data_termino = db.Column(db.Date, nullable=False)
    hora_termino = db.Column(db.Time, nullable=False)
    qualidade_aprovado = db.Column(db.Boolean, default=True)

class ParadaNaoPlanejada(db.Model):
    __tablename__ = 'parada_nao_planejada'
    id = db.Column(db.Integer, primary_key=True)
    ordem_producao_id = db.Column(db.Integer, db.ForeignKey('ordem_producao.id'), nullable=False)
    parada = db.Column(db.String(50), nullable=False)
    tempo_espera = db.Column(db.Time, nullable=False)
    desvios_registrados = db.Column(db.Text, nullable=True)
    aprovacao_desvio = db.Column(db.String(50), nullable=True)

# ==============================================================================
# TABELAS DE MANUTENÇÃO
# ==============================================================================
class OSManutencao(db.Model):
    __tablename__ = 'os_manutencao'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(6), unique=True, nullable=False)
    data_abertura = db.Column(db.Date, nullable=False, default=date.today)
    hora_abert = db.Column(db.Time, nullable=False, default=time(0, 0, 0))
    data_encerramento = db.Column(db.Date, nullable=True)
    solicitante = db.Column(db.String(40), nullable=False)
    area_setor = db.Column(db.String(40), nullable=True)
    maq_equip = db.Column(db.String(100), nullable=False)
    ocorrencia = db.Column(db.String(150), nullable=True)
    parada = db.Column(db.String(2), nullable=False, default='Não')

    # Checkboxes de Tipo de Manutenção
    manut_corretiva = db.Column(db.Boolean, nullable=False, default=False)
    manut_preventiva = db.Column(db.Boolean, nullable=False, default=False)
    manut_preditiva = db.Column(db.Boolean, nullable=False, default=False)
    inspecao = db.Column(db.Boolean, nullable=False, default=False)
    melhorias = db.Column(db.Boolean, nullable=False, default=False)
    predial = db.Column(db.Boolean, nullable=False, default=False)
    outro = db.Column(db.Boolean, nullable=False, default=False)

    # Detalhes
    sintoma = db.Column(db.String(100), nullable=True)
    causa = db.Column(db.String(100), nullable=True)
    intervencao = db.Column(db.String(100), nullable=True)
    materiais_utilizados = db.Column(db.String(100), nullable=True)
    materiais_comprados = db.Column(db.String(100), nullable=True)
    ficha_tec = db.Column(db.String(200), nullable=True)
    obs_manut = db.Column(db.String(100), nullable=True)
    assinatura1 = db.Column(db.String(50), nullable=True)
    assinatura2 = db.Column(db.String(50), nullable=True)

    apontamentos = db.relationship('ManutApont', backref='os_manutencao', lazy=True, cascade="all, delete-orphan")

class ManutApont(db.Model):
    __tablename__ = 'manut_apont'
    id = db.Column(db.Integer, primary_key=True)
    os_manutencao_id = db.Column(db.Integer, db.ForeignKey('os_manutencao.id'), nullable=False)
    manutentor = db.Column(db.String(40), nullable=False)
    data_inicio = db.Column(db.Date, nullable=True)
    hora_inicio = db.Column(db.Time, nullable=True)
    data_termino = db.Column(db.Date, nullable=True)
    hora_termino = db.Column(db.Time, nullable=True)