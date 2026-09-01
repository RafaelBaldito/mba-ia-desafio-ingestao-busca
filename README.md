# Desafio MBA Engenharia de Software com IA - Full Cycle

## Pré-requisitos

- Python com um ambiente virtual que tenha as dependências de `requirements.txt` instaladas.
- Docker e Docker Compose.
- Uma chave da OpenAI com acesso aos modelos configurados.
- O arquivo `document.pdf` na raiz do repositório.

## Configuração e execução

1. Crie e ative o ambiente Python, depois instale as dependências:

   ```bash
   python -m venv .venv
   # Linux/macOS
   . .venv/bin/activate
   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

2. Copie o modelo seguro de configuração e preencha somente os valores locais:

   ```bash
   cp .env.example .env
   ```

   Em Windows PowerShell, use `Copy-Item .env.example .env`. Defina `OPENAI_API_KEY`
   em `.env`; mantenha os identificadores de modelo fornecidos no template e configure
   `DATABASE_URL` e `PG_VECTOR_COLLECTION_NAME` para o banco local. Não versione `.env`.

3. Inicie o PostgreSQL com pgVector e aguarde o serviço ficar saudável, incluindo a
   conclusão de `bootstrap_vector_ext`:

   ```bash
   docker compose up -d
   docker compose ps
   ```

4. Com o banco pronto, ingira o PDF fornecido. Esta etapa é obrigatória antes do chat:

   ```bash
   python src/ingest.py
   ```

   O chat exige que `document.pdf` tenha sido ingerido na coleção configurada e que a
   recuperação encontre exatamente dez chunks. Uma coleção indisponível ou com menos de
   dez chunks não produz resposta.

5. Inicie o chat:

   ```bash
   python src/chat.py
   ```

## Uso do chat

O terminal mostra `Faça sua pergunta:` e aceita uma pergunta por vez em `PERGUNTA: `.
Cada pergunta é independente: não há histórico de conversa.

Exemplo de pergunta fundamentada no PDF (substitua pelo assunto efetivamente presente
em `document.pdf`):

```text
PERGUNTA: Qual informação o documento apresenta sobre <assunto do PDF>?
RESPOSTA: <resposta baseada nos chunks recuperados>
```

Exemplo de pergunta fora do contexto:

```text
PERGUNTA: Qual é a capital da França?
RESPOSTA: Não tenho informações necessárias para responder sua pergunta.
```

Para encerrar, envie `sair`, `exit` ou `quit`, ou use EOF/`Ctrl+C`. O programa responde
com `Chat encerrado.`. Uma pergunta vazia pede uma nova entrada; falhas temporárias de
banco ou OpenAI são exibidas de forma segura e permitem tentar outra pergunta.

## Entrega

No momento da liberação, o repositório desta entrega deve estar público no GitHub.
Essa verificação de publicação faz parte da operação de release e não é executada por
estes comandos locais.
