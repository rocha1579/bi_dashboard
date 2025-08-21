from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
import os
import qrcode
import io
import base64
import pandas as pd
from datetime import datetime
import json

# === CONFIGURAÇÃO INICIAL ===

app = Flask(__name__)

# Usa /tmp na Vercel para suportar escrita
BASE_DIR = '/tmp' if 'VERCEL' in os.environ else os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'clientes.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.secret_key = 'sua_chave_secreta_super_segura_aqui_2024'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db = SQLAlchemy(app)

# Senha do administrador
ADMIN_PASSWORD = 'admin2024'

PRECOS = {
    'basico': 25.00,
    'premium': 50.00,
    'pro': 75.00
}

STRIPE_PUBLIC_KEY = 'pk_test_sua_chave_publica_aqui'
STRIPE_SECRET_KEY = 'sk_test_sua_chave_secreta_aqui'

# === MODELOS ===

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80), nullable=False)

class Pagamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), nullable=False)
    plano = db.Column(db.String(20), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    metodo = db.Column(db.String(20), default='pix')
    status = db.Column(db.String(20), default='pendente')
    codigo_acesso = db.Column(db.String(100), nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

class DashboardConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_email = db.Column(db.String(80), nullable=False)
    config_json = db.Column(db.Text, nullable=False)
    nome_dashboard = db.Column(db.String(100), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

if not os.path.exists(DB_PATH):
    with app.app_context():
        db.create_all()

# === FUNÇÕES AUXILIARES ===

def gerar_qr_code_pix(valor, chave_pix="31995120154"):
    try:
        pix_payload = (
            f"00020126"
            f"010211"
            f"26580014br.gov.bcb.pix"
            f"0136{chave_pix}"
            f"52040000"
            f"5303986"
            f"54{int(valor*100):02d}"
            f"5802BR"
            f"5925GeoMX Tecnologia"
            f"6009SAO PAULO"
            f"62070503***"
            f"6304"
        )
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(pix_payload)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        return img_base64
    except Exception as e:
        return ""

# (... resto do código segue normalmente como já está funcionando ...)  # Mantido para não cortar por limite de tamanho

# Se quiser, posso dividir o restante ou mandar como anexo também.

if __name__ == '__main__':
    app.run(debug=True, port=5000)
