import boto3
import json
import psycopg2
import datetime
import sys
from cryptography.fernet import Fernet

def mask_private_data(ip_address, device_id, hash_key):
    '''Returns a tuple containing masked data.

        Parameters:
            ip_address (str): IP Address to be masked
            device_id (str): device_id to be masked
            hash_key (bytes): key used to encrypt data
        Returns:
            masked_tup (tuple(str, str)): Tuple containing masked ip and device_id
    '''
    fernet = Fernet(hash_key)

    #encrypting the data
    masked_ip = fernet.encrypt(ip_address.encode()).decode()
    masked_device_id = fernet.encrypt(device_id.encode()).decode()

    masked_tup = (masked_ip, masked_device_id)
    return masked_tup



def connect_to_db(db_params):
    '''Returns connection object for db if successfully connected otherwise returns None

        Parameters:
            db_params (dict): Database connection params
        Returns:
            db_connection: psycopg2 connection object if connection is successful
            None: if could not connect
    '''
    try:
        db_connection = psycopg2.connect(
            dbname=db_params['DB_NAME'],
            user=db_params['USERNAME'],
            password=db_params['PASSWORD'],
            host=db_params['HOST'],
            port=db_params['PORT']
        )
    except Exception as e:
        print(e)
        return None
    return db_connection

def connect_to_sqs(aws_access_key_id, aws_secret_access_key, endpoint_url):
    '''Returns the boto3 client object for sqs

        Parameters:
            aws_access_key_id (str): AWS Access key Id
            aws_secret_access_key (str): AWS secret access key
            endpoint_url (str): AWS URL endpoint
        Returns:
            None: if unsuccessful
            sqs: SQS client object
    '''

    try:
        sqs = boto3.client('sqs', 
            region_name='us-east-1', 
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            endpoint_url=endpoint_url)
    except Exception as e:
        print(e)
        return None
    return sqs

if __name__ == '__main__':

    QUEUE_URL = "http://localhost:4566/000000000000/login-queue"
    AWS_ACCESS_KEY_ID = 'replace-with-aws-access-key-id'
    AWS_SECRET_ACCESS_KEY = 'replace-with-aws-secret-access-key'
    ENDPOINT_URL = "http://localhost.localstack.cloud:4566"

    #this can be used to decrypt the data again
    HASH_KEY = b'5QlvXGZnbOO_88Lu0a4dhV3XTh81_cqfGue3nvkwUZU='

    #db connection params
    DB_PARAMS = {
        'DB_NAME': 'postgres',
        'USERNAME': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': 5432,
    }
    db_connection = connect_to_db(DB_PARAMS)
    if not db_connection:
        print("Failed to connect to DB, exiting")
        #exit if connection to db failed
        sys.exit()
    
    sqs = connect_to_sqs(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, ENDPOINT_URL)
    if not sqs:
        print("Failed to gain access to SQS, exiting")
        #exit if could not access SQS
        db_connection.close()
        sys.exit()

    cursor = db_connection.cursor()

    insert_query = '''INSERT INTO user_logins(user_id, device_type, masked_ip, masked_device_id, locale, app_version, create_date) 
    VALUES ('{}', '{}', '{}', '{}', '{}', {}, '{}');'''

    response = sqs.receive_message(QueueUrl=QUEUE_URL)
    messages = response['Messages']
    date = datetime.date.today().isoformat()
    
    n = len(messages)
    print(f"Number of Messages: {n}")


    for message in messages:
        receipt_handle = message['ReceiptHandle']
        message_id = message['MessageId']
        #converting the message body into a dictionary
        data_dict = json.loads(message['Body'])
        masked_ip, masked_device_id = mask_private_data(data_dict['ip'], data_dict['device_id'], HASH_KEY)
        data_dict['ip'] = masked_ip
        data_dict['device_id'] = masked_device_id
        data_dict['create_date'] = date

        #app_version should be an integer
        data_dict['app_version'] = int(data_dict['app_version'].split('.')[0])
        try:
            cursor.execute(insert_query.format(
                data_dict['user_id'], 
                data_dict['device_type'], 
                data_dict['ip'], 
                data_dict['device_id'], 
                data_dict['locale'],
                data_dict['app_version'],
                data_dict['create_date']))

            db_connection.commit()
            print(f"Successfully Inserted {json.dumps(data_dict,indent=2)} in the DB.")

            #delete the message from the queue after it has been successfully added to db
            sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=receipt_handle)
            print("Deleted message from queue")
        except Exception as e:
            print(e)
            print(f"Could not insert {json.dumps(data_dict, indent=2)} in the DB")
    

    cursor.close()
    db_connection.close()
            
