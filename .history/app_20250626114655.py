# Adicionar esta rota ao arquivo app.py existente

@app.route('/download-executavel')
def download_executavel():
    """Servir o executável atualizado com senhas escondidas"""
    try:
        # Caminho para o arquivo executável atualizado
        caminho_executavel = os.path.join(os.getcwd(), 'NovoGrafico_Atualizado.py')
        
        # Verificar se o arquivo existe
        if not os.path.exists(caminho_executavel):
            flash('Arquivo executável não encontrado!', 'error')
            return redirect(url_for('index'))
        
        return send_file(
            caminho_executavel,
            as_attachment=True,
            download_name='AnalisadorGrafico_Seguro.py',
            mimetype='text/x-python'
        )
        
    except Exception as e:
        flash(f'Erro ao baixar executável: {str(e)}', 'error')
        return redirect(url_for('index'))

# Atualizar a função JavaScript no template bi.html
@app.route('/get-download-link')
def get_download_link():
    """Retorna o link atualizado para download"""
    return jsonify({
        'success': True,
        'download_url': url_for('download_executavel'),
        'filename': 'AnalisadorGrafico_Seguro.py',
        'message': 'Executável atualizado com segurança aprimorada'
    })