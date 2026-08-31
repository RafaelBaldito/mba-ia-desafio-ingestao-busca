# Documento de Requisitos de Produto

**Projeto:** Desafio MBA — Ingestão e Busca Semântica com LangChain e Postgres  
**Fonte autoritativa:** `docs/input/PROJECT-BRIEF.md`  
**Status:** APPROVED
**Approval record:** 2026-08-30 — explicit human approval

## 1. Visão geral

O produto é uma aplicação de linha de comando que permite ingerir o conteúdo de um PDF em uma base vetorial PostgreSQL com pgVector e, depois, responder perguntas do usuário exclusivamente com base no conteúdo recuperado desse documento.

O produto deverá possibilitar um fluxo reproduzível: iniciar o banco de dados, ingerir o PDF e executar o chat no terminal.

## 2. Problema e contexto

Informações relevantes podem estar disponíveis em documentos PDF, mas sua consulta manual é pouco prática. O desafio requer uma solução que transforme o conteúdo de um PDF em uma base pesquisável semanticamente e ofereça respostas em linguagem natural sem introduzir conhecimento que não esteja explicitamente presente no contexto recuperado.

## 3. Objetivos

- Ingerir o arquivo `document.pdf` em um armazenamento vetorial PostgreSQL com pgVector.
- Permitir perguntas por uma interface CLI.
- Recuperar os trechos mais relevantes do documento para cada pergunta.
- Produzir respostas fundamentadas somente no contexto recuperado.
- Informar uma resposta padronizada quando a informação não estiver explicitamente disponível no contexto.
- Entregar o projeto em um repositório público no GitHub, com instruções claras de execução.

## 4. Não objetivos

- Responder com conhecimento externo ao PDF ou com inferências, opiniões ou interpretações além do texto recuperado.
- Oferecer interface gráfica, web, API HTTP ou outro canal de interação além da CLI.
- Oferecer suporte ao Gemini; a solução usará OpenAI para embeddings e o modelo `gpt-5.4-mini` para gerar respostas.
- Definir, neste documento, arquitetura, esquema de banco, estratégia de reingestão, tratamento técnico de erros ou pacote exato a ser empregado quando não forem impostos pelo brief.

## 5. Usuário

O usuário é a pessoa que executa a solução localmente, realiza a ingestão do PDF e faz perguntas pelo terminal para consultar o conteúdo do documento.

## 6. Escopo

### Em escopo

- Infraestrutura de banco PostgreSQL com extensão pgVector executável com Docker e Docker Compose.
- Ingestão do PDF de entrada `document.pdf`.
- Divisão do conteúdo em trechos, geração de embeddings e persistência dos vetores.
- Busca semântica dos trechos mais relevantes para uma pergunta.
- Chat interativo em linha de comando que apresenta a resposta da consulta.
- Arquivos de projeto e documentação necessários para reproduzir o fluxo de execução.

### Fora de escopo

- Fontes documentais adicionais além do PDF especificado.
- Respostas que não sejam sustentadas pelo contexto recuperado.
- Requisitos de produto para autenticação, múltiplos usuários, histórico de conversas ou persistência de sessões.
- Garantias de disponibilidade, escala, desempenho ou custo que não constam do brief.

## 7. Requisitos funcionais

| ID | Requisito |
| --- | --- |
| FR-001 | O produto deve disponibilizar `src/ingest.py` para ler o PDF configurado como `document.pdf` e iniciar sua ingestão. |
| FR-002 | Durante a ingestão, o produto deve dividir o conteúdo do PDF em chunks de 1.000 caracteres com sobreposição de 150 caracteres. |
| FR-003 | O produto deve gerar um embedding para cada chunk e armazenar os vetores no PostgreSQL usando pgVector. |
| FR-004 | O produto deve disponibilizar `src/search.py` para realizar a busca semântica usada nas consultas. |
| FR-005 | O produto deve disponibilizar `src/chat.py` como interface de chat em linha de comando. |
| FR-006 | Para cada pergunta recebida no chat, o produto deve gerar a representação vetorial da pergunta e recuperar os 10 resultados mais relevantes da base vetorial. |
| FR-007 | O produto deve concatenar os resultados recuperados para formar o contexto enviado à geração da resposta. |
| FR-008 | O produto deve solicitar uma resposta a uma LLM usando o prompt obrigatório descrito no brief, incluindo o contexto recuperado e a pergunta do usuário. |
| FR-009 | O produto deve responder somente com base no contexto recuperado, sem usar conhecimento externo, inventar conteúdo, emitir opiniões ou fazer interpretações além do que estiver escrito. |
| FR-010 | Quando a informação necessária não estiver explicitamente presente no contexto recuperado, o produto deve responder exatamente: `Não tenho informações necessárias para responder sua pergunta.` |
| FR-011 | O produto deve documentar um fluxo reproduzível para iniciar o banco, executar a ingestão e executar o chat. |

## 8. Requisitos não funcionais

| ID | Requisito |
| --- | --- |
| NFR-001 | A solução deve ser desenvolvida em Python. |
| NFR-002 | A solução deve utilizar LangChain. |
| NFR-003 | O armazenamento vetorial deve utilizar PostgreSQL com pgVector. |
| NFR-004 | O banco de dados deve poder ser executado com Docker e Docker Compose. |
| NFR-005 | A documentação de execução deve ser clara o suficiente para um usuário reproduzir o fluxo esperado. |
| NFR-006 | Mudanças de produção devem possuir testes automatizados significativos, e a cobertura geral do projeto deve ser de pelo menos 90%, conforme as regras do repositório. |

## 9. Restrições e entregáveis

| ID | Restrição ou entregável |
| --- | --- |
| CON-001 | A estrutura de entrega deve conter `docker-compose.yml`, `requirements.txt`, `.env.example`, `src/ingest.py`, `src/search.py`, `src/chat.py`, `document.pdf` e `README.md`. |
| CON-002 | `docker-compose.yml` deve atender à infraestrutura do banco; `requirements.txt` às dependências; `.env.example` ao template de configuração e chaves; e `README.md` às instruções de execução. |
| CON-003 | O PDF de entrada exigido é `document.pdf`. |
| CON-004 | A busca deve usar exatamente `k=10` resultados. |
| CON-005 | O prompt de resposta deve preservar as regras e os exemplos obrigatórios do brief, inclusive a mensagem de ausência de contexto. |
| CON-006 | A entrega deve ser um repositório público no GitHub contendo o código-fonte e um README com instruções claras de execução. |

### Tecnologias e modelos

Python, LangChain, PostgreSQL, pgVector, Docker e Docker Compose são tecnologias obrigatórias. Conforme a instrução atual do projeto, a solução utilizará OpenAI, com `text-embedding-3-small` para embeddings e `gpt-5.4-mini` para geração de respostas. O Gemini não faz parte do escopo do produto.

## 10. Fluxos do usuário e do sistema

1. O usuário inicia a infraestrutura de banco com Docker Compose.
2. O usuário executa `python src/ingest.py`; o sistema lê o PDF, divide seu conteúdo, gera embeddings e persiste os vetores.
3. O usuário executa `python src/chat.py` e informa uma pergunta no terminal.
4. O sistema recupera os 10 chunks mais relevantes, monta o contexto e o prompt obrigatório e obtém a resposta da LLM.
5. O chat apresenta uma resposta fundamentada no contexto ou a mensagem padronizada de ausência de informação.

## 11. Critérios de aceitação

- Com a infraestrutura disponível e a configuração necessária informada, o PDF de entrada pode ser ingerido e seus chunks vetoriais ficam disponíveis para busca no PostgreSQL com pgVector.
- Cada chunk de ingestão respeita os parâmetros de 1.000 caracteres e 150 caracteres de sobreposição.
- Uma pergunta feita pela CLI resulta em busca semântica com 10 resultados recuperados e em uma resposta exibida no terminal.
- Para uma pergunta cuja informação esteja explicitamente no contexto recuperado, a resposta é compatível com esse conteúdo.
- Para pergunta fora do contexto, opinativa ou cuja informação não esteja explicitamente no contexto recuperado, a resposta é exatamente `Não tenho informações necessárias para responder sua pergunta.`
- O README permite reproduzir a sequência de iniciar o banco, ingerir o PDF e usar o chat.
- O repositório de entrega é público e contém os arquivos estruturais exigidos.

## 12. Riscos e dependências de produto

- A ingestão e as respostas dependem de acesso operacional ao PostgreSQL/pgVector, à infraestrutura Docker e à OpenAI para embeddings e geração de respostas.
- A qualidade e a suficiência das respostas dependem do conteúdo do PDF e da recuperação semântica dos trechos relevantes.
- Mudanças em disponibilidade, limites ou custos dos modelos OpenAI podem afetar a execução.

## 13. Premissas

- O usuário fornecerá as credenciais e variáveis de ambiente da OpenAI e do banco, conforme a documentação da solução.
- O arquivo `document.pdf` será o corpus a consultar no fluxo inicial previsto pelo desafio.
- Os detalhes de configuração serão documentados sem expor credenciais reais no repositório.

## 14. Questões em aberto

| ID | Questão | Impacto |
| --- | --- | --- |
| OQ-001 | Qual comportamento deve ocorrer quando não houver API key válida da OpenAI? | Define a experiência de inicialização e falha. |
| OQ-002 | Além da regra de informação explicitamente presente, há critérios objetivos adicionais para decidir se o contexto é suficiente para responder? | Afeta a consistência das respostas de ausência de informação. |
| OQ-003 | Como o CLI deve tratar encerramento, erros e múltiplas perguntas na mesma execução? | Define o ciclo de interação do usuário. |
| OQ-004 | Qual deve ser o comportamento ao reingerir o mesmo PDF? | Afeta duplicação e atualização do conteúdo pesquisável. |
| OQ-005 | Quais comportamentos de produto são esperados para falhas de PDF, banco, embeddings ou LLM? | Define mensagens e recuperabilidade de falhas. |

## 15. Rastreabilidade de requisitos

| Fonte do brief | Requisitos derivados |
| --- | --- |
| Objetivo do desafio; requisitos de ingestão | FR-001 a FR-003 |
| Requisitos de consulta via CLI | FR-004 a FR-007 |
| Prompt obrigatório | FR-008 a FR-010; CON-005 |
| Tecnologias obrigatórias | NFR-001 a NFR-004 |
| Estrutura, ordem de execução e entregável | FR-011; NFR-005; CON-001 a CON-003 e CON-006 |
| Parâmetros explícitos | FR-002, FR-006, CON-004 e seção 9 |
| Instrução atual do usuário | Seção 4 e seção 9 |
| Regras de qualidade do repositório | NFR-006 |

## 16. Aprovação

Este PRD está pronto para revisão humana. A aprovação explícita é necessária antes de iniciar o planejamento de entrega.
