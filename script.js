import { Chart } from "@/components/ui/chart"
// Variáveis globais
let valoresAtuais = []
let periodosAtuais = []
let graficoAtual = null

// Mapeamento de opções
const mapaOpcoes = {
  "30 dias": "1",
  "Últimos 3 meses": "2",
  "Últimos 6 meses": "3",
  Anual: "4",
}

// Função para obter períodos
function obterPeriodos(opcao) {
  const mesAtual = new Date().getMonth() + 1
  const nomesMeses = [
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
  ]

  switch (opcao) {
    case "1":
      return {
        periodos: Array.from({ length: 30 }, (_, i) => `Dia ${i + 1}`),
        tipo: "Diário",
      }
    case "2":
      const meses3 = []
      for (let i = 2; i >= 0; i--) {
        const mes = (mesAtual - i - 1 + 12) % 12
        meses3.push(nomesMeses[mes])
      }
      return { periodos: meses3, tipo: "Mensal" }
    case "3":
      const meses6 = []
      for (let i = 5; i >= 0; i--) {
        const mes = (mesAtual - i - 1 + 12) % 12
        meses6.push(nomesMeses[mes])
      }
      return { periodos: meses6, tipo: "Mensal" }
    case "4":
      return { periodos: nomesMeses, tipo: "Mensal" }
    default:
      return { periodos: [], tipo: "" }
  }
}

// Função para gerar gráfico
function gerarGrafico(periodos, valores, eixoY, tipo, tipoGrafico) {
  const ctx = document.getElementById("grafico").getContext("2d")

  if (graficoAtual) {
    graficoAtual.destroy()
  }

  const cores = {
    line: {
      backgroundColor: "rgba(52, 152, 219, 0.1)",
      borderColor: "rgba(52, 152, 219, 1)",
      pointBackgroundColor: "rgba(231, 76, 60, 1)",
    },
    bar: {
      backgroundColor: "rgba(52, 152, 219, 0.8)",
      borderColor: "rgba(52, 152, 219, 1)",
    },
    doughnut: {
      backgroundColor: [
        "rgba(52, 152, 219, 0.8)",
        "rgba(231, 76, 60, 0.8)",
        "rgba(46, 204, 113, 0.8)",
        "rgba(241, 196, 15, 0.8)",
        "rgba(155, 89, 182, 0.8)",
        "rgba(230, 126, 34, 0.8)",
      ],
    },
  }

  const config = {
    type: tipoGrafico,
    data: {
      labels: periodos,
      datasets: [
        {
          label: eixoY || "Valores",
          data: valores,
          ...cores[tipoGrafico],
          borderWidth: 2,
          tension: 0.4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: `${
            tipoGrafico === "line"
              ? "Gráfico de Linha"
              : tipoGrafico === "bar"
                ? "Gráfico de Barras"
                : "Gráfico de Pizza"
          } - ${tipo} de ${eixoY || "Valores"}`,
          font: {
            size: 16,
            weight: "bold",
          },
        },
        legend: {
          display: tipoGrafico === "doughnut",
        },
      },
      scales:
        tipoGrafico !== "doughnut"
          ? {
              y: {
                beginAtZero: true,
                title: {
                  display: true,
                  text: eixoY || "Valores",
                },
              },
              x: {
                title: {
                  display: true,
                  text: tipo,
                },
              },
            }
          : {},
    },
  }

  graficoAtual = new Chart(ctx, config)
}

// Função para atualizar estatísticas
function atualizarEstatisticas(valores) {
  if (valores.length === 0) {
    document.getElementById("mediaValor").textContent = "-"
    document.getElementById("totalPontos").textContent = "-"
    document.getElementById("maiorValor").textContent = "-"
    document.getElementById("menorValor").textContent = "-"
    return
  }

  const media = valores.reduce((a, b) => a + b, 0) / valores.length
  const maior = Math.max(...valores)
  const menor = Math.min(...valores)

  document.getElementById("mediaValor").textContent = media.toFixed(2)
  document.getElementById("totalPontos").textContent = valores.length
  document.getElementById("maiorValor").textContent = maior.toFixed(2)
  document.getElementById("menorValor").textContent = menor.toFixed(2)
}

// Função para iniciar análise
function gerarAnalise() {
  const escolhaUsuario = document.getElementById("tipoAnalise").value
  const opcao = mapaOpcoes[escolhaUsuario]

  if (!opcao) {
    alert("Selecione um tipo de análise válido.")
    return
  }

  const { periodos, tipo } = obterPeriodos(opcao)
  const eixoY = document.getElementById("eixoY").value.trim()
  const entradaValores = document.getElementById("valores").value.trim()

  try {
    const valores = entradaValores.split(",").map((v) => Number.parseFloat(v.trim()))

    if (valores.some(isNaN)) {
      alert("Todos os valores devem ser numéricos.")
      return
    }

    if (valores.length !== periodos.length) {
      alert(`Você deve digitar exatamente ${periodos.length} valores.`)
      return
    }

    valoresAtuais = valores
    periodosAtuais = periodos

    // Atualizar estatísticas
    atualizarEstatisticas(valores)

    // Mostrar modal de senha
    document.getElementById("modalSenha").style.display = "block"
  } catch (error) {
    alert("Erro ao processar os valores.")
  }
}

// Função para verificar senha
function verificarSenha() {
  const senha = document.getElementById("senha").value
  const eixoY = document.getElementById("eixoY").value.trim()
  const { tipo } = obterPeriodos(mapaOpcoes[document.getElementById("tipoAnalise").value])

  if (senha === "123") {
    alert("Acesso padrão liberado. Exibindo gráfico de linha.")
    gerarGrafico(periodosAtuais, valoresAtuais, eixoY, tipo, "line")
    fecharModal()
  } else if (senha === "premium") {
    alert("Acesso premium liberado. Escolha o tipo de gráfico.")
    fecharModal()
    document.getElementById("modalTipoGrafico").style.display = "block"
  } else {
    alert("Senha incorreta.")
  }
}

// Função para selecionar tipo de gráfico
function selecionarTipoGrafico(tipo) {
  const eixoY = document.getElementById("eixoY").value.trim()
  const { tipo: tipoAnalise } = obterPeriodos(mapaOpcoes[document.getElementById("tipoAnalise").value])

  gerarGrafico(periodosAtuais, valoresAtuais, eixoY, tipoAnalise, tipo)
  fecharModalTipo()
}

// Função para adicionar dado
function adicionarDado() {
  const novoValor = document.getElementById("novoValor").value
  const novoPeriodo = document.getElementById("novoPeriodo").value

  try {
    const valorFloat = Number.parseFloat(novoValor)
    if (isNaN(valorFloat)) {
      alert("Digite um valor numérico válido.")
      return
    }

    valoresAtuais.unshift(valorFloat)
    periodosAtuais.unshift(novoPeriodo)

    alert(`Dado adicionado: ${novoPeriodo} = ${valorFloat}`)

    // Limpar campos
    document.getElementById("novoValor").value = ""
    document.getElementById("novoPeriodo").value = ""

    // Atualizar estatísticas
    atualizarEstatisticas(valoresAtuais)
  } catch (error) {
    alert("Erro ao adicionar dado.")
  }
}

// Função para mostrar média
function mostrarMedia() {
  if (valoresAtuais.length === 0) {
    alert("Nenhum dado carregado.")
    return
  }

  const media = valoresAtuais.reduce((a, b) => a + b, 0) / valoresAtuais.length
  alert(`A média dos valores inseridos é: ${media.toFixed(2)}`)
}

// Função para exportar para Excel
function exportarExcel() {
  if (valoresAtuais.length === 0 || periodosAtuais.length === 0) {
    alert("Nenhum dado carregado para exportar.")
    return
  }

  const eixoY = document.getElementById("eixoY").value.trim() || "Valor"

  const dados = periodosAtuais.map((periodo, index) => ({
    Período: periodo,
    [eixoY]: valoresAtuais[index],
  }))

  // Certifique-se de que XLSX está disponível (por exemplo, importando a biblioteca)
  if (typeof XLSX === "undefined") {
    alert("A biblioteca XLSX não está disponível. Certifique-se de importá-la.")
    return
  }

  const ws = XLSX.utils.json_to_sheet(dados)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, "Dados")

  XLSX.writeFile(wb, "analise_dados.xlsx")
  alert("Arquivo Excel exportado com sucesso!")
}

// Função para download do executável
function downloadExecutable() {
  // Criar um link para download do arquivo Python
  const link = document.createElement("a")
  link.href = "https://blobs.vusercontent.net/blob/NovoGrafico-W9I68lC11miWAKWCQ2CiK5RhzkWtRB.py"
  link.download = "AnalisadorGrafico.py"
  link.click()

  alert("Download iniciado! Execute o arquivo Python para usar a versão desktop.")
}

// Funções para modais
function fecharModal() {
  document.getElementById("modalSenha").style.display = "none"
  document.getElementById("senha").value = ""
}

function fecharModalTipo() {
  document.getElementById("modalTipoGrafico").style.display = "none"
}

// Event listeners
document.addEventListener("DOMContentLoaded", () => {
  // Fechar modal ao clicar fora
  window.onclick = (event) => {
    const modalSenha = document.getElementById("modalSenha")
    const modalTipo = document.getElementById("modalTipoGrafico")

    if (event.target === modalSenha) {
      fecharModal()
    }
    if (event.target === modalTipo) {
      fecharModalTipo()
    }
  }

  // Enter para verificar senha
  document.getElementById("senha").addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      verificarSenha()
    }
  })

  // Mudança no tipo de gráfico
  document.getElementById("tipoGrafico").addEventListener("change", function () {
    if (valoresAtuais.length > 0 && periodosAtuais.length > 0) {
      const eixoY = document.getElementById("eixoY").value.trim()
      const { tipo } = obterPeriodos(mapaOpcoes[document.getElementById("tipoAnalise").value])
      gerarGrafico(periodosAtuais, valoresAtuais, eixoY, tipo, this.value)
    }
  })
})
