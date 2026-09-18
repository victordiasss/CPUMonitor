# CPUMonitor

Monitoramento de utilização da CPU de um servidor Windows, com armazenamento local das medições e geração de relatórios diários.

## Versão

**CPUMonitor 0.1.0**

## Objetivo

O CPUMonitor foi desenvolvido para monitorar um único servidor e registrar informações relacionadas ao processador e sua utilização.

O programa coleta:

- Nome do servidor;
- Sistema operacional;
- Processador;
- Fabricante do processador;
- Núcleos físicos;
- Processadores lógicos / threads;
- Frequência máxima do processador;
- Utilização da CPU.

As medições são armazenadas localmente em um banco de dados SQLite.

## Funcionamento

Por padrão, o programa realiza uma medição a cada **60 segundos**.

Cada amostra utiliza aproximadamente **1 segundo** para calcular a utilização da CPU.

Configuração atual:

```python
INTERVALO_COLETA = 60
INTERVALO_CPU = 1
```

## Modos de coleta

O CPUMonitor possui dois modos:

### 24 horas

Coleta continuamente, 24 horas por dia.

```python
MODO_COLETA = "24H"
```

### 07:00 às 19:00

Coleta somente dentro do período configurado:

```python
MODO_COLETA = "07_19"
```

O horário é definido por:

```python
HORA_INICIO = 7
HORA_FIM = 19
```

Se o programa for iniciado às 10:00 nesse modo, a coleta começa às 10:00 e segue até 19:00.

Se for iniciado antes das 07:00, aguarda o início do período.

## Banco de dados

As medições são armazenadas em:

```text
dados\cpu_monitor.db
```

O banco é criado automaticamente pelo programa.

## Relatórios

Os relatórios são gerados automaticamente na pasta:

```text
relatorios```

São produzidos dois formatos:

```text
relatorio_cpu_YYYY-MM-DD.csv
relatorio_cpu_YYYY-MM-DD.txt
```

Os relatórios apresentam:

- Quantidade de medições;
- Média de utilização da CPU;
- Menor utilização;
- Maior utilização;
- Informações do servidor;
- Informações do processador;
- Modo de coleta;
- Histórico das medições no relatório CSV.

### Cálculo da média

A média de utilização da CPU é calculada considerando todas as medições registradas para o dia:

**Média = soma das utilizações ÷ quantidade de medições**

## Estrutura do projeto

```text
CPUMonitor├── cpu_monitor.py
├── requirements.txt
├── README.md
├── dados│   └── cpu_monitor.db
├── relatorios│   ├── relatorio_cpu_YYYY-MM-DD.csv
│   └── relatorio_cpu_YYYY-MM-DD.txt
└── dist    └── CPUMonitor.exe
```

As pastas `dados`, `relatorios` e `dist` podem ser criadas/geradas durante a execução e compilação.

## Requisitos para execução pelo código-fonte

- Windows;
- Python 3.14 ou compatível;
- `psutil`.

Instalação da dependência:

```powershell
python -m pip install -r requirements.txt
```

## Execução pelo código-fonte

Ative o ambiente virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

Execute:

```powershell
python cpu_monitor.py
```

Para verificar a sintaxe:

```powershell
python -m py_compile cpu_monitor.py
```

## Compilação do executável

Instale o PyInstaller:

```powershell
python -m pip install pyinstaller
```

Compile:

```powershell
pyinstaller --onefile --name CPUMonitor cpu_monitor.py
```

O executável será criado em:

```text
dist\CPUMonitor.exe
```

## Uso do executável

Execute:

```powershell
.\dist\CPUMonitor.exe
```

O programa cria automaticamente as pastas necessárias para o banco de dados e os relatórios.

## Encerramento

Para encerrar o monitoramento durante a execução no console:

```text
CTRL+C
```

Antes de encerrar, o programa gera o relatório do dia atual.

## Observações

- O banco de dados é local e utiliza SQLite.
- Não é necessário um servidor de banco de dados externo.
- O intervalo padrão de coleta é de 60 segundos.
- O programa foi estruturado para posteriormente ser distribuído como executável para Windows Server.

## Autor

Victor Dias
