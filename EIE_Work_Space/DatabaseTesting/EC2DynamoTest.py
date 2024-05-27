import boto3
from botocore.exceptions import ClientError

# Create a DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1b')

# Define the table name
table_name = 'Employees'

def create_table():
    try:
        # Create the table
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        # Wait until the table exists
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        print("Table created successfully")
    except ClientError as e:
        print(f"Error creating table: {e}")

def insert_data():
    try:
        table = dynamodb.Table(table_name)
        table.put_item(
            Item={
                'id': '123',
                'name': 'John Doe',
                'age': 30,
                'department': 'Engineering'
            }
        )
        print("Data inserted successfully")
    except ClientError as e:
        print(f"Error inserting data: {e}")

def query_data():
    try:
        table = dynamodb.Table(table_name)
        response = table.get_item(
            Key={
                'id': '123'
            }
        )
        item = response.get('Item')
        if item:
            print("Data retrieved:", item)
        else:
            print("No data found")
    except ClientError as e:
        print(f"Error querying data: {e}")

def update_data():
    try:
        table = dynamodb.Table(table_name)
        table.update_item(
            Key={
                'id': '123'
            },
            UpdateExpression='SET age = :val1',
            ExpressionAttributeValues={
                ':val1': 35
            }
        )
        print("Data updated successfully")
    except ClientError as e:
        print(f"Error updating data: {e}")

def delete_data():
    try:
        table = dynamodb.Table(table_name)
        table.delete_item(
            Key={
                'id': '123'
            }
        )
        print("Data deleted successfully")
    except ClientError as e:
        print(f"Error deleting data: {e}")

def main():
    create_table()
    #insert_data()
    #query_data()
    #update_data()
    #query_data()  # To see the updated data
    #delete_data()
    #query_data()  # To verify deletion

if __name__ == "__main__":
    main()
