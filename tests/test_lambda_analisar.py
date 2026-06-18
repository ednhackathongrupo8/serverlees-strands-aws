import sys
import os
import json
import pytest

# Adiciona o diretório da lambda ao path para importação
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/lambda_analisar')))

from lambda_function import lambda_handler

def test_lambda_missing_body():
    """Testa se a Lambda retorna erro 400 quando o body está vazio."""
    event = {}
    context = {}
    response = lambda_handler(event, context)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert "error" in body

def test_lambda_apigw_payload_missing_keys():
    """Testa o comportamento quando o payload via API Gateway não tem bucket/key."""
    event = {
        "body": "{}"
    }
    context = {}
    response = lambda_handler(event, context)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert "obrigatorios" in body['error']

# Nota: Testes com o Strands SDK real exigem credenciais AWS válidas.
# Para CI/CD, recomendaria mockar as chamadas do boto3 e da classe Agent.
