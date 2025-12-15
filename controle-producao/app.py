# app.py (VERSÃO COMPLETA - SEM CORTES)

import json
from datetime import date, datetime, time, timedelta
from sqlalchemy import func, extract, or_
from collections import defaultdict
import os
import csv
from decimal import Decimal, InvalidOperation
import click
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv

# ==================== IMPORTAÇÕES DE MODELOS E FORMS ====================
from models import (
    db, User, OS, OSVersao, OrdemProducao, Romaneio, ControleProducao, Produto,
    Apontamento, ParadaNaoPlanejada, Despesa, CustoOperacional, CustoVisita, Carregamento,
    OSManutencao, ManutApont, 
    # Novos Models
    Fornecedor, SolicitacaoCompra, SolicitacaoItem, PedidoCompra, PedidoItem, TipoFornecedor
)

from forms import (
    LoginForm, OSForm, OrdemProducaoForm, ControleProducaoForm,
    RomaneioForm, ProdutoForm, ApontamentoForm, ParadaForm,
    DespesaForm, CustoOperacionalForm, CustoVisitaForm, UserForm,
    OSManutencaoForm, ManutApontForm, 
    # Novos Forms
    FornecedorForm, SolicitacaoCompraForm, TipoFornecedorForm, PedidoCompraForm
)

# ==================== INICIALIZAÇÃO DO APP ====================
load_dotenv()

app = Flask(__name__)

# Configurações
app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-dificil-de-adivinhar-troque-depois'
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASS')}@{os.environ.get('DB_HOST')}/{os.environ.get('DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# === CORREÇÃO DE QUEDAS DE CONEXÃO (POOL PRE-PING) ===
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 280,
    'pool_pre_ping': True,
    'pool_size': 10,
    'max_overflow': 20
}

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== FILTROS E HELPERS ====================

@app.template_filter('format_currency')
def format_currency(value):
    if value is None:
        return "0,00"
    try:
        return f"{value:,.2f}".replace(',', 'v').replace('.', ',').replace('v', '.')
    except:
        return str(value)

@app.template_filter('from_json')
def from_json_filter(s):
    import json
    return json.loads(s)

def alchemy_encoder(obj):
    if isinstance(obj, (date, datetime)):
        return obj.strftime('%Y-%m-%d')
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, time):
        return obj.strftime('%H:%M')
    return None

def criar_snapshot_os(os_obj, usuario, motivo):
    """Cria uma cópia dos dados atuais da OS e salva na tabela OSVersao."""
    dados = {
        'cabecalho': {
            'numero': os_obj.numero,
            'cliente': os_obj.cliente,
            'fase': getattr(os_obj, 'fase', 'OS'),
            'empresa': getattr(os_obj, 'empresa', ''),
            'status': os_obj.status,
            'valor_total': os_obj.valor,
            'data_emissao': os_obj.data_emissao,
            'data_entrega': getattr(os_obj, 'data_entrega', None),
            'data_conclusao': getattr(os_obj, 'data_conclusao', None),
            'tipo_contrato': getattr(os_obj, 'tipo_contrato', ''),
            'Tipo_OS': getattr(os_obj, 'Tipo_OS', ''),
            'observacoes': os_obj.observacoes,
            'Obs2': getattr(os_obj, 'Obs2', ''),
            'enderecos': {
                'fat_endereco': getattr(os_obj, 'fat_endereco', ''),
                'fat_cidade': getattr(os_obj, 'fat_cidade', ''),
                'mont_endereco': getattr(os_obj, 'mont_endereco', ''),
                'mont_cidade': getattr(os_obj, 'mont_cidade', '')
            }
        },
        'custos': [],
        'carregamentos': []
    }

    for c in os_obj.custos_operacionais:
        dados['custos'].append({
            'tipo': 'Operacional',
            'despesa': c.despesa.descricao,
            'valor_previsto': c.valor,
            'valor_realizado': getattr(c, 'valor_realizado', None),
            'data': c.data,
            'responsavel': c.responsavel,
            'obs': c.observacao
        })

    for c in os_obj.custos_visitas:
        dados['custos'].append({
            'tipo': 'Visita',
            'despesa': c.despesa.descricao,
            'valor_previsto': c.valor,
            'valor_realizado': getattr(c, 'valor_realizado', None),
            'data': c.data,
            'responsavel': c.responsavel,
            'obs': c.observacao
        })

    if hasattr(os_obj, 'carregamentos'):
        for car in os_obj.carregamentos:
            dados['carregamentos'].append({
                'data': car.data,
                'placa': car.placa_caminhao,
                'doc': car.documento_referencia,
                'obs': car.observacao
            })

    nova_versao = OSVersao(
        os_id=os_obj.id,
        numero_revisao=os_obj.revisao,
        usuario_responsavel=usuario,
        motivo=motivo,
        dados_snapshot=json.dumps(dados, default=alchemy_encoder, indent=4)
    )
    db.session.add(nova_versao)
    os_obj.revisao += 1
    return True

# === MAPAS E DADOS AUXILIARES ===
MAQUINAS_POR_SETOR = {
    'ADM': ['ESCRITORIO'],
    'FACILITIES': ['PREDIAL'],
    'FABRICA DE LONAS': [
        'MÁQUINA DE AR QUENTE - S/ID (ID: 13)', 'MÁQUINA DE COSTURA - S/ID (ID: 12)', 'MÁQUINA DE ILHOS - S/ID (ID: 14)',
        'MÁQUINA DE SOLDA DE ALTA FREQUÊNCIA - 17K (ID: 1)', 'MÁQUINA DE SOLDA DE ALTA FREQUÊNCIA - 7G (ID: 2)',
        'MÁQUINA DE SOLDA DE ALTA FREQUÊNCIA - 7G (ID: 3)', 'MÁQUINA DE SOLDA DE ALTA FREQUÊNCIA - 7G (ID: 4)',
        'MÁQUINA DE SOLDA DE ALTA FREQUÊNCIA - 7G (ID: 5)', 'MÁQUINA DE SOLDA DE ALTA FREQUÊNCIA - 7G (ID: 6)',
        'MÁQUINA DE SOLDA DE ALTA FREQUÊNCIA - 7G (ID: 7)', 'MÁQUINA DE SOLDA DE ALTA FREQUÊNCIA - 7G (ID: 8)',
        'MÁQUINA DE SOLDA DE ALTA FREQUÊNCIA - 7G (ID: 9)', 'MÁQUINA DE SOLDA DE ALTA FREQUÊNCIA - 7G (ID: 10)',
        'MÁQUINA DE SOLDA DE ALTA FREQUÊNCIA - 7G (ID: 11)'
    ],
    'LAVAGEM DE LONAS': ['MAKITA - DXT (ID: 26)', 'SERRA - S/ID (ID: 27)'],
    'METALURGICA': [
        'FURADEIRA DE BANCADA KONE - KM30MF (ID: 21)', 'PLASMA CNC METALIQUE - MT01 (ID: 25)', 'PLASMA CNC METALIQUE - MT10 (ID: 24)',
        'PRENSA MAQ DRAW - S/ID (ID: 22)', 'SERRA DE FITA FRANHO - FMG500HM (ID: 15)', 'SERRA DE FITA FRANHO - FMG500HM (ID: 16)',
        'SERRA DE FITA FRANHO - FMG500HM (ID: 17)', 'SERRA DE FITA FRANHO - FMG500HM (ID: 18)', 'SERRA DE FITA FRANHO - FMG500HM (ID: 19)',
        'SERRA DE FITA KONE - KM30MF (ID: 20)', 'SERRA POLICORTE - S/ID (ID: 23)'
    ]
}

PROCESSOS_POR_DEPARTAMENTO = {
    'Metalúrgica': [('Solda', 'Solda'), ('Ponteamento', 'Ponteamento'), ('Corte/Fixação', 'Corte/Fixação'), ('Serra', 'Serra'), ('Plasma', 'Plasma'), ('5S', '5S')],
    'Lavagem Lona': [('Lavagem Lona', 'Lavagem Lona'), ('5S', '5S')],
    'Confecção Lona': [('Confecção Lona', 'Confecção Lona'), ('5S', '5S')],
    'Logística': [('Carga e Descarga', 'Carga e Descarga'), ('Armazenamento', 'Armazenamento'), ('Picking', 'Picking')]
}

def preencher_choices_maquina(form_os):
    setor_selecionado = form_os.area_setor.data
    if setor_selecionado in MAQUINAS_POR_SETOR:
        opcoes = [(m, m) for m in MAQUINAS_POR_SETOR[setor_selecionado]]
        form_os.maq_equip.choices = [('', 'Selecione a máquina')] + opcoes
    else:
        form_os.maq_equip.choices = [('', 'Selecione um setor primeiro')]

def preencher_choices_processo(form_op):
    for item_controle in form_op.controles_producao:
        depto_selecionado = item_controle.departamento.data
        if depto_selecionado in PROCESSOS_POR_DEPARTAMENTO:
            choices = [('', 'Selecione um processo')] + PROCESSOS_POR_DEPARTAMENTO[depto_selecionado]
            item_controle.processo.choices = choices
        else:
            item_controle.processo.choices = [('', 'Selecione um departamento primeiro')]

# Decorator de Segurança
def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if current_user.role not in roles:
                flash("Acesso Negado: Você não tem permissão para acessar esta área.", "danger")
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_view
    return wrapper

# ==============================================================================
# ROTAS DE LOGIN E DASHBOARD
# ==============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Usuário ou senha inválidos', 'danger')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('auth/login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    try:
        hoje = date.today()
        mes_atual = hoje.month
        ano_atual = hoje.year

        # Filtra Nulos para evitar erros
        qtd_pre_os = OS.query.filter(
            OS.fase == 'Pré-OS',
            extract('month', OS.data_emissao) == mes_atual,
            extract('year', OS.data_emissao) == ano_atual,
            OS.data_emissao.isnot(None)
        ).count()

        qtd_os = OS.query.filter(
            OS.fase == 'OS',
            extract('month', OS.data_emissao) == mes_atual,
            extract('year', OS.data_emissao) == ano_atual,
            OS.data_emissao.isnot(None)
        ).count()

        total_abertas = OS.query.filter(
            OS.status.in_(['Aberta', 'Em Andamento']),
            OS.fase == 'OS'
        ).count()

        qtd_concluidas = OS.query.filter(
            OS.status == 'Concluída',
            extract('month', OS.data_conclusao) == mes_atual,
            extract('year', OS.data_conclusao) == ano_atual
        ).count()

        antigas_abertas = OS.query.filter(
            OS.status.notin_(['Concluída', 'Cancelada']),
            OS.data_emissao.isnot(None)
        ).order_by(OS.data_emissao.asc()).limit(5).all()

        lista_antigas = []
        for os_obj in antigas_abertas:
            if os_obj.data_emissao:
                dias = (hoje - os_obj.data_emissao).days
            else:
                dias = 0
            lista_antigas.append({
                'id': os_obj.id,
                'numero': os_obj.numero,
                'cliente': os_obj.cliente,
                'fase': getattr(os_obj, 'fase', 'OS'),
                'dias': dias,
                'status': os_obj.status
            })

        evolucao_query = db.session.query(
            func.date_format(OS.data_emissao, '%Y-%m').label('mes_ano'),
            OS.fase,
            func.count(OS.id)
        ).filter(OS.data_emissao.isnot(None))\
         .group_by('mes_ano', OS.fase)\
         .order_by('mes_ano').limit(12).all()

        dados_evolucao = defaultdict(lambda: {'Pré-OS': 0, 'OS': 0})
        for mes, fase, qtd in evolucao_query:
            if mes: dados_evolucao[mes][fase] = qtd

        labels_chart = sorted(dados_evolucao.keys())
        data_pre = [dados_evolucao[m].get('Pré-OS', 0) for m in labels_chart]
        data_os = [dados_evolucao[m].get('OS', 0) for m in labels_chart]

        bar_chart_data = json.dumps({
            'labels': labels_chart,
            'datasets': [
                {'label': 'Pré-OS', 'data': data_pre, 'backgroundColor': '#adb5bd', 'borderRadius': 4},
                {'label': 'OS Definitiva', 'data': data_os, 'backgroundColor': '#0d6efd', 'borderRadius': 4}
            ]
        })

        status_query = db.session.query(OS.status, func.count(OS.id)).group_by(OS.status).all()
        pie_labels = [s[0] for s in status_query]
        pie_values = [s[1] for s in status_query]
        pie_chart_data = json.dumps({
            'labels': pie_labels,
            'datasets': [{'data': pie_values, 'backgroundColor': ['#198754', '#ffc107', '#0d6efd', '#dc3545', '#6c757d']}]
        })

        return render_template('dashboard.html',
                               title="Visão Geral", kpi_pre_os=qtd_pre_os, kpi_os=qtd_os,
                               total_abertas=total_abertas, kpi_concluidas=qtd_concluidas,
                               lista_antigas=lista_antigas, bar_chart_data=bar_chart_data,
                               pie_chart_data=pie_chart_data, mes_nome=hoje.strftime('%m/%Y'))

    except Exception as e:
        print(f"Erro no dashboard: {e}")
        return render_template('dashboard.html', title="Dashboard (Erro)", kpi_pre_os=0, kpi_os=0, total_abertas=0, kpi_concluidas=0, lista_antigas=[], bar_chart_data='{}', pie_chart_data='{}')

# ==============================================================================
# ROTAS DE ORDEM DE SERVIÇO (OS)
# ==============================================================================

@app.route('/os')
@login_required
def lista_os():
    # 1. Captura os filtros da URL (GET)
    f_cliente = request.args.get('cliente', '')
    f_fase = request.args.get('fase', '')
    f_tipo_os = request.args.get('tipo_os', '')
    f_empresa = request.args.get('empresa', '')
    f_data_ini = request.args.get('data_ini', '')

    # 2. Inicia a Query Base
    query = OS.query

    # 3. Aplica os Filtros (se existirem)
    if f_cliente:
        query = query.filter(OS.cliente.ilike(f"%{f_cliente}%"))

    if f_fase:
        query = query.filter(OS.fase == f_fase)

    if f_tipo_os:
        query = query.filter(OS.Tipo_OS == f_tipo_os)

    if f_empresa:
        query = query.filter(OS.empresa == f_empresa)

    if f_data_ini:
        query = query.filter(OS.data_emissao >= f_data_ini)

    # 4. Executa a busca ordenando pelas mais recentes
    lista_filtrada = query.order_by(OS.id.desc()).all()

    # 5. Dados para popular os Dropdowns de Filtro (Valores únicos do banco)
    opcoes_tipo_os = sorted([r[0] for r in db.session.query(OS.Tipo_OS).distinct().filter(OS.Tipo_OS.isnot(None))])
    opcoes_empresas = sorted([r[0] for r in db.session.query(OS.empresa).distinct().filter(OS.empresa.isnot(None))])

    return render_template('lista_os.html',
                           lista_os=lista_filtrada,
                           title="Ordens de Serviço",
                           opcoes_tipo_os=opcoes_tipo_os,
                           opcoes_empresas=opcoes_empresas)

@app.route('/os/nova', methods=['GET', 'POST'])
@login_required
def nova_os():
    form = OSForm()
    despesas_op = [(d.id, d.descricao) for d in Despesa.query.filter_by(tipo='Operacional').order_by(Despesa.descricao).all()]
    despesas_vis = [(d.id, d.descricao) for d in Despesa.query.filter_by(tipo='Visita').order_by(Despesa.descricao).all()]

    for custo_op_entry in form.custos_operacionais:
        custo_op_entry.despesa_id.choices = despesas_op
    for custo_vis_entry in form.custos_visitas:
        custo_vis_entry.despesa_id.choices = despesas_vis

    if not form.is_submitted():
        if not form.custos_operacionais.entries:
            form.custos_operacionais.append_entry()
            form.custos_operacionais[-1].despesa_id.choices = despesas_op
        if not form.custos_visitas.entries:
            form.custos_visitas.append_entry()
            form.custos_visitas[-1].despesa_id.choices = despesas_vis
        if not form.carregamentos.entries:
            form.carregamentos.append_entry()

    if form.validate_on_submit():
        try:
            nova_os_obj = OS(
                numero=form.numero.data,
                cliente=form.cliente.data,
                fase=form.fase.data,
                empresa=form.empresa.data,
                tipo_contrato=form.tipo_contrato.data,
                data_entrega=form.data_entrega.data,
                data_conclusao=form.data_conclusao.data,
                data_emissao=form.data_emissao.data,
                data_inicio=form.data_inicio.data,
                data_termino=form.data_termino.data,
                valor=form.valor.data,
                status=form.status.data,
                observacoes=form.observacoes.data,
                TipoLoc=form.TipoLoc.data,
                Tipo_OS=form.Tipo_OS.data,
                Modelo=form.Modelo.data,
                qtde=form.qtde.data,
                largura=form.largura.data,
                comprim=form.comprim.data,
                Pedireito=form.Pedireito.data,
                Piso=form.Piso.data,
                Acessorios=form.Acessorios.data,
                Razao=form.Razao.data,
                CNPJ=form.CNPJ.data,
                Insc=form.Insc.data,
                CEP=form.CEP.data,
                endereco=form.endereco.data,
                Bairro=form.Bairro.data,
                Cidade=form.Cidade.data,
                UF=form.UF.data,
                Segtrab=form.Segtrab.data,
                email=form.email.data,
                telefone=form.telefone.data,
                integracao=form.integracao.data,
                vendedo=form.vendedo.data,
                # Novos campos de endereço (Faturamento e Montagem)
                fat_endereco=form.fat_endereco.data,
                fat_bairro=form.fat_bairro.data,
                fat_cidade=form.fat_cidade.data,
                fat_uf=form.fat_uf.data,
                fat_cep=form.fat_cep.data,
                fat_emails=form.fat_emails.data,
                mont_endereco=form.mont_endereco.data,
                mont_bairro=form.mont_bairro.data,
                mont_cidade=form.mont_cidade.data,
                mont_uf=form.mont_uf.data,
                mont_cep=form.mont_cep.data
            )
            db.session.add(nova_os_obj)
            db.session.flush()

            for custo_form in form.custos_operacionais:
                if custo_form.despesa_id.data and custo_form.valor.data is not None:
                    custo_op = CustoOperacional(
                        os_id=nova_os_obj.id,
                        despesa_id=custo_form.despesa_id.data,
                        valor=custo_form.valor.data,
                        valor_realizado=custo_form.valor_realizado.data,
                        data=custo_form.data.data,
                        responsavel=custo_form.responsavel.data,
                        observacao=custo_form.observacao.data
                    )
                    db.session.add(custo_op)

            for custo_form in form.custos_visitas:
                if custo_form.despesa_id.data and custo_form.valor.data is not None:
                    custo_vis = CustoVisita(
                        os_id=nova_os_obj.id,
                        despesa_id=custo_form.despesa_id.data,
                        valor=custo_form.valor.data,
                        valor_realizado=custo_form.valor_realizado.data,
                        data=custo_form.data.data,
                        responsavel=custo_form.responsavel.data,
                        observacao=custo_form.observacao.data
                    )
                    db.session.add(custo_vis)

            for carga_form in form.carregamentos:
                if carga_form.placa_caminhao.data or carga_form.documento_referencia.data:
                    carga = Carregamento(
                        os_id=nova_os_obj.id,
                        data=carga_form.data.data,
                        placa_caminhao=carga_form.placa_caminhao.data,
                        documento_referencia=carga_form.documento_referencia.data,
                        observacao=carga_form.observacao.data
                    )
                    db.session.add(carga)

            db.session.commit()
            flash(f'OS "{nova_os_obj.numero}" criada com sucesso!', 'success')
            return redirect(url_for('lista_os'))

        except Exception as e:
            db.session.rollback()
            print(f"Erro detalhado ao salvar OS: {e}")
            flash(f'Erro ao criar OS: {e}', 'danger')

    return render_template('os_form.html', form=form, title="Nova Ordem de Serviço", despesas_op=despesas_op, despesas_vis=despesas_vis)

@app.route('/os/<int:os_id>/visualizar')
@login_required
def visualizar_os(os_id):
    os_obj = OS.query.options(
        db.joinedload(OS.custos_operacionais).joinedload(CustoOperacional.despesa),
        db.joinedload(OS.custos_visitas).joinedload(CustoVisita.despesa),
        db.joinedload(OS.versoes),
        db.joinedload(OS.carregamentos)
    ).get_or_404(os_id)
    return render_template('visualizar_os.html', os=os_obj, title=f"Detalhes da OS {os_obj.numero}")

@app.route('/os/<int:os_id>/imprimir')
@login_required
def imprimir_os(os_id):
    os_obj = OS.query.options(
        db.joinedload(OS.custos_operacionais).joinedload(CustoOperacional.despesa),
        db.joinedload(OS.custos_visitas).joinedload(CustoVisita.despesa),
        db.joinedload(OS.carregamentos)
    ).get_or_404(os_id)
    total_op = sum(c.valor for c in os_obj.custos_operacionais)
    total_vis = sum(c.valor for c in os_obj.custos_visitas)
    return render_template('imprimir_os.html', os=os_obj, total_op=total_op, total_vis=total_vis)

@app.route('/os/<int:os_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_os(os_id):
    os_obj = OS.query.get_or_404(os_id)

    if request.method == 'POST':
        form = OSForm(request.form, obj=os_obj)
    else:
        form = OSForm(obj=os_obj)
        if not form.carregamentos.entries:
            form.carregamentos.append_entry()

    despesas_op = [(d.id, d.descricao) for d in Despesa.query.filter_by(tipo='Operacional').order_by(Despesa.descricao).all()]
    despesas_vis = [(d.id, d.descricao) for d in Despesa.query.filter_by(tipo='Visita').order_by(Despesa.descricao).all()]

    for custo_op_entry in form.custos_operacionais:
        custo_op_entry.despesa_id.choices = despesas_op
    for custo_vis_entry in form.custos_visitas:
        custo_vis_entry.despesa_id.choices = despesas_vis

    if form.validate_on_submit():
        try:
            # === Snapshot Removido daqui, só gera no botão específico ===
            # usuario = current_user.username if current_user.is_authenticated else "Sistema"
            # criar_snapshot_os(os_obj, usuario, "Alteração via Edição")

            # === SEGREGACAO DE FUNÇÕES (COMPRAS vs GERAL) ===
            # Se tiver permissão 'can_edit_general' (Admin/Gerente), edita tudo.
            if current_user.can_edit_general:
                os_obj.numero = form.numero.data
                os_obj.cliente = form.cliente.data
                os_obj.fase = form.fase.data
                os_obj.empresa = form.empresa.data
                os_obj.tipo_contrato = form.tipo_contrato.data
                os_obj.data_entrega = form.data_entrega.data
                os_obj.data_conclusao = form.data_conclusao.data
                os_obj.data_emissao = form.data_emissao.data
                os_obj.data_inicio = form.data_inicio.data
                os_obj.data_termino = form.data_termino.data
                os_obj.valor = form.valor.data
                os_obj.TipoLoc = form.TipoLoc.data
                os_obj.Tipo_OS = form.Tipo_OS.data
                os_obj.Modelo = form.Modelo.data
                os_obj.qtde = form.qtde.data
                os_obj.largura = form.largura.data
                os_obj.comprim = form.comprim.data
                os_obj.Pedireito = form.Pedireito.data
                os_obj.Piso = form.Piso.data
                os_obj.Acessorios = form.Acessorios.data
                os_obj.Razao = form.Razao.data
                os_obj.CNPJ = form.CNPJ.data
                os_obj.Insc = form.Insc.data
                os_obj.CEP = form.CEP.data
                os_obj.endereco = form.endereco.data
                os_obj.Bairro = form.Bairro.data
                os_obj.Cidade = form.Cidade.data
                os_obj.UF = form.UF.data
                os_obj.Segtrab = form.Segtrab.data
                os_obj.email = form.email.data
                os_obj.telefone = form.telefone.data
                os_obj.integracao = form.integracao.data
                os_obj.vendedo = form.vendedo.data

                # Endereços Extras
                os_obj.fat_endereco = form.fat_endereco.data
                os_obj.fat_bairro = form.fat_bairro.data
                os_obj.fat_cidade = form.fat_cidade.data
                os_obj.fat_uf = form.fat_uf.data
                os_obj.fat_cep = form.fat_cep.data
                os_obj.fat_emails = form.fat_emails.data
                os_obj.mont_endereco = form.mont_endereco.data
                os_obj.mont_bairro = form.mont_bairro.data
                os_obj.mont_cidade = form.mont_cidade.data
                os_obj.mont_uf = form.mont_uf.data
                os_obj.mont_cep = form.mont_cep.data

            # === Campos que TODOS (incluindo Compras) podem editar ===
            os_obj.status = form.status.data
            os_obj.observacoes = form.observacoes.data
            os_obj.Obs2 = form.Obs2.data

            # === Atualiza Listas (Custos são liberados para Compras) ===
            CustoOperacional.query.filter_by(os_id=os_obj.id).delete()
            CustoVisita.query.filter_by(os_id=os_obj.id).delete()

            # Carregamento (Logística) só para quem tem acesso geral
            if current_user.can_edit_general:
                Carregamento.query.filter_by(os_id=os_obj.id).delete()

            db.session.flush()

            for f in form.custos_operacionais:
                if f.despesa_id.data and f.valor.data is not None:
                    db.session.add(CustoOperacional(
                        os_id=os_obj.id,
                        despesa_id=f.despesa_id.data,
                        valor=f.valor.data,
                        valor_realizado=f.valor_realizado.data,
                        data=f.data.data,
                        responsavel=f.responsavel.data,
                        observacao=f.observacao.data
                    ))

            for f in form.custos_visitas:
                if f.despesa_id.data and f.valor.data is not None:
                    db.session.add(CustoVisita(
                        os_id=os_obj.id,
                        despesa_id=f.despesa_id.data,
                        valor=f.valor.data,
                        valor_realizado=f.valor_realizado.data,
                        data=f.data.data,
                        responsavel=f.responsavel.data,
                        observacao=f.observacao.data
                    ))

            if current_user.can_edit_general:
                for carga_form in form.carregamentos:
                    if carga_form.placa_caminhao.data or carga_form.documento_referencia.data:
                        db.session.add(Carregamento(
                            os_id=os_obj.id,
                            data=carga_form.data.data,
                            placa_caminhao=carga_form.placa_caminhao.data,
                            documento_referencia=carga_form.documento_referencia.data,
                            observacao=carga_form.observacao.data
                        ))

            db.session.commit()
            flash(f'OS "{os_obj.numero}" atualizada com sucesso!', 'success')
            return redirect(url_for('lista_os'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar OS: {e}', 'danger')
            print(f"Erro ao editar OS {os_id}: {e}")

    return render_template('os_form.html', form=form, title=f"Editar OS {os_obj.numero}", despesas_op=despesas_op, despesas_vis=despesas_vis)

@app.route('/os/<int:os_id>/nova_revisao', methods=['POST'])
@login_required
def gerar_revisao(os_id):
    # Proteção: Apenas quem pode editar geral (Admin/Gerente) pode fechar versão
    if not current_user.can_edit_general:
        flash("Acesso Negado: Apenas Gerentes podem fechar versões.", "danger")
        return redirect(url_for('visualizar_os', os_id=os_id))

    os_obj = OS.query.get_or_404(os_id)
    motivo = request.form.get('motivo', 'Atualização Manual')
    try:
        usuario = current_user.username
        criar_snapshot_os(os_obj, usuario, motivo)
        db.session.commit()
        flash(f'Revisão {os_obj.revisao - 1} salva no histórico!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao gerar revisão: {e}', 'danger')
    return redirect(url_for('visualizar_os', os_id=os_id))

# --- ROTA QUE ESTAVA FALTANDO: CRONOGRAMA ---
@app.route('/cronograma')
@login_required
def cronograma():
    ordens = OS.query.filter(
        OS.fase == 'OS',
        OS.data_inicio.isnot(None),
        OS.data_termino.isnot(None)
    ).all()

    opcoes_empresas = sorted(list(set([os.empresa for os in ordens if os.empresa])))
    opcoes_tipo_os = sorted(list(set([os.Tipo_OS for os in ordens if os.Tipo_OS])))
    
    # Tratamento seguro para tipo_contrato (pode ser None)
    contratos = [os.tipo_contrato for os in ordens if os.tipo_contrato]
    opcoes_contratos = sorted(list(set(contratos)))

    tarefas_gantt = []
    for os_obj in ordens:
        cor = 'bar-blue'
        progress = 0
        if os_obj.status == 'Concluída':
            cor = 'bar-green'; progress = 100
        elif os_obj.status == 'Em Andamento':
            cor = 'bar-orange'; progress = 50
        elif os_obj.status == 'Cancelada':
            cor = 'bar-red'; progress = 100

        tipo_destaque = f"[{os_obj.Tipo_OS.upper()}]" if os_obj.Tipo_OS else "[OS]"
        nome_tarefa = f"{tipo_destaque} {os_obj.cliente} (#{os_obj.numero})"

        tarefas_gantt.append({
            'id': str(os_obj.id),
            'name': nome_tarefa,
            'start': os_obj.data_inicio.strftime('%Y-%m-%d'),
            'end': os_obj.data_termino.strftime('%Y-%m-%d'),
            'progress': progress,
            'custom_class': cor,
            '_empresa': os_obj.empresa or '',
            '_tipo_os': os_obj.Tipo_OS or '',
            '_contrato': os_obj.tipo_contrato or ''
        })

    return render_template('gantt.html',
                           tarefas=json.dumps(tarefas_gantt),
                           title="Cronograma Geral",
                           opcoes_empresas=opcoes_empresas,
                           opcoes_tipo_os=opcoes_tipo_os,
                           opcoes_contratos=opcoes_contratos)

# ==============================================================================
# ROTAS DE ORDEM DE PRODUÇÃO (OP)
# ==============================================================================

@app.route('/ordem/nova', methods=['GET', 'POST'])
@login_required
def nova_ordem():
    form = OrdemProducaoForm()
    form.os.choices = [(os_item.id, os_item.numero) for os_item in OS.query.order_by(OS.numero).all()]
    ultimo_op = OrdemProducao.query.order_by(OrdemProducao.numero_sequencial.desc()).first()
    proximo_numero = (ultimo_op.numero_sequencial + 1) if ultimo_op else 1

    if form.validate_on_submit():
        try:
            nova_op = OrdemProducao(
                numero_sequencial=proximo_numero,
                os_id=form.os.data,
                departamento=form.departamento.data,
                status=form.status.data,
                data_fechamento=form.data_fechamento.data,
                tipo_contrato=form.tipo_contrato.data,
                tipo_op=form.tipo_op.data,
                cliente=form.cliente.data,
                codigo=form.codigo.data,
                part_number_produto=form.part_number_produto.data,
                quantidade=form.quantidade.data,
                largura=form.largura.data,
                comprimento=form.comprimento.data,
                pe_direito=form.pe_direito.data,
                piso=form.piso.data,
                data_emissao=form.data_emissao.data,
                data_inicio_previsto=form.data_inicio_previsto.data,
                data_termino_previsto=form.data_termino_previsto.data,
                data_carregamento=form.data_carregamento.data,
                setor=form.setor.data,
                acessorios=form.acessorios.data,
                observacoes=form.observacoes.data
            )
            db.session.add(nova_op)
            db.session.flush()

            for item_data in form.romaneios.data:
                if item_data.get('descricao') or item_data.get('quantidade'):
                    romaneio_item = Romaneio(
                        ordem_producao_id=nova_op.id,
                        id_item=item_data.get('id_item'),
                        descricao=item_data.get('descricao'),
                        quantidade=item_data.get('quantidade'),
                        materia_prima_utilizada=item_data.get('materia_prima_utilizada')
                    )
                    db.session.add(romaneio_item)

            for item_data in form.controles_producao.data:
                if item_data.get('processo'):
                    controle_item = ControleProducao(
                        ordem_producao_id=nova_op.id,
                        departamento=item_data.get('departamento'),
                        obs_prod=item_data.get('obs_prod'),
                        turno=item_data.get('turno'),
                        processo=item_data.get('processo'),
                        maquina=item_data.get('maquina'),
                        operador=item_data.get('operador'),
                        data_inicio=item_data.get('data_inicio'),
                        hora_inicio=item_data.get('hora_inicio'),
                        data_pausa=item_data.get('data_pausa'),
                        motivo_pausa=item_data.get('motivo_pausa'),
                        data_termino=item_data.get('data_termino'),
                        hora_termino=item_data.get('hora_termino'),
                        qualidade=item_data.get('qualidade')
                    )
                    db.session.add(controle_item)

            db.session.commit()
            flash('Ordem de Produção criada com sucesso!', 'success')
            return redirect(url_for('lista_ordens'))

        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro ao salvar a Ordem de Produção: {e}', 'danger')
            print(f"Erro ao salvar OP: {e}")
    preencher_choices_processo(form)
    return render_template('ordem_form.html', form=form, title="Nova Ordem de Produção", proximo_numero=proximo_numero)

@app.route('/ordens')
@login_required
def lista_ordens():
    query = request.args.get('q', '')
    ordens_query = OrdemProducao.query
    if query:
        search_term = f"%{query}%"
        ordens_query = ordens_query.filter(OrdemProducao.cliente.ilike(search_term))
    ordens = ordens_query.order_by(OrdemProducao.numero_sequencial.desc()).all()
    return render_template('lista_ordens.html', ordens=ordens, title="Ordens de Produção", query=query)

@app.route('/ordem/<int:ordem_id>/visualizar')
@login_required
def visualizar_ordem(ordem_id):
    ordem = OrdemProducao.query.get_or_404(ordem_id)
    return render_template('visualizar_ordem.html', ordem=ordem, title=f"Detalhes da OP {ordem.numero_sequencial}")

@app.route('/ordem/<int:ordem_id>/imprimir')
@login_required
def imprimir_ordem(ordem_id):
    ordem = OrdemProducao.query.options(
        db.joinedload(OrdemProducao.os),
        db.joinedload(OrdemProducao.romaneios),
        db.joinedload(OrdemProducao.controles_producao)
    ).get_or_404(ordem_id)

    produto_descricao = "Produto não encontrado"
    if ordem.part_number_produto:
        produto = Produto.query.filter_by(part_number=ordem.part_number_produto).first()
        if produto:
            produto_descricao = produto.descricao
        else:
            produto_descricao = "Sem descrição cadastrada"
    else:
        produto_descricao = "-"

    total_segundos = 0
    for item in ordem.controles_producao:
        if item.data_inicio and item.hora_inicio and item.data_termino and item.hora_termino:
            try:
                inicio = datetime.combine(item.data_inicio, item.hora_inicio)
                fim = datetime.combine(item.data_termino, item.hora_termino)
                diferenca = fim - inicio
                segundos = diferenca.total_seconds()
                if segundos < 0: segundos = 0
                total_segundos += segundos
                horas = int(segundos // 3600)
                minutos = int((segundos % 3600) // 60)
                item.duracao_formatada = f"{horas:02d}:{minutos:02d}"
            except:
                item.duracao_formatada = "-"
        else:
            item.duracao_formatada = "-"

    total_horas = int(total_segundos // 3600)
    total_minutos = int((total_segundos % 3600) // 60)
    total_formatado = f"{total_horas:02d}:{total_minutos:02d}"

    return render_template('impressao_ordem.html',
                           ordem=ordem,
                           total_horas_gastas=total_formatado,
                           produto_descricao=produto_descricao)

@app.route('/ordem/<int:ordem_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_ordem(ordem_id):
    ordem = OrdemProducao.query.get_or_404(ordem_id)
    if request.method == 'POST':
        form = OrdemProducaoForm(request.form)
    else:
        form = OrdemProducaoForm(obj=ordem)

    form.os.choices = [(os_item.id, os_item.numero) for os_item in OS.query.order_by(OS.numero).all()]
    preencher_choices_processo(form)

    if form.validate_on_submit():
        try:
            ordem.os_id = form.os.data
            ordem.departamento = form.departamento.data
            ordem.status = form.status.data
            ordem.data_fechamento = form.data_fechamento.data
            ordem.tipo_contrato = form.tipo_contrato.data
            ordem.tipo_op = form.tipo_op.data
            ordem.cliente = form.cliente.data
            ordem.codigo = form.codigo.data
            ordem.part_number_produto = form.part_number_produto.data
            ordem.quantidade = form.quantidade.data
            ordem.largura = form.largura.data
            ordem.comprimento = form.comprimento.data
            ordem.pe_direito = form.pe_direito.data
            ordem.piso = form.piso.data
            ordem.data_emissao = form.data_emissao.data
            ordem.data_inicio_previsto = form.data_inicio_previsto.data
            ordem.data_termino_previsto = form.data_termino_previsto.data
            ordem.data_carregamento = form.data_carregamento.data
            ordem.setor = form.setor.data
            ordem.acessorios = form.acessorios.data
            ordem.observacoes = form.observacoes.data

            Romaneio.query.filter_by(ordem_producao_id=ordem.id).delete()
            ControleProducao.query.filter_by(ordem_producao_id=ordem.id).delete()
            db.session.flush()

            for item_data in form.romaneios.data:
                if item_data.get('descricao') or item_data.get('quantidade'):
                    item_data.pop('csrf_token', None)
                    romaneio_item = Romaneio(ordem_producao_id=ordem.id, **item_data)
                    db.session.add(romaneio_item)

            for item_data in form.controles_producao.data:
                 if item_data.get('processo'):
                    item_data.pop('csrf_token', None)
                    controle_item = ControleProducao(ordem_producao_id=ordem.id, **item_data)
                    db.session.add(controle_item)

            db.session.commit()
            flash('Ordem de Produção atualizada com sucesso!', 'success')
            return redirect(url_for('lista_ordens'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar a Ordem de Produção: {e}', 'danger')
            print(f"Erro ao editar OP {ordem_id}: {e}")

    return render_template('ordem_form.html', form=form, ordem=ordem, title=f"Editar OP {ordem.numero_sequencial}")

# ==============================================================================
# ROTAS DE USUÁRIOS (ADMIN)
# ==============================================================================

@app.route('/usuarios')
@login_required
@role_required('admin')
def lista_usuarios():
    users = User.query.all()
    return render_template('lista_usuarios.html', users=users, title="Gerenciar Equipe")

@app.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def novo_usuario():
    form = UserForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Erro: Este usuário já existe.', 'danger')
        else:
            if not form.password.data:
                flash('Senha é obrigatória para novos usuários.', 'warning')
            else:
                user = User(username=form.username.data, role=form.role.data)
                user.set_password(form.password.data)
                db.session.add(user)
                db.session.commit()
                flash(f'Usuário "{user.username}" criado!', 'success')
                return redirect(url_for('lista_usuarios'))
    return render_template('usuario_form.html', form=form, title="Novo Usuário")

@app.route('/usuarios/<int:user_id>/editar', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def editar_usuario(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.role = form.role.data
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash('Usuário atualizado.', 'success')
        return redirect(url_for('lista_usuarios'))
    return render_template('usuario_form.html', form=form, title=f"Editar {user.username}")

@app.route('/usuarios/<int:user_id>/excluir', methods=['POST'])
@login_required
@role_required('admin')
def excluir_usuario(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Você não pode se excluir!', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('Usuário excluído.', 'success')
    return redirect(url_for('lista_usuarios'))

# ==============================================================================
# ROTAS DE PRODUTOS E MANUTENÇÃO
# ==============================================================================

@app.route('/produtos')
@login_required
def lista_produtos():
    query = request.args.get('q', '')
    produtos_query = Produto.query
    if query:
        search_term = f"%{query}%"
        produtos_query = produtos_query.filter(or_(Produto.part_number.ilike(search_term), Produto.sku.ilike(search_term), Produto.descricao.ilike(search_term)))
    produtos = produtos_query.order_by(Produto.part_number).all()
    return render_template('lista_produtos.html', produtos=produtos, title="Lista de Produtos", query=query)

@app.route('/produtos/novo', methods=['GET', 'POST'])
@login_required
def novo_produto():
    form = ProdutoForm()
    if form.validate_on_submit():
        try:
            novo_prod = Produto(part_number=form.part_number.data, sku=form.sku.data, descricao=form.descricao.data, tipo_de_material=form.tipo_de_material.data, custo=form.custo.data)
            db.session.add(novo_prod)
            db.session.commit()
            flash(f'Produto "{novo_prod.part_number}" criado com sucesso!', 'success')
            return redirect(url_for('lista_produtos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar produto: {e}', 'danger')
    return render_template('produto_form.html', form=form, title="Novo Produto")

@app.route('/produtos/<int:produto_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_produto(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    if request.method == 'POST': form = ProdutoForm(request.form)
    else: form = ProdutoForm(obj=produto)
    if form.validate_on_submit():
        try:
            if form.part_number.data != produto.part_number:
                if Produto.query.filter_by(part_number=form.part_number.data).first():
                    flash('Erro: Part Number já existe.', 'danger')
                    return render_template('produto_form.html', form=form, title=f"Editar Produto {produto.part_number}")
            form.populate_obj(produto)
            db.session.commit()
            flash(f'Produto "{produto.part_number}" atualizado com sucesso!', 'success')
            return redirect(url_for('lista_produtos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao editar produto: {e}', 'danger')
    return render_template('produto_form.html', form=form, title=f"Editar Produto {produto.part_number}")

@app.route('/api/os/info')
@login_required
def os_info():
    os_id = request.args.get('os_id')
    if not os_id: return jsonify({'error': 'OS ID não fornecido'}), 400
    os_data = OS.query.get(os_id)
    if os_data: return jsonify({'cliente': os_data.cliente})
    else: return jsonify({'error': 'OS não encontrada'}), 404

@app.route('/api/produto/info')
@login_required
def produto_info():
    part_number_query = request.args.get('part_number', '')
    if not part_number_query: return jsonify({'error': 'Part number não fornecido'}), 400
    produto = Produto.query.filter_by(part_number=part_number_query).first()
    if produto: return jsonify(produto.to_dict())
    else: return jsonify({'error': 'Produto não encontrado'}), 404

@app.route('/api/produtos/search')
@login_required
def search_produtos():
    query = request.args.get('q', '')
    if not query: return jsonify([])
    search_term = f"%{query}%"
    produtos = Produto.query.filter(or_(Produto.part_number.ilike(search_term), Produto.sku.ilike(search_term), Produto.descricao.ilike(search_term))).order_by(Produto.part_number).limit(50).all()
    return jsonify([p.to_dict() for p in produtos])

@app.route('/manutencao/nova', methods=['GET', 'POST'])
@login_required
def nova_manutencao():
    form = OSManutencaoForm()
    ultimo_os = OSManutencao.query.order_by(OSManutencao.id.desc()).first()
    proximo_numero = str(int(ultimo_os.numero) + 1) if ultimo_os and ultimo_os.numero.isdigit() else "1"
    if form.validate_on_submit():
        try:
            nova_os = OSManutencao(numero=proximo_numero, data_abertura=form.data_abertura.data, hora_abert=form.hora_abert.data, solicitante=form.solicitante.data, area_setor=form.area_setor.data, maq_equip=form.maq_equip.data, ocorrencia=form.ocorrencia.data, parada=form.parada.data, manut_corretiva=form.manut_corretiva.data, manut_preventiva=form.manut_preventiva.data, manut_preditiva=form.manut_preditiva.data, inspecao=form.inspecao.data, melhorias=form.melhorias.data, predial=form.predial.data, outro=form.outro.data, sintoma=form.sintoma.data, causa=form.causa.data, intervencao=form.intervencao.data, materiais_utilizados=form.materiais_utilizados.data, materiais_comprados=form.materiais_comprados.data, ficha_tec=form.ficha_tec.data, obs_manut=form.obs_manut.data, assinatura1=form.assinatura1.data, assinatura2=form.assinatura2.data, data_encerramento=form.data_encerramento.data)
            db.session.add(nova_os)
            db.session.flush()
            for apontamento_data in form.apontamentos.data:
                if apontamento_data.get('manutentor'):
                    apontamento_data.pop('csrf_token', None)
                    apontamento = ManutApont(os_manutencao_id=nova_os.id, manutentor=apontamento_data['manutentor'], data_inicio=apontamento_data.get('data_inicio'), hora_inicio=apontamento_data.get('hora_inicio'), data_termino=apontamento_data.get('data_termino'), hora_termino=apontamento_data.get('hora_termino'))
                    db.session.add(apontamento)
            db.session.commit()
            flash(f'OS Manutenção Nº {nova_os.numero} criada com sucesso!', 'success')
            return redirect(url_for('lista_manutencao'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar OS Manutenção: {e}', 'danger')
    preencher_choices_maquina(form)
    return render_template('os_manutencao_form.html', form=form, title="Nova OS de Manutenção", proximo_numero=proximo_numero, maquinas_map=MAQUINAS_POR_SETOR)

@app.route('/manutencao/<int:os_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_manutencao(os_id):
    os_obj = OSManutencao.query.get_or_404(os_id)
    if request.method == 'POST': form = OSManutencaoForm(request.form, obj=os_obj)
    else: form = OSManutencaoForm(obj=os_obj)
    preencher_choices_maquina(form)
    if form.validate_on_submit():
        try:
            os_obj.numero=form.numero.data; os_obj.data_abertura=form.data_abertura.data; os_obj.hora_abert=form.hora_abert.data; os_obj.solicitante=form.solicitante.data; os_obj.area_setor=form.area_setor.data; os_obj.maq_equip=form.maq_equip.data; os_obj.ocorrencia=form.ocorrencia.data; os_obj.parada=form.parada.data; os_obj.manut_corretiva=form.manut_corretiva.data; os_obj.manut_preventiva=form.manut_preventiva.data; os_obj.manut_preditiva=form.manut_preditiva.data; os_obj.inspecao=form.inspecao.data; os_obj.melhorias=form.melhorias.data; os_obj.predial=form.predial.data; os_obj.outro=form.outro.data; os_obj.sintoma=form.sintoma.data; os_obj.causa=form.causa.data; os_obj.intervencao=form.intervencao.data; os_obj.materiais_utilizados=form.materiais_utilizados.data; os_obj.materiais_comprados=form.materiais_comprados.data; os_obj.ficha_tec=form.ficha_tec.data; os_obj.obs_manut=form.obs_manut.data; os_obj.assinatura1=form.assinatura1.data; os_obj.assinatura2=form.assinatura2.data; os_obj.data_encerramento=form.data_encerramento.data
            ManutApont.query.filter_by(os_manutencao_id=os_obj.id).delete()
            db.session.flush()
            for apontamento_data in form.apontamentos.data:
                if apontamento_data.get('manutentor'):
                    apontamento_data.pop('csrf_token', None)
                    apontamento = ManutApont(os_manutencao_id=os_obj.id, manutentor=apontamento_data['manutentor'], data_inicio=apontamento_data.get('data_inicio'), hora_inicio=apontamento_data.get('hora_inicio'), data_termino=apontamento_data.get('data_termino'), hora_termino=apontamento_data.get('hora_termino'))
                    db.session.add(apontamento)
            db.session.commit()
            flash(f'OS Manutenção Nº {os_obj.numero} atualizada com sucesso!', 'success')
            return redirect(url_for('lista_manutencao'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao editar OS Manutenção: {e}', 'danger')
    return render_template('os_manutencao_form.html', form=form, os_obj=os_obj, title=f"Editar OS Manutenção {os_obj.numero}", maquinas_map=MAQUINAS_POR_SETOR)

@app.route('/manutencao')
@login_required
def lista_manutencao():
    todas_as_os = OSManutencao.query.order_by(OSManutencao.data_abertura.desc()).all()
    return render_template('lista_manutencao.html', lista_os=todas_as_os, title="Ordens de Serviço de Manutenção")

@app.route('/manutencao/<int:os_id>/visualizar')
@login_required
def visualizar_manutencao(os_id):
    os_manut = OSManutencao.query.options(db.joinedload(OSManutencao.apontamentos)).get_or_404(os_id)
    parada_status = 'Sim' if os_manut.parada == 'Sim' else 'Não'
    total_segundos = 0
    for item in os_manut.apontamentos:
        if item.data_inicio and item.hora_inicio and item.data_termino and item.hora_termino:
            try:
                inicio = datetime.combine(item.data_inicio, item.hora_inicio)
                fim = datetime.combine(item.data_termino, item.hora_termino)
                diferenca = fim - inicio
                segundos = diferenca.total_seconds()
                if segundos < 0: segundos = 0
                total_segundos += segundos
                horas = int(segundos // 3600); minutos = int((segundos % 3600) // 60)
                item.duracao_formatada = f"{horas:02d}:{minutos:02d}"
            except: item.duracao_formatada = "-"
        else: item.duracao_formatada = "-"
    total_horas = int(total_segundos // 3600); total_minutos = int((total_segundos % 3600) // 60)
    total_horas_gastas = f"{total_horas:02d}:{total_minutos:02d}"
    return render_template('visualizar_manutencao.html', os_manut=os_manut, parada_status=parada_status, total_horas_gastas=total_horas_gastas, title=f"Detalhes da OS {os_manut.numero}")

@app.route('/manutencao/<int:os_id>/imprimir')
@login_required
def imprimir_manutencao(os_id):
    os_manut = OSManutencao.query.options(db.joinedload(OSManutencao.apontamentos)).get_or_404(os_id)
    parada_status = 'Sim' if os_manut.parada == 'Sim' else 'Não'
    total_segundos = 0
    for item in os_manut.apontamentos:
        if item.data_inicio and item.hora_inicio and item.data_termino and item.hora_termino:
            try:
                inicio = datetime.combine(item.data_inicio, item.hora_inicio)
                fim = datetime.combine(item.data_termino, item.hora_termino)
                diferenca = fim - inicio
                segundos = diferenca.total_seconds()
                if segundos < 0: segundos = 0
                total_segundos += segundos
                horas = int(segundos // 3600); minutos = int((segundos % 3600) // 60)
                item.duracao_formatada = f"{horas:02d}:{minutos:02d}"
            except: item.duracao_formatada = "-"
        else: item.duracao_formatada = "-"
    total_horas = int(total_segundos // 3600); total_minutos = int((total_segundos % 3600) // 60)
    total_horas_gastas = f"{total_horas:02d}:{total_minutos:02d}"
    return render_template('imprimir_manutencao.html', os_manut=os_manut, parada_status=parada_status, total_horas_gastas=total_horas_gastas)

@app.route('/manutencao/<int:os_id>/excluir', methods=['POST'])
@login_required
@role_required('admin')
def excluir_manutencao(os_id):
    os_obj = OSManutencao.query.get_or_404(os_id)
    try:
        db.session.delete(os_obj)
        db.session.commit()
        flash(f'OS Manutenção Nº {os_obj.numero} excluída com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir a OS: {e}', 'danger')
    return redirect(url_for('lista_manutencao'))

# =============================================================
# ROTAS DE DESPESAS
# =============================================================
@app.route('/despesas')
@login_required
def lista_despesas():
    despesas = Despesa.query.order_by(Despesa.tipo, Despesa.descricao).all()
    return render_template('lista_despesas.html', despesas=despesas, title="Tipos de Despesa")

@app.route('/despesas/nova', methods=['GET', 'POST'])
@login_required
def nova_despesa():
    form = DespesaForm()
    if form.validate_on_submit():
        try:
            existente = Despesa.query.filter(Despesa.descricao.ilike(form.descricao.data)).first()
            if existente: flash(f'Erro: A despesa "{form.descricao.data}" já existe.', 'warning')
            else:
                nova = Despesa(descricao=form.descricao.data, tipo=form.tipo.data)
                db.session.add(nova); db.session.commit()
                flash(f'Despesa "{form.descricao.data}" criada com sucesso!', 'success')
                return redirect(url_for('lista_despesas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar despesa: {e}.', 'danger')
    return render_template('despesa_form.html', form=form, title="Nova Despesa")

# =============================================================
# MÓDULO DE COMPRAS - CADASTROS (NOVAS FUNCIONALIDADES)
# =============================================================

# --- ROTA PARA GERENCIAR TIPOS DE FORNECEDOR ---
@app.route('/configuracoes/tipos-fornecedor', methods=['GET', 'POST'])
@login_required
def gerenciar_tipos_fornecedor():
    form = TipoFornecedorForm()
    if form.validate_on_submit():
        novo_tipo = TipoFornecedor(descricao=form.descricao.data)
        db.session.add(novo_tipo)
        db.session.commit()
        flash('Novo tipo de fornecedor cadastrado!', 'success')
        return redirect(url_for('gerenciar_tipos_fornecedor'))
    
    tipos = TipoFornecedor.query.order_by(TipoFornecedor.descricao).all()
    return render_template('lista_tipos_fornecedor.html', form=form, tipos=tipos)

# --- ROTAS DE FORNECEDOR ---

@app.route('/fornecedores')
@login_required
def lista_fornecedores():
    fornecedores = Fornecedor.query.order_by(Fornecedor.razao_social).all()
    return render_template('lista_fornecedores.html', fornecedores=fornecedores)

@app.route('/fornecedor/novo', methods=['GET', 'POST'])
@login_required
def novo_fornecedor():
    form = FornecedorForm()
    
    # POPULAR O SELECT FIELD COM DADOS DO BANCO
    form.tipo_fornecedor_id.choices = [(t.id, t.descricao) for t in TipoFornecedor.query.order_by(TipoFornecedor.descricao).all()]
    form.tipo_fornecedor_id.choices.insert(0, (0, 'Selecione um tipo...'))

    if form.validate_on_submit():
        if form.tipo_fornecedor_id.data == 0:
            flash('Selecione um tipo válido.', 'danger')
        else:
            novo = Fornecedor(
                cod_sap=form.cod_sap.data,
                razao_social=form.razao_social.data,
                nome_fantasia=form.nome_fantasia.data,
                tipo_fornecedor_id=form.tipo_fornecedor_id.data,
                documento=form.documento.data,
                inscricao_estadual=form.inscricao_estadual.data,
                email=form.email.data,
                telefone=form.telefone.data,
                endereco=form.endereco.data,
                bairro=form.bairro.data,
                cep=form.cep.data,
                cidade=form.cidade.data,
                uf=form.uf.data,
                pais=form.pais.data
            )
            db.session.add(novo)
            db.session.commit()
            flash('Fornecedor cadastrado com sucesso!', 'success')
            return redirect(url_for('lista_fornecedores'))
            
    return render_template('editar_fornecedor.html', form=form, titulo='Novo Fornecedor')

@app.route('/fornecedor/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_fornecedor(id):
    fornecedor = Fornecedor.query.get_or_404(id)
    form = FornecedorForm(obj=fornecedor)
    
    # POPULAR O SELECT (Igual ao cadastro)
    form.tipo_fornecedor_id.choices = [(t.id, t.descricao) for t in TipoFornecedor.query.order_by(TipoFornecedor.descricao).all()]
    
    if request.method == 'GET':
        # Pré-selecionar o valor atual
        form.tipo_fornecedor_id.data = fornecedor.tipo_fornecedor_id

    if form.validate_on_submit():
        form.populate_obj(fornecedor)
        db.session.commit()
        flash('Fornecedor atualizado!', 'success')
        return redirect(url_for('lista_fornecedores'))
        
    return render_template('editar_fornecedor.html', form=form, titulo='Editar Fornecedor')

# --- API CRÍTICA PARA O BOTÃO "+" FUNCIONAR NO MODAL ---
@app.route('/api/tipos-fornecedor/novo', methods=['POST'])
@login_required
def api_novo_tipo_fornecedor():
    data = request.get_json()
    descricao = data.get('descricao')
    
    if not descricao:
        return jsonify({'success': False, 'error': 'Descrição vazia'}), 400
        
    try:
        existe = TipoFornecedor.query.filter_by(descricao=descricao).first()
        if existe:
            return jsonify({'success': False, 'error': 'Tipo já existe'}), 400

        novo = TipoFornecedor(descricao=descricao)
        db.session.add(novo)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'id': novo.id, 
            'descricao': novo.descricao
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# =============================================================
# MÓDULO DE SOLICITAÇÕES DE COMPRA (Adicione no app.py)
# =============================================================

@app.route('/solicitacoes')
@login_required
def lista_solicitacoes():
    solicitacoes = SolicitacaoCompra.query.order_by(SolicitacaoCompra.id.desc()).all()
    return render_template('lista_solicitacoes.html', solicitacoes=solicitacoes)

@app.route('/solicitacoes/nova', methods=['GET', 'POST'])
@login_required
def nova_solicitacao():
    form = SolicitacaoCompraForm()
    
    # Se for GET e não tiver itens, adiciona um vazio para aparecer o campo
    if request.method == 'GET' and not form.itens.entries:
        form.itens.append_entry()

    if form.validate_on_submit():
        try:
            nova_sol = SolicitacaoCompra(
                user_id=current_user.id,
                observacao=form.observacao.data,
                status='Pendente'
            )
            db.session.add(nova_sol)
            db.session.flush() # Gera o ID da solicitação

            # Salvar os Itens
            for item_form in form.itens:
                if item_form.descricao_item.data and item_form.quantidade.data:
                    novo_item = SolicitacaoItem(
                        solicitacao_id=nova_sol.id,
                        produto_id=item_form.produto_id.data if item_form.produto_id.data else None,                        
                        descricao_item=item_form.descricao_item.data,
                        quantidade=item_form.quantidade.data,
                        unidade=item_form.unidade.data,
                        prioridade=item_form.prioridade.data
                    )
                    db.session.add(novo_item)
            
            db.session.commit()
            flash(f'Solicitação #{nova_sol.id} criada com sucesso!', 'success')
            return redirect(url_for('lista_solicitacoes'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar solicitação: {e}', 'danger')
            print(f"Erro Solicitação: {e}")

    return render_template('nova_solicitacao.html', form=form)

@app.route('/solicitacoes/<int:id>/visualizar')
@login_required
def visualizar_solicitacao(id):
    solicitacao = SolicitacaoCompra.query.get_or_404(id)
    return render_template('visualizar_solicitacao.html', solicitacao=solicitacao)

# =============================================================
# MÓDULO DE PEDIDOS E COTAÇÕES (Adicione ao final do app.py)
# =============================================================

@app.route('/solicitacoes/<int:solicitacao_id>/gerar_pedido', methods=['GET', 'POST'])
@login_required
def gerar_pedido(solicitacao_id):
    solicitacao = SolicitacaoCompra.query.get_or_404(solicitacao_id)
    form = PedidoCompraForm()
    
    # Preenche o Dropdown de Fornecedores
    form.fornecedor.choices = [(f.id, f.razao_social) for f in Fornecedor.query.order_by(Fornecedor.razao_social).all()]
    
    # --- MÉTODO GET: Preenche o formulário com dados da Solicitação ---
    if request.method == 'GET':
        # Se for a primeira vez abrindo, copia os itens da solicitação
        for item_sol in solicitacao.itens:
            # Adiciona uma linha no formulário para cada item
            form.itens.append_entry({
                'produto_id': item_sol.produto_id,
                'descricao': item_sol.descricao_item,
                'quantidade': item_sol.quantidade,
                'unidade': item_sol.unidade,
                'valor_unitario': Decimal('0.00') # Começa zerado para obrigar cotação
            })

    # --- MÉTODO POST: Salvar ou Aprovar ---
    if form.validate_on_submit():
        try:
            # 1. Gera número do pedido (AnoMesDia-HoraMinuto) para ser único
            num_pedido = datetime.now().strftime('%Y%m%d-%H%M%S')
            
            # 2. Calcula o Valor Total
            total_pedido = Decimal('0.00')
            for item in form.itens:
                subtotal = item.quantidade.data * item.valor_unitario.data
                total_pedido += subtotal

            # 3. Define Status Inicial
            status_pedido = 'Em Cotação' # Padrão
            data_aprov = None
            aprovador_id = None

            # 4. LÓGICA DE ALÇADA (Se clicou em "Salvar e Aprovar")
            if form.submit_aprovar.data:
                limite_alcada = Decimal('5000.00') # Exemplo: 5 mil reais
                eh_gerente = current_user.role in ['admin', 'gerente']
                
                if total_pedido > limite_alcada and not eh_gerente:
                    flash(f'Valor R$ {total_pedido:,.2f} excede sua alçada. Pedido salvo como "Aguardando Aprovação".', 'warning')
                    status_pedido = 'Aguardando Aprovação'
                else:
                    status_pedido = 'Aprovado'
                    data_aprov = datetime.now()
                    aprovador_id = current_user.id
                    flash('Pedido Aprovado com sucesso!', 'success')

            # 5. Salva no Banco
            novo_pedido = PedidoCompra(
                numero_pedido=num_pedido,
                solicitacao_origem_id=solicitacao.id,
                fornecedor_id=form.fornecedor.data,
                condicao_pagamento=form.condicao_pagamento.data,
                prazo_entrega=form.prazo_entrega.data,
                observacoes=form.observacoes.data,
                valor_total=total_pedido,
                status=status_pedido,
                aprovado_por_id=aprovador_id,
                data_aprovacao=data_aprov
            )
            db.session.add(novo_pedido)
            db.session.flush()

            # 6. Salva os Itens do Pedido
            for item_form in form.itens:
                total_item = item_form.quantidade.data * item_form.valor_unitario.data
                db.session.add(PedidoItem(
                    pedido_id=novo_pedido.id,
                    descricao=item_form.descricao.data,
                    quantidade=item_form.quantidade.data,
                    valor_unitario=item_form.valor_unitario.data,
                    valor_total_item=total_item
                ))
            
            # 7. Atualiza a Solicitação original
            solicitacao.status = 'Em Pedido'
            
            db.session.commit()
            return redirect(url_for('lista_solicitacoes')) # Depois mudaremos para lista de pedidos

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao gerar pedido: {e}', 'danger')
            print(e)

    return render_template('novo_pedido.html', form=form, solicitacao=solicitacao)


# ==============================================================================
# COMANDOS CLI
# ==============================================================================

@app.cli.command('create-db')
def create_db_command():
    with app.app_context():
        try:
            db.create_all()
            print('Banco de dados e tabelas criados/atualizados com sucesso!')
        except Exception as e: print(f"Erro ao criar tabelas: {e}")

@app.cli.command('create-user')
def create_user_command():
    username = 'admin'
    password = '123'
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user: print(f'Usuário "{username}" já existe.')
        else:
            try:
                new_user = User(username=username)
                new_user.set_password(password)
                new_user.role = 'admin'
                db.session.add(new_user)
                db.session.commit()
                print(f'Usuário "{username}" criado com sucesso!')
            except Exception as e:
                db.session.rollback()
                print(f"Erro ao criar usuário: {e}")

@app.cli.command('seed-tipos')
def seed_tipos():
    """Popula a tabela de tipos de fornecedor com os dados padrão."""
    lista_padrao = [
        'Fabricante e Distribuidor (Matéria Prima/Material de Processo)',
        'Fabricante e Distribuidor (Comércio Varejista, Revenda e Distribuição - MRO)',
        'Prestador de Serviço (Ambiente Externo)',
        'Prestador de Serviço (Ambiente Interno)',
        'Prestador de Serviço Específico de Advocacia/Treinamento/Consultoria',
        'Prestador de Serviço Pessoa Física',
        'Prestador de Serviço de Controle de Pragas e Vetores',
        'Locação sem Mão de Obra',
        'Fornecedor de Produtos Químicos Controlados',
        'Tratamento e Destinação de Resíduos',
        'Transportador - Cargas/Resíduos Perigosos',
        'Transportador - Interestadual Perigosos',
        'Transportador - Resíduos Não Perigosos',
        'Transportador - Cargas Não Perigosas'
    ]
    with app.app_context():
        # Verifica se a tabela existe antes de inserir
        try:
            for item in lista_padrao:
                existe = TipoFornecedor.query.filter_by(descricao=item).first()
                if not existe:
                    db.session.add(TipoFornecedor(descricao=item))
            db.session.commit()
            print("Tipos de fornecedor cadastrados com sucesso!")
        except Exception as e:
            print(f"Erro ao popular tipos: {e}")

@app.cli.command('import-products')
@click.argument('filename')
def import_products_command(filename):
    with app.app_context():
        try:
            num_deleted = db.session.query(Produto).delete()
            db.session.commit()
            if num_deleted > 0: print(f"{num_deleted} produtos antigos foram apagados.")

            with open(filename, mode='r', encoding='latin-1') as csv_file:
                header_line = csv_file.readline()
                headers = [h.strip().lower() for h in header_line.split(';')]
                print(f"Cabeçalhos detectados no CSV: {headers}")
                csv_reader = csv.DictReader(csv_file, fieldnames=headers, delimiter=';')
                products_to_add = []
                print(f"Lendo o arquivo '{filename}'...")

                for i, row in enumerate(csv_reader, start=2):
                    try:
                        part_number_val = row.get('part_number', '').strip()
                        if not part_number_val:
                            print(f"Aviso: Linha {i} sem 'part_number'. Ignorada.")
                            continue
                        sku_val = row.get('sku', '').strip() or None
                        tipo_material_val = row.get('tipo_de_material', '').strip() or None
                        descricao_val = row.get('descricao', '').strip()
                        costo_str = row.get('custo', '0').replace(',', '.').strip()
                        costo_value = Decimal(costo_str) if costo_str else Decimal('0.0')

                        product = Produto(part_number=part_number_val, sku=sku_val, descricao=descricao_val, tipo_de_material=tipo_material_val, custo=costo_value)
                        products_to_add.append(product)
                    except Exception as e:
                        print(f"Erro na linha {i}: {e}. Ignorada.")
                        continue

                if products_to_add:
                    db.session.bulk_save_objects(products_to_add)
                    db.session.commit()
                    print(f"Importação concluída! {len(products_to_add)} produtos adicionados.")
                else:
                    print("Nenhum produto válido encontrado.")

        except FileNotFoundError: print(f"Erro: Arquivo '{filename}' não encontrado.")
        except Exception as e:
            db.session.rollback()
            print(f"Erro geral na importação: {e}")
            print("Transação revertida.")

if __name__ == '__main__':
    app.run(debug=True)