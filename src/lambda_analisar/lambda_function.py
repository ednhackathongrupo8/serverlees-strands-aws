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
    """Salva o resultado da análise no DynamoDB e retorna os dados completos salvos em JSON."""
    dynamo = boto3.resource('dynamodb')
    table = dynamo.Table(os.environ['DYNAMO_TABLE_NAME'])
    resultado['id'] = str(uuid.uuid4())    
    table.put_item(Item=resultado)
    return json.dumps(resultado, default=str)


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
