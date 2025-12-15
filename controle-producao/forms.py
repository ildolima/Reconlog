from datetime import date, datetime, time, timedelta
from flask_wtf import FlaskForm
from wtforms import Form, StringField, PasswordField, BooleanField, IntegerField, DecimalField, DateField, TimeField, TextAreaField, SubmitField, FieldList, FormField, SelectField, RadioField
from wtforms.validators import DataRequired, Optional, Length, InputRequired, Email

# ==================== LISTAS DE OPÇÕES (MANUTENÇÃO - COMPLETAS) ====================
OPCOES_SINTOMAS = [
    ('', 'Selecione um Sintoma...'),
    ('Aquecimento', 'Aquecimento'),
    ('Aquecimento anormal do óleo', 'Aquecimento anormal do óleo'),
    ('Aquecimento de rolamentos / mancais', 'Aquecimento de rolamentos / mancais'),
    ('Ar-condicionado não resfria', 'Ar-condicionado não resfria'),
    ('Barreira de segurança desajustada', 'Barreira de segurança desajustada'),
    ('Bomba não funcionando', 'Bomba não funcionando'),
    ('Botão de emergência travado', 'Botão de emergência travado'),
    ('Cheiro de Queimado', 'Cheiro de Queimado'),
    ('Cheiro incomum', 'Cheiro incomum'),
    ('Cilindro não aciona', 'Cilindro não aciona'),
    ('Cilindro não movimenta', 'Cilindro não movimenta'),
    ('Conexão solta', 'Conexão solta'),
    ('Cortina de luz falhando', 'Cortina de luz falhando'),
    ('Desalinhado', 'Desalinhado'),
    ('Desarme', 'Desarme'),
    ('Display apagado', 'Display apagado'),
    ('Faisca', 'Faisca'),
    ('Falha de acesso', 'Falha de acesso'),
    ('Falha de comunicação', 'Falha de comunicação'),
    ('Filtro obstruído', 'Filtro obstruído'),
    ('Folga', 'Folga'),
    ('Fusivel Queimado', 'Fusivel Queimado'),
    ('Infiltração / goteira', 'Infiltração / goteira'),
    ('Intertravamento não funciona', 'Intertravamento não funciona'),
    ('Leitura incorreta', 'Leitura incorreta'),
    ('Lubrificação', 'Lubrificação'),
    ('Mangueira rompida', 'Mangueira rompida'),
    ('Mau contato', 'Mau contato'),
    ('Não liga', 'Não liga'),
    ('Parâmetros desconfigurados', 'Parâmetros desconfigurados'),
    ('Perda de torque', 'Perda de torque'),
    ('Piso solto / quebrado', 'Piso solto / quebrado'),
    ('Porta / janela danificada', 'Porta / janela danificada'),
    ('Pressão insuficiente', 'Pressão insuficiente'),
    ('Proteção de máquina danificada', 'Proteção de máquina danificada'),
    ('Quebra de componente', 'Quebra de componente'),
    ('Ruido anormal', 'Ruido anormal'),
    ('Ruido no sistema', 'Ruido no sistema'),
    ('Sem energia', 'Sem energia'),
    ('Sem pressao', 'Sem pressao'),
    ('Sensor não detecta', 'Sensor não detecta'),
    ('Sensor sujo / desalinhado', 'Sensor sujo / desalinhado'),
    ('Tempo de ciclo aumentado', 'Tempo de ciclo aumentado'),
    ('Tomada sem energia', 'Tomada sem energia'),
    ('Torneira ou vaso com vazamento', 'Torneira ou vaso com vazamento'),
    ('Travado', 'Travado'),
    ('Variação de tensão', 'Variação de tensão'),
    ('Vazamento de ar', 'Vazamento de ar'),
    ('Vazamento de fluido', 'Vazamento de fluido'),
    ('Vazamento de oleo / graxa', 'Vazamento de oleo / graxa'),
    ('Vibração', 'Vibração'),
    ('Válvula travando', 'Válvula travando')
]

OPCOES_CAUSAS = [
    ('', 'Selecione uma Causa...'),
    ('Acúmulo de sujeira', 'Acúmulo de sujeira'),
    ('Ajuste incorreto', 'Ajuste incorreto'),
    ('Ajuste incorreto de parâmetros', 'Ajuste incorreto de parâmetros'),
    ('Ar no sistema', 'Ar no sistema'),
    ('Aterramento inadequado', 'Aterramento inadequado'),
    ('Atuador travado', 'Atuador travado'),
    ('Batida', 'Batida'),
    ('Bomba desgastada', 'Bomba desgastada'),
    ('Cabo de sinal rompido', 'Cabo de sinal rompido'),
    ('Cabos desgastados', 'Cabos desgastados'),
    ('Cilindro desgastado', 'Cilindro desgastado'),
    ('Componente queimado (relé, contator, fusível...)', 'Componente queimado (relé, contator, fusível...)'),
    ('Configuração incorreta', 'Configuração incorreta'),
    ('Correia frouxa ou danificada', 'Correia frouxa ou danificada'),
    ('Curto-circuito', 'Curto-circuito'),
    ('Desgaste natural por tempo de uso', 'Desgaste natural por tempo de uso'),
    ('Disjuntor', 'Disjuntor'),
    ('Eixo desalinhado', 'Eixo desalinhado'),
    ('Erro de operação', 'Erro de operação'),
    ('Excesso de carga no equipamento', 'Excesso de carga no equipamento'),
    ('Falha de comunicação de rede', 'Falha de comunicação de rede'),
    ('Falha em encoder / célula de carga', 'Falha em encoder / célula de carga'),
    ('Falta de alimentação elétrica', 'Falta de alimentação elétrica'),
    ('Falta de fluido hidráulico', 'Falta de fluido hidráulico'),
    ('Falta de lubrificação', 'Falta de lubrificação'),
    ('Falta de manutenção preventiva', 'Falta de manutenção preventiva'),
    ('Falta de treinamento do operador', 'Falta de treinamento do operador'),
    ('Falta de ventilação', 'Falta de ventilação'),
    ('Filtro entupido', 'Filtro entupido'),
    ('Filtro saturado', 'Filtro saturado'),
    ('Fixação solta', 'Fixação solta'),
    ('Fluido contaminado', 'Fluido contaminado'),
    ('Inspeções não realizadas', 'Inspeções não realizadas'),
    ('Interferência eletromagnética', 'Interferência eletromagnética'),
    ('Lubrificante inadequado', 'Lubrificante inadequado'),
    ('Mau contato em conexões', 'Mau contato em conexões'),
    ('Montagem incorreta', 'Montagem incorreta'),
    ('PLC com falha / erro de programa', 'PLC com falha / erro de programa'),
    ('Painel com sujeira ou umidade', 'Painel com sujeira ou umidade'),
    ('Peça paralela / não original', 'Peça paralela / não original'),
    ('Plano de lubrificação incompleto', 'Plano de lubrificação incompleto'),
    ('Poeira excessiva', 'Poeira excessiva'),
    ('Pressão de linha insuficiente', 'Pressão de linha insuficiente'),
    ('Pressão desregulada', 'Pressão desregulada'),
    ('Procedimento não seguido', 'Procedimento não seguido'),
    ('Produtos químicos agressivos', 'Produtos químicos agressivos'),
    ('Queda de tensão / oscilação', 'Queda de tensão / oscilação'),
    ('Regulador desajustado', 'Regulador desajustado'),
    ('Rolamento danificado', 'Rolamento danificado'),
    ('Sensor sujo ou desalinhado', 'Sensor sujo ou desalinhado'),
    ('Setup inadequado', 'Setup inadequado'),
    ('Sobrecarga no circuito', 'Sobrecarga no circuito'),
    ('Sobretemperatura no óleo', 'Sobretemperatura no óleo'),
    ('Temperatura ambiente elevada', 'Temperatura ambiente elevada'),
    ('Troca de peça fora do prazo', 'Troca de peça fora do prazo'),
    ('Umidade', 'Umidade'),
    ('Utilização fora da capacidade nominal', 'Utilização fora da capacidade nominal'),
    ('Vazamento em conexões ou mangueiras', 'Vazamento em conexões ou mangueiras'),
    ('Vibrações externas', 'Vibrações externas'),
    ('Válvula emperrada por sujeira', 'Válvula emperrada por sujeira'),
    ('Válvula travada', 'Válvula travada'),
    ('Água no sistema de ar comprimido', 'Água no sistema de ar comprimido')
]

OPCOES_INTERVENCOES = [
    ('', 'Selecione uma Intervenção...'),
    ('Ajuste de componentes', 'Ajuste de componentes'),
    ('Ajuste preventivo', 'Ajuste preventivo'),
    ('Análise de vibração', 'Análise de vibração'),
    ('Aperto de conexões', 'Aperto de conexões'),
    ('Calibração de instrumentos', 'Calibração de instrumentos'),
    ('Checagem de segurança', 'Checagem de segurança'),
    ('Coleta de óleo para análise', 'Coleta de óleo para análise'),
    ('Correção de falha elétrica', 'Correção de falha elétrica'),
    ('Correção de falha hidráulica', 'Correção de falha hidráulica'),
    ('Correção de falha mecânica', 'Correção de falha mecânica'),
    ('Correção de falha pneumática', 'Correção de falha pneumática'),
    ('Desobstrução de tubulações / dutos', 'Desobstrução de tubulações / dutos'),
    ('Inspeção periódica', 'Inspeção periódica'),
    ('Limpeza técnica', 'Limpeza técnica'),
    ('Lubrificação de componentes', 'Lubrificação de componentes'),
    ('Reaperto geral', 'Reaperto geral'),
    ('Reparo emergencial', 'Reparo emergencial'),
    ('Termografia', 'Termografia'),
    ('Teste funcional', 'Teste funcional'),
    ('Troca de peças danificadas', 'Troca de peças danificadas'),
    ('Troca programada de peças', 'Troca programada de peças'),
    ('Ultrassom', 'Ultrassom'),
    ('Verificação do alinhamento', 'Verificação do alinhamento')
]

# ==================== FORMS DE AUTENTICAÇÃO E CADASTROS BÁSICOS ====================

class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')

class DespesaForm(FlaskForm):
    descricao = StringField('Descrição da Despesa', validators=[DataRequired(), Length(max=100)])
    tipo = SelectField('Tipo', choices=[('Operacional', 'Operacional'), ('Visita', 'Visita')], validators=[DataRequired()])
    submit = SubmitField('Salvar Despesa')

class ProdutoForm(FlaskForm):
    part_number = StringField('Part Number', validators=[DataRequired(), Length(max=40)])
    sku = StringField('SKU', validators=[Optional(), Length(max=8)])
    descricao = StringField('Descrição', validators=[DataRequired(), Length(max=40)])
    tipo_de_material = StringField('Tipo de Material', validators=[Optional(), Length(max=15)])
    custo = DecimalField('Custo', places=3, validators=[DataRequired()])
    submit = SubmitField('Salvar Produto')

# ==================== FORMS AUXILIARES (SUB-FORMS) ====================

class CustoOperacionalForm(FlaskForm):
    class Meta: csrf = False
    despesa_id = SelectField('Despesa Operacional', coerce=int, validators=[InputRequired()])
    valor = DecimalField('Previsto (R$)', places=2, validators=[InputRequired()])
    valor_realizado = DecimalField('Realizado (R$)', places=2, validators=[Optional()])
    data = DateField('Data', default=date.today, format='%Y-%m-%d', validators=[DataRequired()])
    responsavel = SelectField('Responsável', choices=[('Reconlog', 'Reconlog'), ('Cliente', 'Cliente'), ('NSA', 'NSA')], default='Reconlog')
    observacao = StringField('Obs', validators=[Optional(), Length(max=200)])

class CustoVisitaForm(FlaskForm):
    class Meta: csrf = False
    despesa_id = SelectField('Despesa de Visita', coerce=int, validators=[InputRequired()])
    valor = DecimalField('Previsto (R$)', places=2, validators=[InputRequired()])
    valor_realizado = DecimalField('Realizado (R$)', places=2, validators=[Optional()])
    data = DateField('Data', default=date.today, format='%Y-%m-%d', validators=[DataRequired()])
    responsavel = SelectField('Responsável', choices=[('Reconlog', 'Reconlog'), ('Cliente', 'Cliente'), ('NSA', 'NSA')], default='Reconlog')
    observacao = StringField('Obs', validators=[Optional(), Length(max=200)])

class CarregamentoForm(FlaskForm):
    class Meta: csrf = False
    data = DateField('Data', default=date.today, format='%Y-%m-%d', validators=[DataRequired()])
    placa_caminhao = StringField('Placa', validators=[Optional(), Length(max=20)])
    documento_referencia = StringField('Doc/Romaneio', validators=[Optional(), Length(max=100)])
    observacao = StringField('Obs', validators=[Optional(), Length(max=200)])

class RomaneioForm(Form):
    id_item = IntegerField('ID', validators=[Optional()])
    descricao = StringField('Descrição', validators=[Optional(), Length(max=60)])
    quantidade = IntegerField('Qnt', validators=[Optional()])
    materia_prima_utilizada = StringField('Matéria Prima', validators=[Optional(), Length(max=50)])

class ControleProducaoForm(Form):
    departamento = SelectField('Departamento', choices=[('', 'Selecione'), ('Metalúrgica', 'Metalúrgica'), ('Confecção Lona', 'Confecção Lona'), ('Lavagem Lona', 'Lavagem Lona'), ('Logística', 'Logística')], validators=[Optional()])
    obs_prod = TextAreaField('Observação', validators=[Optional()])
    turno = SelectField('Turno', choices=[('', 'Selecione'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4')], validators=[Optional()])
    processo = SelectField('Processo', choices=[('', 'Selecione um departamento primeiro')], validators=[Optional()], validate_choice=False)
    maquina = StringField('Máquina', validators=[Optional()])
    operador = StringField('Operador', validators=[Optional()])
    data_inicio = DateField('Data Início', validators=[Optional()], format='%Y-%m-%d')
    hora_inicio = TimeField('Hora Início', validators=[Optional()], format='%H:%M')
    data_pausa = DateField('Data Desvio', validators=[Optional()], format='%Y-%m-%d')
    motivo_pausa = StringField('Motivo Desvio', validators=[Optional()])
    data_termino = DateField('Data Término', validators=[Optional()], format='%Y-%m-%d')
    hora_termino = TimeField('Hora Término', validators=[Optional()], format='%H:%M')
    qualidade = SelectField('Qualidade', choices=[('', 'Selecione'), ('Aprovado', 'Aprovado'), ('Reprovado', 'Reprovado')], validators=[Optional()])

class ApontamentoForm(FlaskForm):
    turno = StringField('Turno', validators=[Optional()])
    processo = StringField('Processo', validators=[Optional()])
    maquina_operacao = StringField('Máquina/Operação', validators=[Optional()])
    operador = StringField('Operador', validators=[Optional()])
    data_inicio = DateField('Data Início', validators=[Optional()], format='%Y-%m-%d')
    hora_inicio = TimeField('Início (h)', validators=[Optional()], format='%H:%M')
    data_termino = DateField('Data Término', validators=[Optional()], format='%Y-%m-%d')
    hora_termino = TimeField('Término (h)', validators=[Optional()], format='%H:%M')
    qualidade_aprovado = BooleanField('Aprovado', default=True)

class ParadaForm(FlaskForm):
    parada = StringField('Parada', validators=[Optional()])
    tempo_espera = TimeField('Tempo de Espera', validators=[Optional()], format='%H:%M')
    desvios_registrados = TextAreaField('Desvios', validators=[Optional()])
    aprovacao_desvio = StringField('Aprovação', validators=[Optional()])

class ManutApontForm(Form):
    manutentor = StringField('Manutentor', validators=[DataRequired(), Length(max=40)])
    data_inicio = DateField('Data Início', validators=[Optional()], format='%Y-%m-%d')
    hora_inicio = TimeField('Hora Início', validators=[Optional()], format='%H:%M')
    data_termino = DateField('Data Término', validators=[Optional()], format='%Y-%m-%d')
    hora_termino = TimeField('Hora Término', validators=[Optional()], format='%H:%M')

# ==================== FORMULÁRIOS PRINCIPAIS ====================

class OSForm(FlaskForm):
    # Classificação
    fase = RadioField('Classificação', choices=[('Pré-OS', 'Pré-OS'), ('OS', 'Ordem de Serviço')], default='OS', validators=[DataRequired()])
    Tipo_OS = SelectField('Tipo de O.S.', choices=[('', 'Selecione...'), ('Montagem', 'Montagem'), ('Desmontagem', 'Desmontagem'), ('Manutenção', 'Manutenção')], validators=[Optional()])
    empresa = SelectField('Empresa Destinada', choices=[('', 'Selecione...'), ('Reconlog Brasil', 'Reconlog Brasil'), ('Reconlog', 'Reconlog'), ('Reconlog Rental', 'Reconlog Rental')], validators=[DataRequired()])

    # Cronograma
    data_emissao = DateField('Data de Emissão', validators=[DataRequired()], default=date.today, format='%Y-%m-%d')
    data_inicio = DateField('Data de Início', validators=[Optional()], format='%Y-%m-%d')
    data_termino = DateField('Data Prevista Término', validators=[Optional()], format='%Y-%m-%d')
    data_entrega = DateField('Data de Entrega', validators=[Optional()], format='%Y-%m-%d')
    data_conclusao = DateField('Data de Conclusão', validators=[Optional()], format='%Y-%m-%d')
    data_carregamento = DateField('Data de Carregamento', validators=[Optional()], format='%Y-%m-%d') # Mantido legacy

    # Cliente e Status
    numero = StringField('Número da OS', validators=[DataRequired(), Length(max=50)])
    cliente = StringField('Cliente', validators=[DataRequired(), Length(max=150)])
    status = SelectField('Status', choices=[('Aberta', 'Aberta'), ('Em Andamento', 'Em Andamento'), ('Concluída', 'Concluída'), ('Cancelada', 'Cancelada')], validators=[DataRequired()], default='Aberta')
    Razao = StringField('Razão Social', validators=[Optional(), Length(max=30)])
    CNPJ = StringField('CNPJ', validators=[Optional(), Length(max=14)])
    Insc = StringField('Inscrição', validators=[Optional(), Length(max=15)])
    email = StringField('E-mail Contato', validators=[Optional(), Length(max=30)])
    telefone = StringField('Telefone Contato', validators=[Optional(), Length(max=30)])

    # Endereços
    endereco = StringField('Endereço', validators=[Optional(), Length(max=40)])
    Bairro = StringField('Bairro', validators=[Optional(), Length(max=40)])
    Cidade = StringField('Cidade', validators=[Optional(), Length(max=40)])
    UF = StringField('UF', validators=[Optional(), Length(max=2)])
    CEP = StringField('CEP', validators=[Optional(), Length(max=8)])

    fat_endereco = StringField('Endereço (Fat)', validators=[Optional(), Length(max=100)])
    fat_bairro = StringField('Bairro (Fat)', validators=[Optional(), Length(max=50)])
    fat_cidade = StringField('Cidade (Fat)', validators=[Optional(), Length(max=50)])
    fat_uf = StringField('UF (Fat)', validators=[Optional(), Length(max=2)])
    fat_cep = StringField('CEP (Fat)', validators=[Optional(), Length(max=10)])
    fat_emails = StringField('E-mails Faturamento', validators=[Optional(), Length(max=100)])

    mont_endereco = StringField('Endereço (Mont)', validators=[Optional(), Length(max=100)])
    mont_bairro = StringField('Bairro (Mont)', validators=[Optional(), Length(max=50)])
    mont_cidade = StringField('Cidade (Mont)', validators=[Optional(), Length(max=50)])
    mont_uf = StringField('UF (Mont)', validators=[Optional(), Length(max=2)])
    mont_cep = StringField('CEP (Mont)', validators=[Optional(), Length(max=10)])

    # Contrato e Detalhes
    tipo_contrato = SelectField('Tipo de Contrato', choices=[('', 'Selecione...'), ('Venda', 'Venda'), ('Locação', 'Locação'), ('Renovação', 'Renovação'), ('Prestação de Serviços', 'Prestação de Serviços')], validators=[Optional()])
    valor = DecimalField('Valor Total OS (R$)', places=2, validators=[DataRequired()])
    TipoLoc = StringField('Tipo Locação', validators=[Optional(), Length(max=15)])
    Modelo = StringField('Modelo', validators=[Optional(), Length(max=15)])
    qtde = DecimalField('Quantidade Item', places=3, validators=[Optional()])
    largura = DecimalField('Largura', places=5, validators=[Optional()])
    comprim = DecimalField('Comprimento', places=5, validators=[Optional()])
    Pedireito = DecimalField('Pé Direito', places=5, validators=[Optional()])
    Piso = StringField('Piso', validators=[Optional(), Length(max=15)])
    Acessorios = StringField('Acessórios', validators=[Optional(), Length(max=60)])

    # Responsáveis e Obs
    vendedo = StringField('Vendedor', validators=[Optional(), Length(max=40)])
    Segtrab = StringField('Segurança Trabalho', validators=[Optional(), Length(max=20)])
    integracao = StringField('Integração?', validators=[Optional(), Length(max=20)])
    observacoes = TextAreaField('Observações Gerais', validators=[Optional()])
    Obs2 = StringField('Outras Observações', validators=[Optional(), Length(max=60)])

    # Listas Dinâmicas
    custos_operacionais = FieldList(FormField(CustoOperacionalForm), min_entries=0)
    custos_visitas = FieldList(FormField(CustoVisitaForm), min_entries=0)
    carregamentos = FieldList(FormField(CarregamentoForm), min_entries=0)
    submit = SubmitField('Salvar OS')

class OrdemProducaoForm(FlaskForm):
    os = SelectField('Ordem de Serviço (OS)', coerce=int, validators=[DataRequired(message="Selecione uma OS.")])
    departamento = SelectField('Departamento', choices=[('', 'Selecione'), ('Metalurgia', 'Metalurgia'), ('Lona', 'Lona'), ('Logistica', 'Logistica')], validators=[DataRequired()])
    status = SelectField('Status', choices=[('Aberto', 'Aberto'), ('Fechado', 'Fechado')], validators=[DataRequired()], default='Aberto')
    data_fechamento = DateField('Data de Fechamento', validators=[Optional()], format='%Y-%m-%d')
    tipo_contrato = SelectField('Tipo de Contrato', choices=[('', 'Selecione'), ('Venda', 'Venda'), ('Locação', 'Locação')], validators=[DataRequired()])
    tipo_op = StringField('Tipo de O.P', validators=[Optional(), Length(max=5)])
    cliente = StringField('Cliente', validators=[DataRequired(), Length(max=60)])
    codigo = StringField('Código (OP)', validators=[Optional(), Length(max=8)])
    part_number_produto = StringField('Part Number do Produto', validators=[Optional()])
    quantidade = DecimalField('Quantidade', validators=[DataRequired()])
    largura = DecimalField('Largura', validators=[DataRequired()])
    comprimento = DecimalField('Comprimento', validators=[DataRequired()])
    pe_direito = DecimalField('Pé Direito', validators=[DataRequired()])
    piso = StringField('Piso', validators=[Optional(), Length(max=10)])
    data_emissao = DateField('Data da Emissão', validators=[DataRequired()], default=date.today, format='%Y-%m-%d')
    data_inicio_previsto = DateField('Data de Início Previsto', validators=[DataRequired()], default=date.today, format='%Y-%m-%d')
    data_termino_previsto = DateField('Data de Término Previsto', validators=[DataRequired()], default=date.today, format='%Y-%m-%d')
    data_carregamento = DateField('Data de Carregamento', validators=[DataRequired()], default=date.today, format='%Y-%m-%d')
    setor = StringField('Observação', validators=[Optional(), Length(max=20)])
    acessorios = TextAreaField('Acessórios', validators=[Optional()])
    observacoes = TextAreaField('Observações', validators=[Optional()])

    romaneios = FieldList(FormField(RomaneioForm), min_entries=1)
    controles_producao = FieldList(FormField(ControleProducaoForm), min_entries=1)
    submit = SubmitField('Salvar Ordem de Produção')

class OSManutencaoForm(FlaskForm):
    numero = StringField('Número OS', validators=[Optional(), Length(max=6)])
    data_abertura = DateField('Data Abertura', default=date.today, format='%Y-%m-%d', validators=[DataRequired()])
    hora_abert = TimeField('Hora Abertura', default=time(0, 0, 0), format='%H:%M', validators=[DataRequired()])
    solicitante = StringField('Solicitante', validators=[DataRequired(), Length(max=40)])
    area_setor = SelectField('Área/Setor', choices=[('', 'Selecione...'), ('ADM', 'ADM'), ('FACILITIES', 'FACILITIES'), ('FABRICA DE LONAS', 'FABRICA DE LONAS'), ('LAVAGEM DE LONAS', 'LAVAGEM DE LONAS'), ('METALURGICA', 'METALURGICA')], validators=[DataRequired()])
    maq_equip = SelectField('Máquina/Equipamento', choices=[('', 'Selecione um setor primeiro')], validators=[DataRequired()], validate_choice=False)
    ocorrencia = StringField('Ocorrência / Defeito', validators=[Optional(), Length(max=150)])
    parada = SelectField('Parada de Produção?', choices=[('Não', 'Não'), ('Sim', 'Sim')], validators=[DataRequired()], default='Não')

    sintoma = SelectField('Sintoma', choices=OPCOES_SINTOMAS, validators=[Optional()])
    causa = SelectField('Causa', choices=OPCOES_CAUSAS, validators=[Optional()])
    intervencao = SelectField('Intervenção', choices=OPCOES_INTERVENCOES, validators=[Optional()])

    materiais_utilizados = StringField('Materiais Utilizados', validators=[Optional(), Length(max=100)])
    data_encerramento = DateField('Data Encerramento', validators=[Optional()], format='%Y-%m-%d')

    manut_corretiva = BooleanField('Maint. Corretiva')
    manut_preventiva = BooleanField('Maint. Preventiva')
    manut_preditiva = BooleanField('Maint. Preditiva')
    inspecao = BooleanField('Inspeção')
    melhorias = BooleanField('Melhorias')
    predial = BooleanField('Predial')
    outro = BooleanField('Outro Serviço')
    obs_manut = TextAreaField('OBS Manutenção', validators=[Optional(), Length(max=100)])
    materiais_comprados = StringField('Materiais Comprados', validators=[Optional(), Length(max=100)])
    ficha_tec = StringField('Ficha Técnica', validators=[Optional(), Length(max=200)])
    assinatura1 = StringField('Assinatura 1', validators=[Optional(), Length(max=50)])
    assinatura2 = StringField('Assinatura 2', validators=[Optional(), Length(max=50)])

    apontamentos = FieldList(FormField(ManutApontForm), min_entries=1)
    submit = SubmitField('Salvar OS de Manutenção')

class UserForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('Senha', validators=[Optional(), Length(min=4)])
    role = SelectField('Nível de Acesso', choices=[('operador', 'Operador (Acesso Básico)'), ('compras', 'Compras (Custos)'), ('gerente', 'Gerente (Vê Custos)'), ('admin', 'Admin (Total)')], validators=[DataRequired()])
    submit = SubmitField('Salvar Usuário')

# 1. NOVO FORM PARA CADASTRAR/EDITAR TIPOS
class TipoFornecedorForm(FlaskForm):
    descricao = StringField('Descrição do Tipo', validators=[DataRequired(), Length(max=200)])
    submit = SubmitField('Salvar Tipo')

# 2. ATUALIZAÇÃO DO FORNECEDOR FORM
class FornecedorForm(FlaskForm):
    cod_sap = StringField('Cód. SAP', validators=[Optional(), Length(max=20)])
    razao_social = StringField('Razão Social', validators=[DataRequired(), Length(max=150)])
    nome_fantasia = StringField('Nome Fantasia', validators=[Optional(), Length(max=100)])
    
    # SelectField com coerce=int (pois o valor será o ID 1, 2, 3...)
    tipo_fornecedor_id = SelectField('Tipo de Fornecedor', coerce=int, validators=[DataRequired(message="Selecione um tipo")])

    documento = StringField('CNPJ / CPF / NIT / NIF', validators=[DataRequired(), Length(max=20)])
    inscricao_estadual = StringField('Inscrição Estadual', validators=[Optional(), Length(max=20)])
    email = StringField('E-mail', validators=[Optional(), Email(), Length(max=100)])
    telefone = StringField('Telefone', validators=[Optional(), Length(max=40)])
    
    endereco = StringField('Endereço', validators=[Optional(), Length(max=150)])
    bairro = StringField('Bairro', validators=[Optional(), Length(max=60)])
    cep = StringField('CEP', validators=[Optional(), Length(max=10)])
    cidade = StringField('Cidade', validators=[Optional(), Length(max=60)])
    uf = SelectField('UF', choices=[('', '-'), ('SP', 'SP'), ('RJ', 'RJ'), ('MG', 'MG'), ('RS', 'RS'), ('PR', 'PR'), ('SC', 'SC'), ('ES', 'ES'), ('GO', 'GO'), ('MT', 'MT'), ('MS', 'MS'), ('DF', 'DF'), ('BA', 'BA'), ('PE', 'PE')], validators=[Optional()])
    pais = StringField('País', default='Brasil', validators=[Optional(), Length(max=40)])

    submit = SubmitField('Salvar Fornecedor')

# No forms.py (Substitua a classe SolicitacaoItemForm por esta)
class SolicitacaoItemForm(Form):
    # Campo Oculto para o ID do Produto
    produto_id = IntegerField('ID Produto', validators=[Optional()]) 
    
    descricao_item = StringField('Descrição do Item', validators=[DataRequired(), Length(max=100)])
    quantidade = DecimalField('Qtd', validators=[DataRequired()])
    unidade = SelectField('Un.', choices=[('UN', 'UN'), ('KG', 'KG'), ('LT', 'LT'), ('MT', 'MT')], default='UN')
    prioridade = SelectField('Prioridade', choices=[('Normal', 'Normal'), ('Alta', 'Alta'), ('Baixa', 'Baixa')], default='Normal')

class SolicitacaoCompraForm(FlaskForm):
    observacao = TextAreaField('Justificativa / Observação', validators=[Optional()])
    itens = FieldList(FormField(SolicitacaoItemForm), min_entries=1)
    submit = SubmitField('Enviar Solicitação') 

# ==================== FORMS DE PEDIDO DE COMPRA ====================

class PedidoItemForm(Form):
    # O ID do produto vem oculto ou read-only
    produto_id = IntegerField('ID', validators=[Optional()])
    descricao = StringField('Descrição', validators=[DataRequired()])
    quantidade = DecimalField('Qtd', validators=[DataRequired()])
    unidade = StringField('Un.', validators=[Optional()])
    valor_unitario = DecimalField('Valor Unit. (R$)', validators=[InputRequired()])
    # O valor total do item será calculado pelo sistema (qtd * valor)

class PedidoCompraForm(FlaskForm):
    fornecedor = SelectField('Fornecedor', coerce=int, validators=[DataRequired()])
    condicao_pagamento = StringField('Condição de Pagamento', validators=[DataRequired(), Length(max=100)], default='28 DDL')
    prazo_entrega = StringField('Prazo de Entrega', validators=[Optional()], default='Imediato')
    observacoes = TextAreaField('Observações / Frete', validators=[Optional()])
    
    # Lista de itens (preços a preencher)
    itens = FieldList(FormField(PedidoItemForm), min_entries=1)
    
    # Botões de ação
    submit_salvar = SubmitField('Salvar Cotação')
    submit_aprovar = SubmitField('Salvar e Aprovar') # A lógica de alçada vai aqui