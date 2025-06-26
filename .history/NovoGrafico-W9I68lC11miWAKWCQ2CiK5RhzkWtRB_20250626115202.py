import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import matplotlib.pyplot as plt
from datetime import datetime
from calendar import month_name
import statistics
import pandas as pd
from dotenv import load_dotenv
import os


load_dotenv()

SENHA_BASIC = os.getenv("SENHA_BASIC")
SENHA_PREMIUM = os.getenv("SENHA_PREMIUM")
valores_atuais = []
periodos_atuais = []

mapa_opcoes = {
    "30 dias": '1',
    "Últimos 3 meses": '2',
    "Últimos 6 meses": '3',
    "Anual": '4'
}

def obter_periodos(opcao):
    mes_atual = datetime.now().month
    if opcao == '1':
        return [f'Dia {i+1}' for i in range(30)], 'Diário'
    elif opcao == '2':
        meses = [(mes_atual - i - 1) % 12 + 1 for i in range(3)][::-1]
        return [month_name[m].capitalize() for m in meses], 'Mensal'
    elif opcao == '3':
        meses = [(mes_atual - i - 1) % 12 + 1 for i in range(6)][::-1]
        return [month_name[m].capitalize() for m in meses], 'Mensal'
    elif opcao == '4':
        return [month_name[m].capitalize() for m in range(1, 13)], 'Mensal'
    return [], ''

def gerar_grafico(periodos, valores, eixo_y, tipo, tipo_grafico):
    fig, ax = plt.subplots(figsize=(14, 6))

    if tipo_grafico == '1':
        ax.plot(periodos, valores, marker='o', markersize=6, linewidth=2, color='#007ACC',
                markerfacecolor='#FF6600', markeredgecolor='#FF6600')
        ax.fill_between(periodos, valores, color='#ADD8E6', alpha=0.3)
        ax.set_title(f'Gráfico de Linha - {tipo} de {eixo_y}', fontsize=18, weight='bold')
    elif tipo_grafico == '2':
        ax.bar(periodos, valores, color='#007ACC', edgecolor='black')
        ax.set_title(f'Gráfico de Barras - {tipo} de {eixo_y}', fontsize=18, weight='bold')
    elif tipo_grafico == '3':
        ax.hist(valores, bins=10, color='#FF6600', edgecolor='black')
        ax.set_title(f'Histograma - Distribuição de {eixo_y}', fontsize=18, weight='bold')
        ax.set_xlabel(eixo_y)
        ax.set_ylabel('Frequência')
        plt.tight_layout()
        plt.show()
        return

    ax.set_xlabel(tipo, fontsize=12)
    ax.set_ylabel(eixo_y, fontsize=12)
    ax.grid(color='gray', linestyle='--', linewidth=0.6, alpha=0.7)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.xticks(rotation=45 if len(periodos) <= 6 else 90, fontsize=10)
    plt.yticks(fontsize=10)
    plt.tight_layout()
    plt.show()

def iniciar_analise():
    escolha_usuario = tipo_analise.get()
    opcao = mapa_opcoes.get(escolha_usuario)

    if not opcao:
        messagebox.showerror("Erro", "Selecione um tipo de análise válido.")
        return

    periodos, tipo = obter_periodos(opcao)
    eixo_y = campo_eixo_y.get().strip()
    entrada_valores = campo_valores.get("1.0", tk.END).strip()

    try:
        valores = [float(v.strip()) for v in entrada_valores.split(',')]
        if len(valores) != len(periodos):
            messagebox.showerror("Erro", f"Você deve digitar exatamente {len(periodos)} valores.")
            return
    except ValueError:
        messagebox.showerror("Erro", "Todos os valores devem ser numéricos.")
        return

    global valores_atuais, periodos_atuais
    valores_atuais = valores
    periodos_atuais = periodos

    senha = simpledialog.askstring("Senha", "Digite a senha de acesso:")

    if senha == SENHA_BASIC:
        messagebox.showinfo("Acesso Padrão", "Acesso padrão liberado. Exibindo gráfico de linha.")
        gerar_grafico(periodos, valores, eixo_y, tipo, '1')
    elif senha == SENHA_PREMIUM:
        tipo_grafico = simpledialog.askstring("Tipo de Gráfico", "Digite o tipo de gráfico (1 - Linha, 2 - Barras, 3 - Histograma):")
        if tipo_grafico not in ['1', '2', '3']:
            messagebox.showerror("Erro", "Opção de gráfico inválida.")
            return
        gerar_grafico(periodos, valores, eixo_y, tipo, tipo_grafico)
    else:
        messagebox.showerror("Acesso negado", "Senha incorreta.")

def adicionar_dado():
    novo_valor = campo_novo_valor.get()
    novo_periodo = campo_novo_periodo.get()
    try:
        valor_float = float(novo_valor)
        valores_atuais.insert(0, valor_float)
        periodos_atuais.insert(0, novo_periodo)
        messagebox.showinfo("Sucesso", f"Dado adicionado: {novo_periodo} = {valor_float}")
    except ValueError:
        messagebox.showerror("Erro", "Digite um valor numérico válido.")

def mostrar_media():
    if not valores_atuais:
        messagebox.showerror("Erro", "Nenhum dado carregado.")
        return
    media = statistics.mean(valores_atuais)
    messagebox.showinfo("Média", f"A média dos valores inseridos é: {media:.2f}")

def exportar_para_excel():
    if not valores_atuais or not periodos_atuais:
        messagebox.showerror("Erro", "Nenhum dado carregado para exportar.")
        return

    eixo_y = campo_eixo_y.get().strip()
    if not eixo_y:
        eixo_y = "Valor"

    df = pd.DataFrame({
        "Período": periodos_atuais,
        eixo_y: valores_atuais
    })

    caminho_arquivo = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                   filetypes=[("Arquivo Excel", "*.xlsx")],
                                                   title="Salvar como")
    if caminho_arquivo:
        try:
            df.to_excel(caminho_arquivo, index=False)
            messagebox.showinfo("Sucesso", f"Arquivo salvo com sucesso em:\n{caminho_arquivo}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar o arquivo:\n{str(e)}")

# Interface Tkinter
janela = tk.Tk()
janela.title("Análise de Dados com Gráfico")
janela.geometry("850x680")
janela.configure(bg="#f0f0f0")

titulo = tk.Label(janela, text="Analisador Gráfico de Dados", font=("Helvetica", 16, "bold"), bg="#f0f0f0")
titulo.pack(pady=10)

frame_analise = tk.Frame(janela, bg="#f0f0f0")
frame_analise.pack(pady=10)

tk.Label(frame_analise, text="Tipo de Análise:", font=("Helvetica", 12), bg="#f0f0f0").grid(row=0, column=0, sticky='w')
tipo_analise = tk.StringVar()
tipo_analise.set("30 dias")
tk.OptionMenu(frame_analise, tipo_analise, *mapa_opcoes.keys()).grid(row=0, column=1, padx=10, pady=5)

tk.Label(frame_analise, text="Nome do Eixo Y:", font=("Helvetica", 12), bg="#f0f0f0").grid(row=1, column=0, sticky='w')
campo_eixo_y = tk.Entry(frame_analise, width=40)
campo_eixo_y.grid(row=1, column=1, padx=10, pady=5)

tk.Label(janela, text="Valores (separados por vírgula):", font=("Helvetica", 12), bg="#f0f0f0").pack()
campo_valores = tk.Text(janela, width=90, height=5, font=("Courier", 10))
campo_valores.pack(pady=5)

frame_novos = tk.Frame(janela, bg="#f0f0f0")
frame_novos.pack(pady=10)

tk.Label(frame_novos, text="Novo Valor:", font=("Helvetica", 12), bg="#f0f0f0").grid(row=0, column=0)
campo_novo_valor = tk.Entry(frame_novos, width=15)
campo_novo_valor.grid(row=0, column=1, padx=5)

tk.Label(frame_novos, text="Mês/Período:", font=("Helvetica", 12), bg="#f0f0f0").grid(row=0, column=2)
campo_novo_periodo = tk.Entry(frame_novos, width=15)
campo_novo_periodo.grid(row=0, column=3, padx=5)

tk.Button(frame_novos, text="Adicionar Dado", command=adicionar_dado, bg="#1976D2", fg="white").grid(row=0, column=4, padx=10)

tk.Button(janela, text="Gerar Análise", command=iniciar_analise, bg="#4CAF50", fg="white",
          font=("Helvetica", 12, "bold"), width=20).pack(pady=10)

tk.Button(janela, text="Mostrar Média", command=mostrar_media, bg="#FF9800", fg="white",
          font=("Helvetica", 12), width=20).pack(pady=5)

tk.Button(janela, text="Exportar para Excel", command=exportar_para_excel, bg="#2196F3", fg="white",
          font=("Helvetica", 12), width=20).pack(pady=5)

janela.mainloop()
