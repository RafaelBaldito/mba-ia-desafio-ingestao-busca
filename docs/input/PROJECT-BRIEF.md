# Project Brief --- Ingestão e Busca Semântica com LangChain e Postgres

## 1. Origem e finalidade

Este documento registra o enunciado do desafio do MBA **Ingestão e Busca
Semântica com LangChain e Postgres** como fonte de entrada para o
processo de desenvolvimento.

Seu objetivo é preservar os requisitos, restrições, exemplos,
tecnologias e critérios de entrega definidos pelo desafio antes de
qualquer interpretação de produto, decisão arquitetural ou decomposição
técnica.

Este documento deve ser tratado como **input do projeto**.
Interpretações formais devem ser produzidas posteriormente no `PRD.md`.

------------------------------------------------------------------------

## 2. Objetivo do desafio

Entregar um software capaz de:

1.  **Ingestão:** ler um arquivo PDF e salvar suas informações em um
    banco de dados PostgreSQL com extensão **pgVector**.
2.  **Busca:** permitir que o usuário faça perguntas via **linha de
    comando (CLI)** e receba respostas baseadas apenas no conteúdo do
    PDF.

### Exemplo esperado no CLI

``` text
Faça sua pergunta:

PERGUNTA: Qual o faturamento da Empresa SuperTechIABrazil?
RESPOSTA: O faturamento foi de 10 milhões de reais.
```

Para perguntas fora do contexto:

``` text
PERGUNTA: Quantos clientes temos em 2024?
RESPOSTA: Não tenho informações necessárias para responder sua pergunta.
```

------------------------------------------------------------------------

## 3. Tecnologias obrigatórias

-   **Linguagem:** Python
-   **Framework:** LangChain
-   **Banco de dados:** PostgreSQL + pgVector
-   **Execução do banco:** Docker e Docker Compose
-   O `docker-compose` é fornecido no repositório de exemplo.

------------------------------------------------------------------------

## 4. Pacotes e APIs recomendados

O desafio recomenda os seguintes componentes:

### Split de documentos

``` python
from langchain_text_splitters import RecursiveCharacterTextSplitter
```

### Embeddings com OpenAI

``` python
from langchain_openai import OpenAIEmbeddings
```

### Embeddings com Gemini

``` python
from langchain_google_genai import GoogleGenerativeAIEmbeddings
```

### Carregamento de PDF

``` python
from langchain_community.document_loaders import PyPDFLoader
```

### Persistência vetorial

``` python
from langchain_postgres import PGVector
```

### Busca semântica

``` python
similarity_search_with_score(query, k=10)
```

Os pacotes desta seção são apresentados pelo desafio como
**recomendados**, salvo quando outra seção os tornar necessários para
satisfazer um requisito obrigatório.

------------------------------------------------------------------------

## 5. Provedores e modelos

### OpenAI

-   Deve ser criada uma API Key da OpenAI.
-   Modelo de embeddings indicado: `text-embedding-3-small`.
-   Modelo de LLM para geração de resposta: `gpt-5-nano`.

### Gemini

-   Deve ser criada uma API Key da Google.
-   Modelo de embeddings indicado: `models/embedding-001`.
-   Modelos sugeridos para geração de resposta:
    -   `gemini-2.5-flash-lite`;
    -   `gemini-3.1-flash-lite-preview`.
-   Pode ser utilizado outro modelo Gemini, desde que atinja os
    resultados esperados.
-   Os limites gratuitos podem mudar e devem ser consultados na
    documentação oficial do Google quando necessário.

O enunciado apresenta configurações para OpenAI e Gemini. A
interpretação exata sobre obrigatoriedade, alternativa entre provedores
ou suporte simultâneo deve ser formalizada no PRD sem inventar
requisitos não expressos no desafio.

------------------------------------------------------------------------

## 6. Requisitos de ingestão do PDF

O processo de ingestão deve:

1.  ler o PDF fornecido;
2.  dividir o conteúdo em **chunks de 1000 caracteres**;
3.  utilizar **overlap de 150 caracteres** entre chunks;
4.  converter cada chunk em embedding;
5.  armazenar os vetores no PostgreSQL utilizando pgVector.

------------------------------------------------------------------------

## 7. Requisitos de consulta via CLI

Deve existir um script Python que simule um chat no terminal.

Ao receber uma pergunta do usuário, o software deve:

1.  vetorizar a pergunta;
2.  buscar os **10 resultados mais relevantes (`k=10`)** no banco
    vetorial;
3.  concatenar os resultados recuperados para formar o contexto;
4.  montar o prompt definido pelo desafio;
5.  chamar a LLM;
6.  retornar a resposta ao usuário.

------------------------------------------------------------------------

## 8. Prompt obrigatório

O prompt a ser utilizado é:

``` text
CONTEXTO:
{resultados concatenados do banco de dados}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta do usuário}

RESPONDA A "PERGUNTA DO USUÁRIO"
```

A resposta deve ser produzida somente com base no contexto recuperado.

Quando a informação necessária não estiver explicitamente no contexto, a
resposta esperada é:

``` text
Não tenho informações necessárias para responder sua pergunta.
```

------------------------------------------------------------------------

## 9. Estrutura obrigatória do projeto

O desafio determina o uso da estrutura fornecida pelo repositório-base:

``` text
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── src/
│   ├── ingest.py
│   ├── search.py
│   └── chat.py
├── document.pdf
└── README.md
```

Responsabilidades indicadas pelo enunciado:

-   `docker-compose.yml` --- infraestrutura do banco;
-   `requirements.txt` --- dependências;
-   `.env.example` --- template de configuração/API Key;
-   `src/ingest.py` --- script de ingestão do PDF;
-   `src/search.py` --- script de busca;
-   `src/chat.py` --- CLI para interação com o usuário;
-   `document.pdf` --- documento utilizado na ingestão;
-   `README.md` --- instruções de execução.

Repositório-base:

`https://github.com/devfullcycle/mba-ia-desafio-ingestao-busca/`

------------------------------------------------------------------------

## 10. Ambiente virtual Python

O enunciado orienta a criação e ativação de ambiente virtual antes da
instalação das dependências:

``` bash
python3 -m venv venv
source venv/bin/activate
```

A forma exata de ativação pode variar conforme o sistema operacional e
ambiente de desenvolvimento, sem alterar o requisito funcional do
projeto.

------------------------------------------------------------------------

## 11. Ordem de execução esperada

### 1. Subir o banco de dados

``` bash
docker compose up -d
```

### 2. Executar a ingestão do PDF

``` bash
python src/ingest.py
```

### 3. Executar o chat

``` bash
python src/chat.py
```

A solução entregue deve permitir que esse fluxo seja documentado e
reproduzido.

------------------------------------------------------------------------

## 12. Entregável

O entregável exigido é:

1.  **Repositório público no GitHub** contendo:
    -   todo o código-fonte;
    -   `README.md` com instruções claras para execução do projeto.

------------------------------------------------------------------------

## 13. Repositórios de referência

### Curso de nivelamento com LangChain

`https://github.com/devfullcycle/mba-ia-niv-introducao-langchain/`

### Template básico / estrutura do projeto

`https://github.com/devfullcycle/mba-ia-desafio-ingestao-busca/`

Esses repositórios são referências fornecidas pelo desafio. O
template-base define a estrutura inicial exigida; materiais de
nivelamento não devem ser tratados automaticamente como requisitos
adicionais.

------------------------------------------------------------------------

## 14. Restrições e parâmetros explícitos

Os seguintes parâmetros são explicitamente definidos pelo desafio e
devem ser preservados nas etapas posteriores:

  Item                      Valor
  ------------------------- ------------------------------------
  Linguagem                 Python
  Framework                 LangChain
  Banco                     PostgreSQL + pgVector
  Infraestrutura do banco   Docker + Docker Compose
  Chunk size                1000 caracteres
  Chunk overlap             150 caracteres
  Resultados da busca       `k=10`
  OpenAI embedding          `text-embedding-3-small`
  OpenAI LLM                `gpt-5-nano`
  Gemini embedding          `models/embedding-001`
  Interface                 CLI
  Fonte das respostas       Somente contexto recuperado do PDF
  PDF de entrada            `document.pdf`
  Script de ingestão        `src/ingest.py`
  Script de busca           `src/search.py`
  Script de chat            `src/chat.py`

------------------------------------------------------------------------

## 15. Pontos que exigem interpretação posterior

O enunciado contém aspectos que devem ser esclarecidos ou formalizados
durante a criação do PRD/TECHSPEC, sem alterar este Project Brief:

-   relação entre suporte OpenAI e Gemini: alternativa, escolha de
    implementação ou suporte simultâneo;
-   quais itens da lista de pacotes recomendados serão utilizados
    efetivamente;
-   comportamento de configuração quando uma API Key não estiver
    disponível;
-   critérios objetivos adicionais para determinar se o contexto
    recuperado é suficiente para responder;
-   comportamento do CLI para encerramento, erros e múltiplas perguntas;
-   estratégia de reingestão do mesmo PDF;
-   tratamento de falhas de PDF, banco, embeddings ou LLM;
-   requisitos de testes além dos quality gates definidos pelo próprio
    repositório.

Esses pontos não devem ser respondidos neste documento por suposição.
Devem ser tratados pelas etapas apropriadas do workflow.

------------------------------------------------------------------------

## 16. Regra de preservação

Este arquivo representa a fonte de entrada do desafio.

Ele não deve ser alterado para refletir decisões tomadas posteriormente
em:

-   `PRD.md`;
-   `DELIVERY-PLAN.md`;
-   arquitetura;
-   TECHSPECs;
-   tasks;
-   implementação.

Quando uma interpretação do enunciado precisar ser revisada, a alteração
deve ocorrer no artefato derivado correspondente, preservando este
Project Brief como referência original.
