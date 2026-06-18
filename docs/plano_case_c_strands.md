# Plano Case C — Strands Agents + AWS Serverless (Hacktoon EDN)

> **Objetivo único:** Atender 100% o desafio do Hacktoon conforme o PDF oficial.
> Tudo que não está no enunciado foi removido. Foco total em entregar, testar e apresentar.

---

## O que o Hacktoon pede (checklist oficial)

| # | Requisito | Entregável |
|---|-----------|------------|
| 1 | API serverless que recebe documento de sinistro | `POST /analisar-sinistro` via API Gateway → Lambda |
| 2 | Agente Strands com ferramentas | `Agent()` com `extrair_texto_do_documento` + `salvar_resultado_dynamodb` |
| 3 | Extrair texto com Textract | Tool `@tool` chamando `detect_document_text` |
| 4 | Classificar tipo de documento | system_prompt instrui: BO, Laudo, NF, RG ou Outro |
| 5 | Extrair campos relevantes | data, valor, local, envolvidos |
| 6 | Gerar resumo em linguagem natural | Resumo de 2 frases via LLM |
| 7 | Salvar resultado no DynamoDB | Tool `@tool` com `put_item` |
| 8 | Retornar JSON estruturado | `{id, tipo_documento, resumo, campos_extraidos, processado_em}` |
| 9 | **Bônus:** GET /sinistro/{id} | Lambda separada + rota GET no API Gateway |
| 10 | Demo de 2 min | Chamada ao vivo + JSON + DynamoDB + aprendizados |

---

## Arquitetura (exatamente o que o PDF pede)

```
POST /analisar-sinistro
        │
   API Gateway (HTTP API)
        │
     Lambda (Python 3.12 + Strands Layer)
        │
    Strands Agent (Bedrock Nova Lite)
    ┌────┴────┐
 Textract   DynamoDB
    │
  S3 (documento)
```

---

## Fase 0 — Infra no Console AWS (0–10 min)

### 1. Criar bucket S3
- Console → S3 → Create bucket
- Nome: `docusmart-sinistros`
- Região: `us-east-1`
- Block all public access: ativado
- **Upload imediato** de um documento de teste (PDF ou imagem)

### 2. Criar tabela DynamoDB
- Console → DynamoDB → Create table
- Nome: `sinistros-resultados`
- Partition key: `id` (String)
- Billing mode: On-demand

### 3. Criar função Lambda
- Console → Lambda → Create function
- Runtime: **Python 3.12**
- Architecture: **x86_64**
- **Timeout: 60 segundos** (obrigatório — LLM precisa de tempo)
- Memory: 512 MB

### 4. Adicionar Layer do Strands
- Lambda → Configuration → Layers → Add a layer → Specify an ARN
```
arn:aws:lambda:us-east-1:856699698935:layer:strands-agents-py3_12-x86_64:2
```
> ⚠ **Sem esse Layer o Strands não funciona.** Não precisa instalar nada manualmente.

### 5. Variáveis de ambiente
- Lambda → Configuration → Environment variables
```
AWS_REGION_NAME   = us-east-1
DYNAMO_TABLE_NAME = sinistros-resultados
DOCUMENTS_BUCKET  = docusmart-sinistros
```

### 6. Permissões IAM (Execution Role)
- Lambda → Configuration → Permissions → Execution role → Add permissions
```
AmazonTextractFullAccess
AmazonDynamoDBFullAccess
AmazonS3ReadOnlyAccess
AmazonBedrockFullAccess
```
> ⚠ **O erro mais comum no hackathon é falta de permissão IAM. Confira ANTES de testar.**

---

## Fase 1 — Código da Lambda POST (10–30 min)

Arquivo: `lambda_function.py`

Este é o código que vai no editor da Lambda no console AWS. Copie e cole diretamente.

```python
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
    body = json.loads(event.get('body', '{}'))
    bucket = body.get('bucket')
    key = body.get('key')

    agente = Agent(
        model=BedrockModel(model_id='us.amazon.nova-lite-v1:0'),
        tools=[extrair_texto_do_documento, salvar_resultado_dynamodb],
        system_prompt=(
            'Você é um especialista em análise de sinistros de seguro. '
            'Use as ferramentas disponíveis para: '
            '1) extrair o texto do documento, '
            '2) classificar o tipo: Boletim de Ocorrência, Laudo Médico, '
            'Nota Fiscal, Documento de Identidade ou Outro, '
            '3) extrair campos relevantes: data, valor, local, envolvidos, '
            '4) gerar um resumo de 2 frases, '
            '5) salvar o resultado no DynamoDB. '
            'Responda APENAS com o JSON final, sem texto adicional.'
        )
    )

    resposta = agente(f'Analise o documento no bucket {bucket}, chave {key}')

    texto_resposta = str(resposta)
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

> 💡 Este é o **código exato do enunciado**. Funciona direto. Não adicione complexidade desnecessária.

---

## Fase 2 — API Gateway + Teste end-to-end (30–55 min)

### Criar API Gateway
- Console → API Gateway → Create API → **HTTP API**
- Integração: Lambda (selecionar sua função)
- Rota: `POST /analisar-sinistro`
- Stage: `$default` (auto-deploy ativado)

### Testar com curl
```bash
curl -X POST https://SEU_ENDPOINT/analisar-sinistro \
  -H "Content-Type: application/json" \
  -d '{"bucket": "docusmart-sinistros", "key": "seu-arquivo.pdf"}'
```

### Output esperado (formato exigido pelo Hacktoon)
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

### Validação
- [ ] JSON retornado contém todas as 5 chaves: `id`, `tipo_documento`, `resumo`, `campos_extraidos`, `processado_em`
- [ ] Item apareceu no DynamoDB (Console → DynamoDB → Explore items)

---

## Fase 3 — Bônus: GET /sinistro/{id} (55–75 min)

Crie uma **segunda Lambda** (ou adicione lógica de roteamento à existente):

```python
import json
import boto3
import os

def lambda_handler(event, context):
    sinistro_id = event['pathParameters']['id']
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

No API Gateway: adicionar rota `GET /sinistro/{id}` apontando para essa Lambda.

> ⚠ Essa Lambda precisa da variável `DYNAMO_TABLE_NAME` e permissão `AmazonDynamoDBFullAccess`.

---

## Fase 4 — Preparar Demo (75–90 min)

### O que a demo deve mostrar (exigência do Hacktoon)

1. **Chamada ao vivo** no Postman ou curl enviando um documento real
2. **JSON retornado** na resposta (mostrar as 5 chaves)
3. **Item salvo no DynamoDB** (abrir console AWS e mostrar)
4. **O que aprenderam** sobre o Strands SDK e o que fariam diferente

### Preparação
- [ ] Documento de teste já está no S3
- [ ] Comando curl/Postman já está pronto e testado
- [ ] Saber abrir o DynamoDB no console rapidamente
- [ ] Preparar 2-3 frases sobre aprendizados com Strands

---

## Cronograma (90 minutos — tempo do Hacktoon)

| Bloco | Tempo | O que fazer |
|-------|-------|-------------|
| 0–10 min | 10 min | Criar S3, DynamoDB, Lambda com Layer do Strands, permissões IAM |
| 10–30 min | 20 min | Colar o `lambda_function.py`, testar invocação direto no console Lambda |
| 30–55 min | 25 min | Criar HTTP API no API Gateway, rota POST, teste end-to-end com curl |
| 55–75 min | 20 min | Bônus: Lambda GET + rota GET no API Gateway |
| 75–90 min | 15 min | Preparar demo, testar fluxo completo, ensaiar apresentação |

> 💡 **Siga a ordem exata.** Cada etapa depende da anterior. Não pule para o código antes da infra estar pronta.

---

## Checklist final antes da demo

- [ ] Documento de teste está no S3
- [ ] Layer do Strands está na Lambda
- [ ] Variáveis de ambiente configuradas (`AWS_REGION_NAME`, `DYNAMO_TABLE_NAME`, `DOCUMENTS_BUCKET`)
- [ ] Permissões IAM corretas (Textract, DynamoDB, S3, Bedrock)
- [ ] Timeout da Lambda em 60s ou mais
- [ ] `POST /analisar-sinistro` retorna JSON com as 5 chaves esperadas
- [ ] Item aparece no DynamoDB após chamada
- [ ] (Bônus) `GET /sinistro/{id}` retorna o item salvo
- [ ] Comando curl ou Postman pronto para a demo

---

## Dicas do enunciado (resumo)

| Dica | Por quê |
|------|---------|
| Confie no agente para decidir a ordem das ferramentas | É o conceito do Strands — não codifique fluxo passo a passo |
| Se o agente errar, melhore o `system_prompt` | É a principal alavanca de ajuste |
| Timeout ≥ 60s | LLM precisa de tempo para processar |
| Arquivo já deve estar no S3 antes de chamar Textract | Textract lê do S3, não aceita upload direto |
| DynamoDB não precisa de schema | Salve o dict Python diretamente com `put_item` |
| Use modo Lambda Proxy no API Gateway | Body chega como string — use `json.loads(event['body'])` |
| IAM é o erro #1 | Verifique permissões antes de qualquer teste |
