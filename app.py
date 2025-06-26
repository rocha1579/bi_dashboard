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

# Novos preços atualizados
PRECOS = {
    'basico': 25.00,    # Gráficos básicos
    'premium': 50.00,   # Gráficos avançados + exportação
    'pro': 75.00        # Editor visual + dashboard avançado
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
    return render_template('admin_clientes.html', clientes=clientes, pagamentos=pagamentos)

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
    
    # Gerar códigos de acesso mais seguros
    if plano == 'basico':
        pagamento.codigo_acesso = 'Basic123*'
    elif plano == 'premium':
        pagamento.codigo_acesso = 'Premium2024$'
    else:  # pro
        pagamento.codigo_acesso = 'ProBI2024!@#'
    
    db.session.add(pagamento)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'codigo': pagamento.codigo_acesso,
        'message': 'Pagamento processado com sucesso!'
    })

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
    
    # Gerar códigos de acesso mais seguros
    if pagamento.plano == 'basico':
        pagamento.codigo_acesso = 'Basic123*'
    elif pagamento.plano == 'premium':
        pagamento.codigo_acesso = 'Premium2024$'
    else:  # pro
        pagamento.codigo_acesso = 'ProBI2024!@#'
    
    db.session.commit()
    flash(f'Pagamento confirmado! Código: {pagamento.codigo_acesso}', 'success')
    return redirect(url_for('admin_clientes'))

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
