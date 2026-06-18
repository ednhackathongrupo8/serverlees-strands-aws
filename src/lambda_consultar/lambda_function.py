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
