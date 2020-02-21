# Laboratório de Experimentação de Software

## Propósito
Repositório criado para publicar as respostas pertinentes às [atividades 
propostas](https://github.com/xavierlaerte/labex-20.1/blob/master/labs/lab01.md) 
 no [repositório da disciplina](https://github.com/xavierlaerte/labex-20.1).

## Instruções de uso (Linux/MacOS)
Independente do método escolhido, a aplicação irá procurar por um arquivo de 
texto no diretório raíz do projeto chamado `graphql.token` que contém uma chave 
de acesso à API do GitHub para o uso do GraphQL. Caso a aplicação não 
identifique esse arquivo, a mesma irá solicitar que o usuário insira esta chave 
manualmente no prompt do terminal.

### Método recomendado: Container Docker

**Requisitos:**
- [Docker](https://docs.docker.com/install/#supported-platforms)

A partir do diretório raíz do projeto, execute:

- `docker build --rm --no-cache --pull -t zuquim-labex:latest .`
- `docker run -it --rm --name zuquim-labex zuquim-labex`

### Método #2: [venv](https://docs.python.org/3.7/library/venv.html)

**Requisitos:**
- [Python](https://www.python.org/downloads/) >= 3.6
- Módulos Python contidos no arquivo 
[requirements.txt](https://github.com/Zuquim/smelly-octopus/blob/master/requirements.txt)

A partir do diretório raíz do projeto, execute:

- `python3 -m venv venv` (para criar um ambiente virtual local e descartável)
- `source venv/bin/activate` (para ativar o binário python da venv)
- `pip install --no-cache-dir -r requirements.txt` (para instalar os módulos 
necessários)
- `python3 app.py` (para executar a aplicação e ver o resultado)

___
### Informações da Disciplina
* Universidade: **PUC Minas - Praça da Liberdade**
* Curso: **Engenharia de Software**
* Turno: **Noturno**
* Professor: **[Laerte Xavier](https://github.com/xavierlaerte)**  
* Semestre: **2020.1**
