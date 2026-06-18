# DocuSmart — Case C: Strands Agents + AWS Serverless

![Equipe Grupo 8](frontend/footer.png)

> **Projeto desenvolvido em equipe para o Hackathon Talento Tech #Hack2hire da Escola da Nuvem (EDN) - Grupo 8.**

![AWS](https://img.shields.io/badge/AWS-Serverless-orange)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![License](https://img.shields.io/badge/License-MIT-green)

> **Hacktoon EDN** — Análise inteligente de documentos de sinistro usando Amazon Strands SDK + AWS Serverless.

Este tutorial mostra **todas as etapas** para construir do zero um micro-pipeline serverless que usa o **Strands Agents SDK** para criar um agente de IA que coordena a análise de documentos de sinistro de seguro dentro de uma AWS Lambda.

---

## 📋 O que o projeto faz

1. Recebe via API o nome de um documento armazenado no S3
2. Um **agente Strands** (rodando dentro de uma Lambda) coordena automaticamente:
   - **Extração de texto** do documento via Amazon Textract
   - **Classificação** do tipo: Boletim de Ocorrência, Laudo Médico, Nota Fiscal, Documento de Identidade ou Outro
   - **Extração de campos** relevantes: data, valor, local, envolvidos
   - **Geração de resumo** em linguagem natural (2 frases)
   - **Persistência** do resultado no DynamoDB
3. Retorna um JSON estruturado com a análise completa

---

## 🏗 Arquitetura

```
Cliente (curl / Postman)
        │
   POST /analisar-sinistro
        │
  ┌─────▼──────┐
  │ API Gateway │  (HTTP API, stage $default)
  │  (HTTP API) │
  └─────┬──────┘
        │
  ┌─────▼──────────────────────────────┐
  │  Lambda: docusmart-analisar        │
  │  Python 3.12 + Strands Layer       │
  │                                    │
  │  ┌──────────────────────────────┐  │
  │  │  Strands Agent               │  │
  │  │  (Bedrock Nova Lite)         │  │
  │  │                              │  │
  │  │  Tool 1: extrair_texto       │──┼──► Amazon Textract ──► S3
  │  │  Tool 2: salvar_resultado    │──┼──► DynamoDB
  │  └──────────────────────────────┘  │
  └────────────────────────────────────┘

  GET /sinistro/{id}
        │
  ┌─────▼──────────────────────────────┐
  │  Lambda: docusmart-consultar       │──► DynamoDB
  │  (bônus)                           │
  └────────────────────────────────────┘
```

---

## 🗂 Estrutura do Repositório

```
├── README.md                              # Este tutorial
├── plano_case_c_strands.md                # Plano original do case
├── docs/
│   ├── documentos-teste/                  # Documentos para upload no S3
│   │   ├── documento_teste_sinistro_docusmart.pdf
│   │   ├── laudo_medico_sinistro.pdf
│   │   ├── nota_fiscal_servico_sinistro.pdf
│   │   ├── documento_identidade_rg.pdf
│   │   └── Certificado de Registro e Licenciamento de Veículo.pdf
│   └── referencia/                        # PDF do enunciado do Hacktoon
└── src/
    ├── lambda_analisar/                   # Lambda POST /analisar-sinistro
    │   ├── lambda_function.py
    │   └── requirements.txt
    └── lambda_consultar/                  # Lambda GET /sinistro/{id} (bônus)
        ├── lambda_function.py
        └── requirements.txt
```

---

## 🛠 Serviços AWS Utilizados

| Serviço | Função | Nome/Configuração |
|---------|--------|-------------------|
| **S3** | Armazenamento dos documentos | Bucket: `docusmart-sinistros` |
| **DynamoDB** | Armazenamento dos resultados | Tabela: `sinistros-resultados` |
| **Lambda** | Executa o agente Strands | `docusmart-analisar` + `docusmart-consultar` |
| **API Gateway** | Endpoint REST | HTTP API |
| **Amazon Bedrock** | LLM para classificação e resumo | Modelo: `us.amazon.nova-lite-v1:0` |
| **Amazon Textract** | OCR / extração de texto | `detect_document_text` |

---

## 🚀 Tutorial Passo a Passo

### Etapa 1 — Criar o Bucket S3

1. Acesse o **Console AWS → S3 → Create bucket**
2. Configure:

| Campo | Valor |
|-------|-------|
| Bucket name | `docusmart-sinistros` |
| AWS Region | `us-east-1` (N. Virginia) |
| Block all public access | ✅ Ativado |

3. Clique em **Create bucket**
4. Entre no bucket criado e faça **Upload** dos arquivos da pasta `docs/documentos-teste/`:
   - `documento_teste_sinistro_docusmart.pdf`
   - `laudo_medico_sinistro.pdf`
   - `nota_fiscal_servico_sinistro.pdf`
   - `documento_identidade_rg.pdf`
   - `Certificado de Registro e Licenciamento de Veículo.pdf`

---

### Etapa 2 — Criar a Tabela DynamoDB

1. Acesse o **Console AWS → DynamoDB → Create table**
2. Configure:

| Campo | Valor |
|-------|-------|
| Table name | `sinistros-resultados` |
| Partition key | `id` (tipo: **String**) |
| Sort key | *(deixar vazio)* |
| Table settings | Customize settings |
| Read/write capacity | **On-demand** |

3. Clique em **Create table**

---

### Etapa 3 — Habilitar o Modelo no Amazon Bedrock

1. Acesse o **Console AWS → Amazon Bedrock → Model access** (menu lateral esquerdo)
2. Clique em **Manage model access**
3. Marque o modelo **Amazon Nova Lite** (`us.amazon.nova-lite-v1:0`)
4. Clique em **Save changes** e aguarde o status mudar para **Access granted**

> ⚠️ **Sem esse passo, o agente Strands não conseguirá chamar o LLM e você verá erro de acesso negado.**

---

### Etapa 4 — Criar a Lambda Principal (`docusmart-analisar`)

#### 4.1 — Criar a função

1. Acesse o **Console AWS → Lambda → Create function**
2. Selecione **Author from scratch**
3. Configure:

| Campo | Valor |
|-------|-------|
| Function name | `docusmart-analisar` |
| Runtime | **Python 3.12** |
| Architecture | **x86_64** |

4. Clique em **Create function**

#### 4.2 — Ajustar configurações gerais

1. Na aba **Configuration → General configuration → Edit**:

| Campo | Valor |
|-------|-------|
| Memory | **512 MB** |
| Timeout | **1 min 0 seg** |

> ⚠️ O timeout padrão de 3 segundos **não é suficiente**. O LLM precisa de pelo menos 60 segundos para processar.

#### 4.3 — Adicionar o Layer do Strands Agents SDK

1. Na aba **Code → Layers → Add a layer**
2. Selecione **Specify an ARN**
3. Cole o ARN:

```
arn:aws:lambda:us-east-1:856699698935:layer:strands-agents-py3_12-x86_64:2
```

4. Clique em **Verify** e depois **Add**

> ⚠️ **Este Layer é obrigatório.** Sem ele, o `import strands` vai falhar. Não é necessário instalar pacotes manualmente.

#### 4.4 — Configurar variáveis de ambiente

1. Na aba **Configuration → Environment variables → Edit**
2. Adicione:

| Key | Value |
|-----|-------|
| `AWS_REGION_NAME` | `us-east-1` |
| `DYNAMO_TABLE_NAME` | `sinistros-resultados` |
| `DOCUMENTS_BUCKET` | `docusmart-sinistros` |

3. Clique em **Save**

#### 4.5 — Configurar permissões IAM

1. Na aba **Configuration → Permissions**
2. Clique no nome da **Execution role** (abrirá o IAM em nova aba)
3. Clique em **Add permissions → Attach policies**
4. Busque e adicione estas 4 políticas:

| Política | Motivo |
|----------|--------|
| `AmazonTextractFullAccess` | Permite chamar Textract para OCR |
| `AmazonDynamoDBFullAccess` | Permite ler/gravar na tabela de resultados |
| `AmazonS3ReadOnlyAccess` | Permite ler documentos do bucket S3 |
| `AmazonBedrockFullAccess` | Permite chamar o modelo Nova Lite via Bedrock |

> ⚠️ **Falta de permissão IAM é o erro #1 em hackathons.** Se algo der `AccessDeniedException`, verifique aqui primeiro.

#### 4.6 — Colar o código

1. Volte para a aba **Code** da Lambda
2. Apague o conteúdo padrão de `lambda_function.py`
3. Cole o código abaixo (idêntico ao arquivo `src/lambda_analisar/lambda_function.py`):

```python
"""
Lambda handler para POST /analisar-sinistro.
Código conforme enunciado do Hacktoon EDN — Case C: Strands Agents + AWS Serverless.
"""

import json
import boto3
import uuid
import os
import re
from datetime import datetime
from strands import Agent
from strands.models import BedrockModel
from strands.tools import tool


# --- Ferramenta 1: Extração de texto via Textract ---

@tool
def extrair_texto_do_documento(bucket: str, key: str) -> str:
    """Extrai o texto de um documento usando Amazon Textract."""
    textract = boto3.client('textract')
    try:
        resp = textract.detect_document_text(
            Document={'S3Object': {'Bucket': bucket, 'Name': key}}
        )
        return ' '.join(
            b['Text'] for b in resp['Blocks']
            if b['BlockType'] == 'LINE'
        )
    except Exception as e:
        error_msg = str(e)
        if 'UnsupportedDocumentException' in error_msg or 'pdf' in key.lower():
            import time
            resp_start = textract.start_document_text_detection(
                DocumentLocation={'S3Object': {'Bucket': bucket, 'Name': key}}
            )
            job_id = resp_start['JobId']
            
            while True:
                resp_get = textract.get_document_text_detection(JobId=job_id)
                status = resp_get['JobStatus']
                if status in ['SUCCEEDED', 'FAILED']:
                    break
                time.sleep(0.5)
                
            if status == 'SUCCEEDED':
                blocks = resp_get.get('Blocks', [])
                next_token = resp_get.get('NextToken')
                while next_token:
                    resp_get = textract.get_document_text_detection(JobId=job_id, NextToken=next_token)
                    blocks.extend(resp_get.get('Blocks', []))
                    next_token = resp_get.get('NextToken')
                    
                return ' '.join(
                    b['Text'] for b in blocks
                    if b['BlockType'] == 'LINE'
                )
        raise e


# --- Ferramenta 2: Salvar resultado no DynamoDB ---

@tool
def salvar_resultado_dynamodb(resultado: dict) -> str:
    """Salva o resultado da análise no DynamoDB e retorna o ID gerado."""
    dynamo = boto3.resource('dynamodb')
    table = dynamo.Table(os.environ['DYNAMO_TABLE_NAME'])
    resultado['id'] = str(uuid.uuid4())    
    table.put_item(Item=resultado)
    return resultado['id']


# --- Handler principal ---

def lambda_handler(event, context):
    # Trata chamada via API Gateway Proxy (body como string JSON)
    # ou teste direto no console da Lambda (passando o dict com bucket e key no root)
    if isinstance(event, dict) and 'body' in event:
        body_content = event['body']
        if isinstance(body_content, str):
            try:
                body = json.loads(body_content)
            except Exception:
                body = {}
        elif isinstance(body_content, dict):
            body = body_content
        else:
            body = {}
    elif isinstance(event, dict):
        body = event
    else:
        body = {}

    bucket = body.get('bucket')
    key = body.get('key')

    if not bucket or not key:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Os campos "bucket" e "key" sao obrigatorios. Se estiver testando no console da AWS Lambda, configure um evento de teste com o JSON: {"bucket": "nome-do-bucket", "key": "caminho/do-arquivo.pdf"}'
            })
        }

    agente = Agent(
        model=BedrockModel(model_id='us.amazon.nova-lite-v1:0'),
        tools=[extrair_texto_do_documento, salvar_resultado_dynamodb],
        system_prompt=(
            'Você é um especialista em análise de sinistros de seguro. '
            'Use as ferramentas disponíveis para: '
            '1) extrair o texto do documento usando a ferramenta extrair_texto_do_documento, '
            '2) analisar o texto extraído e classificar o tipo de documento como um destes: '
            'Boletim de Ocorrência, Laudo Médico, Nota Fiscal, Documento de Identidade ou Outro, '
            '3) extrair campos relevantes do texto, '
            '4) gerar um resumo de 2 frases, '
            '5) salvar o resultado no DynamoDB usando a ferramenta salvar_resultado_dynamodb. '
            'IMPORTANTE: ao chamar salvar_resultado_dynamodb, passe um dicionário com EXATAMENTE estas chaves: '
            '{"tipo_documento": "...", "resumo": "resumo de 2 frases", '
            '"campos_extraidos": {"data": "...", "valor": "...", "local": "...", '
            '"envolvidos": ["nome1", "nome2"]}, "processado_em": "data/hora ISO 8601"}. '
            'Após salvar, responda APENAS com o JSON final incluindo o id retornado, sem texto adicional.'
        )
    )

    resposta = agente(f'Analise o documento no bucket {bucket}, chave {key}')

    texto_resposta = str(resposta)
    # Limpa a resposta para retornar estritamente um JSON
    json_match = re.search(r'(\{.*\})', texto_resposta, re.DOTALL)
    if json_match:
        body_str = json_match.group(1)
    else:
        body_str = texto_resposta

    return {
        'statusCode': 200,
        'body': body_str
    }
```

5. Clique em **Deploy**

#### 4.7 — Testar no console da Lambda

1. Clique em **Test → Create new event**
2. Event name: `testeBO`
3. Cole este JSON no corpo do evento:

```json
{
  "bucket": "docusmart-sinistros",
  "key": "documento_teste_sinistro_docusmart.pdf"
}
```

4. Clique em **Test**
5. Aguarde a execução (pode levar 15–40 segundos)
6. Verifique se o retorno contém um JSON com os campos: `id`, `tipo_documento`, `resumo`, `campos_extraidos`, `processado_em`

> 💡 Se funcionar aqui, o código está correto. Qualquer erro nesta etapa é provavelmente de permissão IAM ou Layer faltando.

---

### Etapa 5 — Criar a API Gateway (HTTP API)

#### 5.1 — Criar a API

1. Acesse o **Console AWS → API Gateway → Create API**
2. Escolha **HTTP API → Build**
3. Na tela de integrações:
   - Clique em **Add integration**
   - Integration type: **Lambda**
   - Lambda function: `docusmart-analisar`
   - API name: `docusmart-api`
4. Clique em **Next**

#### 5.2 — Configurar a rota POST

1. Na tela de rotas:
   - Method: **POST**
   - Resource path: `/analisar-sinistro`
   - Integration target: `docusmart-analisar`
2. Clique em **Next**

#### 5.3 — Stage

1. Stage name: `$default` (auto-deploy ativado)
2. Clique em **Next → Create**

#### 5.4 — Copiar a URL do endpoint

Após a criação, copie o **Invoke URL** que aparece na tela. Será algo como:

```
https://abc123def4.execute-api.us-east-1.amazonaws.com
```

---

### Etapa 6 — Testar End-to-End com curl

Execute no terminal:

```bash
curl -X POST https://SEU_ENDPOINT/analisar-sinistro \
  -H "Content-Type: application/json" \
  -d '{"bucket": "docusmart-sinistros", "key": "documento_teste_sinistro_docusmart.pdf"}'
```

#### Resposta esperada

```json
{
  "id": "7f3a91bc-...",
  "tipo_documento": "Boletim de Ocorrência",
  "resumo": "Acidente de trânsito na Av. Paulista em 10/06/2025, envolvendo dois veículos. Sem vítimas.",
  "campos_extraidos": {
    "data": "10/06/2025",
    "local": "Av. Paulista, 1000",
    "valor_prejuizo": "R$ 4.500,00",
    "envolvidos": ["João Silva", "Maria Souza"]
  },
  "processado_em": "2025-06-10T14:23:00Z"
}
```

#### Validação

- [ ] JSON retornado contém as 5 chaves: `id`, `tipo_documento`, `resumo`, `campos_extraidos`, `processado_em`
- [ ] Item apareceu no DynamoDB (Console → DynamoDB → Explore items → `sinistros-resultados`)

---

### Etapa 7 — Bônus: Lambda de Consulta (`docusmart-consultar`)

#### 7.1 — Criar a segunda Lambda

1. **Console AWS → Lambda → Create function**
2. Configure:

| Campo | Valor |
|-------|-------|
| Function name | `docusmart-consultar` |
| Runtime | **Python 3.12** |
| Architecture | **x86_64** |

3. Clique em **Create function**

#### 7.2 — Configurar

- **Variáveis de ambiente:** adicione `DYNAMO_TABLE_NAME` = `sinistros-resultados`
- **Permissões IAM:** adicione `AmazonDynamoDBFullAccess` à execution role

#### 7.3 — Colar o código

Cole o código abaixo (idêntico ao arquivo `src/lambda_consultar/lambda_function.py`):

```python
"""
Lambda handler para GET /sinistro/{id}.
Bônus do Hacktoon EDN — Case C: Strands Agents + AWS Serverless.
"""

import json
import boto3
import os


def lambda_handler(event, context):
    # Aceita parametro via API Gateway (pathParameters)
    # ou teste direto no console da Lambda (passando o id no root)
    sinistro_id = None
    if isinstance(event, dict):
        if 'pathParameters' in event and isinstance(event['pathParameters'], dict):
            sinistro_id = event['pathParameters'].get('id')
        if not sinistro_id:
            sinistro_id = event.get('id')

    if not sinistro_id:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'O parametro "id" e obrigatorio no pathParameters ou diretamente no evento de teste.'})
        }
    dynamo = boto3.resource('dynamodb')
    table = dynamo.Table(os.environ['DYNAMO_TABLE_NAME'])
    resp = table.get_item(Key={'id': sinistro_id})
    item = resp.get('Item', None)

    if not item:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'não encontrado'})
        }

    return {
        'statusCode': 200,
        'body': json.dumps(item, default=str)
    }
```

Clique em **Deploy**.

#### 7.4 — Adicionar rota GET no API Gateway

1. Volte ao **API Gateway → docusmart-api → Routes**
2. Clique em **Create**
3. Configure:
   - Method: **GET**
   - Path: `/sinistro/{id}`
4. Clique em **Create**
5. Vá em **Integrations** → selecione a rota `GET /sinistro/{id}` → **Attach integration → Create and attach**
6. Integration type: **Lambda**
7. Lambda function: `docusmart-consultar`
8. Clique em **Create**

#### 7.5 — Testar a consulta

Use o `id` retornado na etapa anterior:

```bash
curl https://SEU_ENDPOINT/sinistro/7f3a91bc-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

---

## 📄 Resumo dos Endpoints

| Método | Rota | Lambda | Descrição |
|--------|------|--------|-----------|
| `POST` | `/analisar-sinistro` | `docusmart-analisar` | Envia documento para análise pelo agente Strands |
| `GET` | `/sinistro/{id}` | `docusmart-consultar` | Consulta resultado salvo no DynamoDB (bônus) |

---

## ✅ Checklist Final

- [ ] Documentos de teste estão no bucket `docusmart-sinistros`
- [ ] Tabela `sinistros-resultados` existe no DynamoDB
- [ ] Modelo **Nova Lite** habilitado no Amazon Bedrock
- [ ] Layer do Strands está na Lambda `docusmart-analisar`
- [ ] Variáveis de ambiente configuradas (`AWS_REGION_NAME`, `DYNAMO_TABLE_NAME`, `DOCUMENTS_BUCKET`)
- [ ] Permissões IAM corretas (Textract, DynamoDB, S3, Bedrock)
- [ ] Timeout da Lambda em **60 segundos** ou mais
- [ ] `POST /analisar-sinistro` retorna JSON com as 5 chaves esperadas
- [ ] Item aparece no DynamoDB após chamada
- [ ] (Bônus) `GET /sinistro/{id}` retorna o item salvo

---

## 🧠 Como o Strands Agents SDK funciona neste projeto

O diferencial do projeto é que **o agente decide sozinho a ordem de execução das ferramentas**. O código não tem um fluxo rígido tipo "passo 1, passo 2, passo 3". Em vez disso:

1. O `system_prompt` diz **o que** o agente deve fazer (extrair, classificar, resumir, salvar)
2. As `tools` dizem **como** ele pode fazer (Textract para extrair, DynamoDB para salvar)
3. O agente (LLM Nova Lite) decide a **ordem** e **coordena** tudo automaticamente

Isso é o conceito central do Strands SDK: em vez de codificar fluxo passo a passo, você dá ferramentas ao agente e confia nele para orquestrar.

---

## 🐛 Troubleshooting

| Problema | Solução |
|----------|---------|
| `ModuleNotFoundError: No module named 'strands'` | Layer do Strands não está adicionado na Lambda |
| `AccessDeniedException` no Textract | Falta `AmazonTextractFullAccess` na role |
| `AccessDeniedException` no Bedrock | Falta `AmazonBedrockFullAccess` ou modelo não habilitado |
| `Task timed out after 3.00 seconds` | Timeout da Lambda precisa ser ≥ 60 segundos |
| `ResourceNotFoundException` no DynamoDB | Nome da tabela errado ou variável `DYNAMO_TABLE_NAME` não configurada |
| Textract retorna texto vazio | Documento pode ser uma imagem escaneada de baixa qualidade |

---

## 🚀 (Opcional) Deploy Profissional via AWS SAM

Para um ambiente pronto para produção ou MVP estruturado, o repositório conta com um `template.yaml` que provisiona a infraestrutura completa de forma automatizada usando **Infraestrutura como Código (IaC)**.

> 🛡️ **Segurança Reforçada:** O template inclui melhores práticas da AWS, como políticas de retenção de dados (`DeletionPolicy: Retain`), criptografia at-rest no DynamoDB e S3, bloqueio de acesso público ao bucket e versionamento de objetos.

> ⚠️ **Atenção à Região:** A função Lambda utiliza uma Layer do Strands Agents cujo ARN está publicado na região `us-east-1` (Norte da Virgínia). Portanto, **você deve realizar o deploy deste template nesta mesma região**.

Para fazer o deploy automático da infraestrutura completa via CLI:
```bash
sam build
sam deploy --guided
```
*(Durante as perguntas do `--guided`, certifique-se de preencher **AWS Region** como `us-east-1`)*

## 🧪 Testes Locais

Para executar a suíte de testes unitários da aplicação localmente, na pasta do projeto:

```bash
pip install -r requirements.txt
pytest tests/
```
