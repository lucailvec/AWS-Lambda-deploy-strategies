import json, boto3
import os
import uuid
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

table_name = os.environ['DYNAMODB_TABLE_NAME']

client = boto3.resource('dynamodb')
table = client.Table(table_name)

def lambda_handler(event, context):
    method  = event['httpMethod']
    note_id = event['pathParameters'].get('note-id', None) if event['pathParameters'] is not None else None # /api/note/{note-id}
    
    print(f'method: {method} resource: note/{note_id if not note_id else ""}')
    
    if not note_id:# /api/note/
        if method == "GET":
            response = table.scan()#table.query()
            data = response["Items"]
            while "LastEvaluatedKey" in response:
                response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
                data.extend(response['Items'])
            return {
                'statusCode':200,
                'body': json.dumps(data)
            }
        elif method == "POST":
            if not event['body'] or event['body']=="":
                return {
                    'statusCode': 400,
                    'body': "Body empty"
                    }
            body = event['body']
            data = json.loads(body)
            _id = uuid.uuid4()
            description = data.get('description')
            new_item = {
                'uuid': str(_id),
                'description': description
            }
            response  = table.put_item(Item=new_item)
            return {
                'statusCode' : 200,
                'body': json.dumps(new_item)
            }
        else:
            return {
                'statusCode': 405
            }
    else:        # /api/note/{note-id}
        if method == "GET":
            response = table.get_item(Key={'uuid': note_id})
            
            return {
                'statusCode':200,
                'body': json.dumps(response['Item'])
            }
        elif method == "PUT":
            if not event['body'] or json.loads(event['body']).get('description', None)==None:
                return {
                    'statusCode':401,
                    'body': "Description field missing"
                }
            body = json.loads(event['body'])
            new_description = body.get('description')
            response = table.update_item(
                Key={'uuid':note_id},
                UpdateExpression="set  description=:d",
                ExpressionAttributeValues={':d':new_description},
                ReturnValues='ALL_NEW'
                )
            return {
                'statusCode':200,
                'body': json.dumps(response['Attributes'])
            }
        elif method == "DELETE":
            response  = table.delete_item(Key={'uuid':note_id})
            
            return {
                'statusCode':200,
                'body': json.dumps({'uuid':note_id})
            }
        else:
            return {
                'statusCode': 405
            }
