import csv
import os
import platform
import sqlite3
import socket
import sys
import time
from datetime import datetime, timedelta

import psutil


# ============================================================
# CONFIGURAÇÕES
# ============================================================

# Intervalo entre as medições.
# 60 segundos = 1 medição por minuto.
INTERVALO_COLETA = 60

# Quantidade de segundos usada para calcular cada amostra.
# O valor 1 significa que cada medição representa
# aproximadamente 1 segundo de utilização da CPU.
INTERVALO_CPU = 1


# ============================================================
# DIRETÓRIOS
# ============================================================

# Obtém a pasta onde o programa está sendo executado.
# Isso é importante quando o programa virar .exe.
BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))

PASTA_DADOS = os.path.join(BASE_DIR, "dados")
PASTA_RELATORIOS = os.path.join(BASE_DIR, "relatorios")

BANCO_DADOS = os.path.join(
    PASTA_DADOS,
    "cpu_monitor.db"
)


# Cria as pastas automaticamente.
os.makedirs(PASTA_DADOS, exist_ok=True)
os.makedirs(PASTA_RELATORIOS, exist_ok=True)


# ============================================================
# BANCO DE DADOS
# ============================================================

def conectar_banco():
    """
    Abre conexão com o banco SQLite.
    """
    return sqlite3.connect(BANCO_DADOS)


def criar_banco():
    """
    Cria as tabelas necessárias caso ainda não existam.
    """

    conn = conectar_banco()
    cursor = conn.cursor()

    # Informações permanentes do servidor.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS servidor (
            id INTEGER PRIMARY KEY,
            nome_servidor TEXT NOT NULL,
            sistema_operacional TEXT,
            processador TEXT,
            fabricante_processador TEXT,
            nucleos_fisicos INTEGER,
            processadores_logicos INTEGER,
            frequencia_maxima_mhz REAL,
            data_primeiro_registro TEXT
        )
    """)

    # Medições da CPU.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monitoramento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT NOT NULL,
            data TEXT NOT NULL,
            uso_cpu REAL NOT NULL
        )
    """)

    # Índice para acelerar consultas por data.
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_monitoramento_data
        ON monitoramento(data)
    """)

    conn.commit()
    conn.close()


# ============================================================
# IDENTIFICAÇÃO DO PROCESSADOR
# ============================================================

def obter_nome_processador_windows():
    """
    Obtém o nome comercial do processador através do Registro
    do Windows.

    Isso normalmente fornece informações melhores que
    platform.processor().
    """

    if platform.system() != "Windows":
        return None

    try:
        import winreg

        caminho = (
            r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
        )

        chave = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            caminho
        )

        nome, _ = winreg.QueryValueEx(
            chave,
            "ProcessorNameString"
        )

        winreg.CloseKey(chave)

        return nome.strip()

    except Exception:
        return None


def obter_fabricante_processador():
    """
    Obtém o fabricante do processador.
    """

    if platform.system() != "Windows":
        return "Não identificado"

    try:
        import winreg

        caminho = (
            r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
        )

        chave = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            caminho
        )

        fabricante, _ = winreg.QueryValueEx(
            chave,
            "VendorIdentifier"
        )

        winreg.CloseKey(chave)

        return fabricante.strip()

    except Exception:
        return "Não identificado"


def obter_informacoes_servidor():
    """
    Coleta todas as informações principais do servidor.
    """

    nome_servidor = socket.gethostname()

    sistema = platform.system()
    versao = platform.version()
    arquitetura = platform.machine()

    sistema_operacional = (
        f"{sistema} - {versao} - {arquitetura}"
    )

    # Tenta obter o nome completo pelo Registro do Windows.
    processador = obter_nome_processador_windows()

    # Caso não consiga, utiliza platform.processor().
    if not processador:
        processador = platform.processor()

    if not processador:
        processador = "Não identificado"

    fabricante = obter_fabricante_processador()

    # Núcleos físicos.
    nucleos_fisicos = psutil.cpu_count(logical=False)

    if nucleos_fisicos is None:
        nucleos_fisicos = 0

    # Processadores lógicos.
    # Em máquinas com Hyper-Threading/SMT,
    # normalmente representa a quantidade de threads
    # disponíveis para o sistema operacional.
    processadores_logicos = psutil.cpu_count(logical=True)

    if processadores_logicos is None:
        processadores_logicos = 0

    # Frequência.
    frequencia = psutil.cpu_freq()

    if frequencia:
        frequencia_maxima = frequencia.max
    else:
        frequencia_maxima = 0

    return {
        "nome_servidor": nome_servidor,
        "sistema_operacional": sistema_operacional,
        "processador": processador,
        "fabricante_processador": fabricante,
        "nucleos_fisicos": nucleos_fisicos,
        "processadores_logicos": processadores_logicos,
        "frequencia_maxima_mhz": frequencia_maxima
    }


# ============================================================
# SALVAR INFORMAÇÕES DO SERVIDOR
# ============================================================

def salvar_informacoes_servidor(info):
    """
    Salva ou atualiza as informações do servidor.
    """

    conn = conectar_banco()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM servidor
    """)

    quantidade = cursor.fetchone()[0]

    if quantidade == 0:

        cursor.execute("""
            INSERT INTO servidor (
                id,
                nome_servidor,
                sistema_operacional,
                processador,
                fabricante_processador,
                nucleos_fisicos,
                processadores_logicos,
                frequencia_maxima_mhz,
                data_primeiro_registro
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            1,
            info["nome_servidor"],
            info["sistema_operacional"],
            info["processador"],
            info["fabricante_processador"],
            info["nucleos_fisicos"],
            info["processadores_logicos"],
            info["frequencia_maxima_mhz"],
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ))

    else:

        cursor.execute("""
            UPDATE servidor
            SET nome_servidor = ?,
                sistema_operacional = ?,
                processador = ?,
                fabricante_processador = ?,
                nucleos_fisicos = ?,
                processadores_logicos = ?,
                frequencia_maxima_mhz = ?
            WHERE id = 1
        """, (
            info["nome_servidor"],
            info["sistema_operacional"],
            info["processador"],
            info["fabricante_processador"],
            info["nucleos_fisicos"],
            info["processadores_logicos"],
            info["frequencia_maxima_mhz"]
        ))

    conn.commit()
    conn.close()


# ============================================================
# COLETA DA CPU
# ============================================================

def coletar_cpu():
    """
    Mede a utilização total da CPU.

    interval=1 faz o psutil calcular a utilização durante
    aproximadamente um segundo.
    """

    uso = psutil.cpu_percent(
        interval=INTERVALO_CPU
    )

    return uso


# ============================================================
# SALVAR MEDIÇÃO
# ============================================================

def salvar_medicao(uso_cpu):
    """
    Salva uma medição no banco.
    """

    agora = datetime.now()

    conn = conectar_banco()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO monitoramento (
            data_hora,
            data,
            uso_cpu
        )
        VALUES (?, ?, ?)
    """, (
        agora.strftime("%Y-%m-%d %H:%M:%S"),
        agora.strftime("%Y-%m-%d"),
        uso_cpu
    ))

    conn.commit()
    conn.close()


# ============================================================
# OBTER ESTATÍSTICAS DO DIA
# ============================================================

def obter_estatisticas(data):
    """
    Obtém quantidade de medições, média, mínimo e máximo.
    """

    conn = conectar_banco()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*),
            AVG(uso_cpu),
            MIN(uso_cpu),
            MAX(uso_cpu)
        FROM monitoramento
        WHERE data = ?
    """, (data,))

    resultado = cursor.fetchone()

    conn.close()

    quantidade = resultado[0]

    if quantidade == 0:
        return None

    return {
        "quantidade": quantidade,
        "media": resultado[1],
        "minimo": resultado[2],
        "maximo": resultado[3]
    }


# ============================================================
# GERAR RELATÓRIO CSV
# ============================================================

def gerar_relatorio_csv(data):
    """
    Gera o relatório diário em CSV.
    """

    estatisticas = obter_estatisticas(data)

    if not estatisticas:
        print(
            f"[RELATORIO] Sem dados para {data}."
        )
        return

    conn = conectar_banco()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            nome_servidor,
            sistema_operacional,
            processador,
            fabricante_processador,
            nucleos_fisicos,
            processadores_logicos,
            frequencia_maxima_mhz
        FROM servidor
        WHERE id = 1
    """)

    servidor = cursor.fetchone()

    cursor.execute("""
        SELECT
            data_hora,
            uso_cpu
        FROM monitoramento
        WHERE data = ?
        ORDER BY data_hora
    """, (data,))

    medicoes = cursor.fetchall()

    conn.close()

    arquivo = os.path.join(
        PASTA_RELATORIOS,
        f"relatorio_cpu_{data}.csv"
    )

    with open(
        arquivo,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as csvfile:

        escritor = csv.writer(
            csvfile,
            delimiter=";"
        )

        escritor.writerow([
            "RELATÓRIO DIÁRIO DE MONITORAMENTO DE CPU"
        ])

        escritor.writerow([])

        escritor.writerow([
            "Data",
            data
        ])

        if servidor:

            escritor.writerow([
                "Servidor",
                servidor[0]
            ])

            escritor.writerow([
                "Sistema operacional",
                servidor[1]
            ])

            escritor.writerow([
                "Processador",
                servidor[2]
            ])

            escritor.writerow([
                "Fabricante",
                servidor[3]
            ])

            escritor.writerow([
                "Núcleos físicos",
                servidor[4]
            ])

            escritor.writerow([
                "Processadores lógicos / threads",
                servidor[5]
            ])

            escritor.writerow([
                "Frequência máxima (MHz)",
                round(
                    servidor[6] or 0,
                    2
                )
            ])

        escritor.writerow([])

        escritor.writerow([
            "Quantidade de medições",
            estatisticas["quantidade"]
        ])

        escritor.writerow([
            "Média de utilização da CPU (%)",
            round(
                estatisticas["media"],
                2
            )
        ])

        escritor.writerow([
            "Menor utilização (%)",
            round(
                estatisticas["minimo"],
                2
            )
        ])

        escritor.writerow([
            "Maior utilização (%)",
            round(
                estatisticas["maximo"],
                2
            )
        ])

        escritor.writerow([])

        escritor.writerow([
            "Data/Hora",
            "Uso da CPU (%)"
        ])

        for data_hora, uso in medicoes:

            escritor.writerow([
                data_hora,
                round(uso, 2)
            ])

    print(
        f"[RELATORIO] CSV criado: {arquivo}"
    )


# ============================================================
# GERAR RELATÓRIO TXT
# ============================================================

def gerar_relatorio_txt(data):
    """
    Gera um relatório TXT resumido e legível.
    """

    estatisticas = obter_estatisticas(data)

    if not estatisticas:
        return

    conn = conectar_banco()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            nome_servidor,
            sistema_operacional,
            processador,
            fabricante_processador,
            nucleos_fisicos,
            processadores_logicos,
            frequencia_maxima_mhz
        FROM servidor
        WHERE id = 1
    """)

    servidor = cursor.fetchone()

    conn.close()

    arquivo = os.path.join(
        PASTA_RELATORIOS,
        f"relatorio_cpu_{data}.txt"
    )

    linhas = []

    linhas.append("=" * 65)
    linhas.append(
        "           RELATÓRIO DIÁRIO DE CPU"
    )
    linhas.append("=" * 65)
    linhas.append("")

    linhas.append(
        f"Data....................: {data}"
    )

    if servidor:

        linhas.append(
            f"Servidor................: {servidor[0]}"
        )

        linhas.append(
            f"Sistema operacional.....: {servidor[1]}"
        )

        linhas.append(
            f"Processador.............: {servidor[2]}"
        )

        linhas.append(
            f"Fabricante..............: {servidor[3]}"
        )

        linhas.append(
            f"Núcleos físicos.........: {servidor[4]}"
        )

        linhas.append(
            "Processadores lógicos...: "
            f"{servidor[5]}"
        )

        linhas.append(
            "Threads disponíveis....: "
            f"{servidor[5]}"
        )

        linhas.append(
            "Frequência máxima.......: "
            f"{servidor[6] or 0:.2f} MHz"
        )

    linhas.append("")
    linhas.append("-" * 65)
    linhas.append("UTILIZAÇÃO DA CPU")
    linhas.append("-" * 65)

    linhas.append(
        "Quantidade de medições..: "
        f"{estatisticas['quantidade']}"
    )

    linhas.append(
        "Média...................: "
        f"{estatisticas['media']:.2f}%"
    )

    linhas.append(
        "Mínima..................: "
        f"{estatisticas['minimo']:.2f}%"
    )

    linhas.append(
        "Máxima..................: "
        f"{estatisticas['maximo']:.2f}%"
    )

    linhas.append("")

    linhas.append(
        f"Intervalo de coleta.....: "
        f"{INTERVALO_COLETA} segundos"
    )

    linhas.append(
        f"Gerado em................: "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    linhas.append("")
    linhas.append("=" * 65)

    with open(
        arquivo,
        "w",
        encoding="utf-8"
    ) as txtfile:

        txtfile.write(
            "\n".join(linhas)
        )

    print(
        f"[RELATORIO] TXT criado: {arquivo}"
    )


# ============================================================
# GERAR RELATÓRIO COMPLETO
# ============================================================

def gerar_relatorio(data):
    """
    Gera todos os formatos de relatório.
    """

    print(
        f"[RELATORIO] Gerando relatório de {data}..."
    )

    gerar_relatorio_csv(data)
    gerar_relatorio_txt(data)


# ============================================================
# VERIFICAR RELATÓRIO ANTERIOR
# ============================================================

def verificar_relatorio_anterior():
    """
    Se o programa foi reiniciado e o relatório do dia anterior
    ainda não existe, tenta gerar automaticamente.
    """

    ontem = datetime.now() - timedelta(days=1)

    data_ontem = ontem.strftime(
        "%Y-%m-%d"
    )

    arquivo_csv = os.path.join(
        PASTA_RELATORIOS,
        f"relatorio_cpu_{data_ontem}.csv"
    )

    if not os.path.exists(arquivo_csv):

        gerar_relatorio(data_ontem)


# ============================================================
# EXIBIR INFORMAÇÕES DO SERVIDOR
# ============================================================

def mostrar_informacoes(info):

    print()
    print("=" * 65)
    print("                    CPU MONITOR")
    print("=" * 65)

    print(
        f"Servidor................: "
        f"{info['nome_servidor']}"
    )

    print(
        f"Sistema operacional.....: "
        f"{info['sistema_operacional']}"
    )

    print(
        f"Processador.............: "
        f"{info['processador']}"
    )

    print(
        f"Fabricante..............: "
        f"{info['fabricante_processador']}"
    )

    print(
        f"Núcleos físicos.........: "
        f"{info['nucleos_fisicos']}"
    )

    print(
        f"Processadores lógicos..: "
        f"{info['processadores_logicos']}"
    )

    print(
        f"Threads disponíveis....: "
        f"{info['processadores_logicos']}"
    )

    print(
        f"Frequência máxima.......: "
        f"{info['frequencia_maxima_mhz']:.2f} MHz"
    )

    print("=" * 65)

    print(
        f"Intervalo de coleta.....: "
        f"{INTERVALO_COLETA} segundos"
    )

    print(
        f"Banco de dados..........: "
        f"{BANCO_DADOS}"
    )

    print(
        f"Relatórios..............: "
        f"{PASTA_RELATORIOS}"
    )

    print("=" * 65)
    print()


# ============================================================
# MONITORAMENTO
# ============================================================

def iniciar_monitoramento():

    print()
    print("Inicializando CPU Monitor...")

    # Cria banco/tabelas.
    criar_banco()

    # Obtém informações do servidor.
    info = obter_informacoes_servidor()

    # Salva informações.
    salvar_informacoes_servidor(info)

    # Exibe informações.
    mostrar_informacoes(info)

    # Verifica relatório anterior.
    verificar_relatorio_anterior()

    data_atual = datetime.now().strftime(
        "%Y-%m-%d"
    )

    print(
        "Monitoramento iniciado."
    )

    print(
        "Pressione CTRL+C para encerrar."
    )

    print()

    try:

        while True:

            inicio_ciclo = time.time()

            agora = datetime.now()

            nova_data = agora.strftime(
                "%Y-%m-%d"
            )

            # ------------------------------------------------
            # Mudança de dia
            # ------------------------------------------------

            if nova_data != data_atual:

                print(
                    "[SISTEMA] Mudança de dia detectada."
                )

                # Gera relatório do dia anterior.
                gerar_relatorio(data_atual)

                data_atual = nova_data

            # ------------------------------------------------
            # Coleta CPU
            # ------------------------------------------------

            uso_cpu = coletar_cpu()

            # ------------------------------------------------
            # Salva medição
            # ------------------------------------------------

            salvar_medicao(uso_cpu)

            # ------------------------------------------------
            # Exibe no console
            # ------------------------------------------------

            print(
                f"[{agora.strftime('%Y-%m-%d %H:%M:%S')}] "
                f"CPU: {uso_cpu:6.2f}%"
            )

            # ------------------------------------------------
            # Controle do intervalo
            # ------------------------------------------------

            tempo_decorrido = (
                time.time() - inicio_ciclo
            )

            espera = (
                INTERVALO_COLETA -
                tempo_decorrido
            )

            if espera > 0:

                time.sleep(espera)

    except KeyboardInterrupt:

        print()
        print(
            "Encerrando monitoramento..."
        )

        # Gera relatório do dia atual
        # antes de encerrar.
        gerar_relatorio(data_atual)

        print(
            "CPU Monitor encerrado."
        )


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

if __name__ == "__main__":

    iniciar_monitoramento()
    