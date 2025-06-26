from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
import os
import qrcode
import io
import base64
import pandas as pd
from datetime import datetime
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clientes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'sua_chave_secreta_super_segura_aqui_2024'

# Criar pasta de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Senha do administrador
ADMIN_PASSWORD = 'admin2024'

# Preços atualizados
PRECOS = {
    'basico': 25.00,    # Gráficos básicos
    'premium': 50.00,   # Gráficos avançados + exportação
    'pro': 75.00        # Editor visual + dashboard avançado
}

# SENHAS ATUALIZADAS - Sincronizadas com o frontend
SENHAS_ACESSO = {
    'basico': 'bi2025basic',
    'premium': 'bi2025premium', 
    'pro': 'bi2025pro'
}

# Configuração Stripe (substitua pela sua chave)
STRIPE_PUBLIC_KEY = 'pk_test_sua_chave_publica_aqui'
STRIPE_SECRET_KEY = 'sk_test_sua_chave_secreta_aqui'

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80), nullable=False)

class Pagamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), nullable=False)
    plano = db.Column(db.String(20), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    metodo = db.Column(db.String(20), default='pix')  # pix ou cartao
    status = db.Column(db.String(20), default='pendente')
    codigo_acesso = db.Column(db.String(100), nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

class DashboardConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_email = db.Column(db.String(80), nullable=False)
    config_json = db.Column(db.Text, nullable=False)
    nome_dashboard = db.Column(db.String(100), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

class LogAcesso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    senha_usada = db.Column(db.String(100), nullable=False)
    plano_acessado = db.Column(db.String(20), nullable=False)
    ip_usuario = db.Column(db.String(45), nullable=True)
    data_acesso = db.Column(db.DateTime, default=datetime.utcnow)
    sucesso = db.Column(db.Boolean, default=True)

# Remover banco existente para recriar
if os.path.exists('clientes.db'):
    os.remove('clientes.db')

with app.app_context():
    db.create_all()

def gerar_qr_code_pix(valor, chave_pix="31995120154"):
    """Gera QR Code PIX"""
    pix_payload = f"00020126580014br.gov.bcb.pix0136{chave_pix}520400005303986540{valor:.2f}5802BR5925Gabriel Alves6009SAO PAULO62070503***6304"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(pix_payload)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return img_base64

def processar_arquivo_dados(arquivo):
    """Processa arquivo CSV/Excel e extrai dados"""
    try:
        if arquivo.filename.endswith('.csv'):
            df = pd.read_csv(arquivo)
        elif arquivo.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(arquivo)
        else:
            return None, "Formato de arquivo não suportado"
        
        # Tentar identificar colunas de período e valores
        colunas = df.columns.tolist()
        
        # Procurar por colunas que podem ser períodos
        coluna_periodo = None
        coluna_valor = None
        
        for col in colunas:
            col_lower = col.lower()
            if any(palavra in col_lower for palavra in ['data', 'periodo', 'mes', 'dia', 'ano', 'time']):
                coluna_periodo = col
            elif any(palavra in col_lower for palavra in ['valor', 'vendas', 'receita', 'quantidade', 'total']):
                coluna_valor = col
        
        # Se não encontrou, usar as duas primeiras colunas
        if not coluna_periodo:
            coluna_periodo = colunas[0]
        if not coluna_valor and len(colunas) > 1:
            coluna_valor = colunas[1]
        
        # Extrair dados
        periodos = df[coluna_periodo].astype(str).tolist()[:20]  # Limitar a 20 itens
        valores = pd.to_numeric(df[coluna_valor], errors='coerce').fillna(0).tolist()[:20]
        
        return {
            'periodos': periodos,
            'valores': valores,
            'eixo_y': coluna_valor,
            'tipo_analise': 'Dados Importados'
        }, None
        
    except Exception as e:
        return None, f"Erro ao processar arquivo: {str(e)}"

def registrar_acesso(senha, sucesso=True):
    """Registra tentativa de acesso no sistema"""
    plano = 'desconhecido'
    for p, s in SENHAS_ACESSO.items():
        if s == senha:
            plano = p
            break
    
    log = LogAcesso(
        senha_usada=senha,
        plano_acessado=plano,
        ip_usuario=request.remote_addr,
        sucesso=sucesso
    )
    db.session.add(log)
    db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        senha = request.form.get('senha')
        if senha == ADMIN_PASSWORD:
            session['admin'] = True
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('admin_clientes'))
        else:
            flash('Senha incorreta!', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/clientes')
def admin_clientes():
    if not session.get('admin'):
        flash('Acesso negado! Faça login como administrador.', 'error')
        return redirect(url_for('admin_login'))
    
    clientes = Cliente.query.all()
    pagamentos = Pagamento.query.order_by(Pagamento.data_criacao.desc()).all()
    logs_acesso = LogAcesso.query.order_by(LogAcesso.data_acesso.desc()).limit(50).all()
    
    # Estatísticas
    stats = {
        'total_clientes': len(clientes),
        'total_pagamentos': len(pagamentos),
        'pagamentos_confirmados': len([p for p in pagamentos if p.status == 'confirmado']),
        'receita_total': sum([p.valor for p in pagamentos if p.status == 'confirmado']),
        'acessos_hoje': len([l for l in logs_acesso if l.data_acesso.date() == datetime.now().date()])
    }
    
    return render_template('admin_clientes.html', 
                         clientes=clientes, 
                         pagamentos=pagamentos,
                         logs_acesso=logs_acesso,
                         stats=stats,
                         senhas_acesso=SENHAS_ACESSO)

@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/bi')
def bi():
    return render_template('bi.html')

@app.route('/bi-pro')
def bi_pro():
    return render_template('bi_pro.html')

@app.route('/pagamento/<plano>')
def pagamento(plano):
    if plano not in PRECOS:
        flash('Plano inválido!', 'error')
        return redirect(url_for('index'))
    
    valor = PRECOS[plano]
    qr_code = gerar_qr_code_pix(valor)
    
    return render_template('pagamento.html', 
                         plano=plano, 
                         valor=valor, 
                         qr_code=qr_code,
                         chave_pix="31995120154",
                         stripe_public_key=STRIPE_PUBLIC_KEY)

@app.route('/confirmar-pagamento', methods=['POST'])
def confirmar_pagamento():
    email = request.form.get('email')
    plano = request.form.get('plano')
    metodo = request.form.get('metodo', 'pix')
    
    if not email or plano not in PRECOS:
        flash('Dados inválidos!', 'error')
        return redirect(url_for('index'))
    
    # Registrar pagamento
    pagamento = Pagamento(
        email=email,
        plano=plano,
        valor=PRECOS[plano],
        metodo=metodo,
        status='pendente'
    )
    db.session.add(pagamento)
    db.session.commit()
    
    flash('Pagamento registrado! Aguarde a confirmação.', 'info')
    return render_template('confirmacao.html', email=email, plano=plano)

@app.route('/processar-cartao', methods=['POST'])
def processar_cartao():
    # Aqui você integraria com Stripe ou outro processador
    # Por enquanto, vamos simular o processamento
    
    email = request.form.get('email')
    plano = request.form.get('plano')
    
    # Simular processamento bem-sucedido
    pagamento = Pagamento(
        email=email,
        plano=plano,
        valor=PRECOS[plano],
        metodo='cartao',
        status='confirmado'  # Cartão é confirmado automaticamente
    )
    
    # Usar as novas senhas atualizadas
    pagamento.codigo_acesso = SENHAS_ACESSO[plano]
    
    db.session.add(pagamento)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'codigo': pagamento.codigo_acesso,
        'message': 'Pagamento processado com sucesso!'
    })

@app.route('/verificar-acesso', methods=['POST'])
def verificar_acesso():
    """Nova rota para verificar senhas de acesso"""
    data = request.get_json()
    senha = data.get('senha', '').strip()
    
    # Verificar se a senha é válida
    plano_encontrado = None
    for plano, senha_correta in SENHAS_ACESSO.items():
        if senha == senha_correta:
            plano_encontrado = plano
            break
    
    if plano_encontrado:
        # Registrar acesso bem-sucedido
        registrar_acesso(senha, sucesso=True)
        
        return jsonify({
            'success': True,
            'plano': plano_encontrado,
            'message': f'Acesso {plano_encontrado.title()} liberado com sucesso!'
        })
    else:
        # Registrar tentativa de acesso falhada
        registrar_acesso(senha, sucesso=False)
        
        return jsonify({
            'success': False,
            'message': 'Senha incorreta! Verifique as senhas disponíveis.'
        }), 401

@app.route('/upload-dados', methods=['POST'])
def upload_dados():
    if 'arquivo' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'})
    
    arquivo = request.files['arquivo']
    if arquivo.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'})
    
    dados, erro = processar_arquivo_dados(arquivo)
    
    if erro:
        return jsonify({'error': erro})
    
    return jsonify({'success': True, 'dados': dados})

@app.route('/salvar-dashboard', methods=['POST'])
def salvar_dashboard():
    data = request.get_json()
    
    config = DashboardConfig(
        usuario_email=data.get('email', 'anonimo'),
        config_json=json.dumps(data.get('config')),
        nome_dashboard=data.get('nome', 'Dashboard Sem Nome')
    )
    
    db.session.add(config)
    db.session.commit()
    
    return jsonify({'success': True, 'id': config.id})

@app.route('/cliente', methods=['GET', 'POST'])
def cliente():
    if request.method == 'POST':
        if not session.get('admin'):
            flash('Acesso negado! Apenas administradores podem cadastrar clientes.', 'error')
            return redirect(url_for('admin_login'))
        
        nome = request.form.get('nome')
        email = request.form.get('email')

        if not nome or not email:
            flash('Nome e email são obrigatórios!', 'error')
            return redirect(url_for('admin_clientes'))

        novo_cliente = Cliente(nome=nome, email=email)
        db.session.add(novo_cliente)
        db.session.commit()
        flash('Cliente cadastrado com sucesso!', 'success')
        return redirect(url_for('admin_clientes'))
    
    clientes = Cliente.query.all()
    return jsonify([{'id': c.id, 'nome': c.nome, 'email': c.email} for c in clientes])

@app.route('/admin/confirmar-pagamento/<int:pagamento_id>')
def confirmar_pagamento_admin(pagamento_id):
    if not session.get('admin'):
        flash('Acesso negado!', 'error')
        return redirect(url_for('admin_login'))
    
    pagamento = Pagamento.query.get_or_404(pagamento_id)
    pagamento.status = 'confirmado'
    
    # Usar as novas senhas atualizadas
    pagamento.codigo_acesso = SENHAS_ACESSO[pagamento.plano]
    
    db.session.commit()
    flash(f'Pagamento confirmado! Código: {pagamento.codigo_acesso}', 'success')
    return redirect(url_for('admin_clientes'))

@app.route('/admin/gerar-codigo/<plano>')
def gerar_codigo_teste(plano):
    """Gerar código de teste para administradores"""
    if not session.get('admin'):
        return jsonify({'error': 'Acesso negado'}), 403
    
    if plano not in SENHAS_ACESSO:
        return jsonify({'error': 'Plano inválido'}), 400
    
    codigo = SENHAS_ACESSO[plano]
    
    # Registrar geração de código de teste
    pagamento_teste = Pagamento(
        email='admin@teste.com',
        plano=plano,
        valor=0.00,
        metodo='teste',
        status='confirmado',
        codigo_acesso=codigo
    )
    db.session.add(pagamento_teste)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'codigo': codigo,
        'plano': plano,
        'message': f'Código de teste gerado para plano {plano}'
    })

@app.route('/enviar-relatorio-email', methods=['POST'])
def enviar_relatorio_email():
    try:
        data = request.get_json()
        email = data.get('email')
        formato = data.get('formato')
        relatorio = data.get('relatorio')
        tipo = data.get('tipo', 'teste')
        
        # Simular envio de email (em produção usaria SMTP real)
        print(f"📧 Simulando envio de email:")
        print(f"   Destinatário: {email}")
        print(f"   Formato: {formato}")
        print(f"   Tipo: {tipo}")
        print(f"   Título: {relatorio.get('titulo', 'Relatório BI')}")
        print(f"   Data: {relatorio.get('data')}")
        
        # Registrar envio no banco (opcional)
        # envio = EnvioEmail(
        #     email=email,
        #     formato=formato,
        #     tipo=tipo,
        #     status='enviado',
        #     data_envio=datetime.utcnow()
        # )
        # db.session.add(envio)
        # db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Email {tipo} enviado com sucesso para {email}',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"Erro ao enviar email: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/senhas-acesso')
def api_senhas_acesso():
    """API para obter senhas de acesso atuais"""
    if not session.get('admin'):
        return jsonify({'error': 'Acesso negado'}), 403
    
    return jsonify({
        'senhas': SENHAS_ACESSO,
        'precos': PRECOS,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/admin/logs')
def admin_logs():
    """Visualizar logs de acesso"""
    if not session.get('admin'):
        flash('Acesso negado!', 'error')
        return redirect(url_for('admin_login'))
    
    logs = LogAcesso.query.order_by(LogAcesso.data_acesso.desc()).limit(100).all()
    
    # Estatísticas dos logs
    total_acessos = LogAcesso.query.count()
    acessos_sucesso = LogAcesso.query.filter_by(sucesso=True).count()
    acessos_falha = LogAcesso.query.filter_by(sucesso=False).count()
    
    stats_logs = {
        'total': total_acessos,
        'sucesso': acessos_sucesso,
        'falha': acessos_falha,
        'taxa_sucesso': (acessos_sucesso / total_acessos * 100) if total_acessos > 0 else 0
    }
    
    return render_template('admin_logs.html', logs=logs, stats=stats_logs)

if __name__ == '__main__':
    print("🚀 Iniciando Dashboard BI Pro Backend")
    print("📊 Senhas de acesso atualizadas:")
    for plano, senha in SENHAS_ACESSO.items():
        print(f"   {plano.upper()}: {senha}")
    print("🔧 Servidor rodando em http://localhost:5000")
    
    app.run(debug=True, port=5000)
