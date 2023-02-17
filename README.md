# Fetch Rewards
## Data Engineering Take Home: ETL off a SQS Queue

### Requirements:
- python3
- boto3
- psycopg2
- cryptography


### Steps to run:
- Clone the repository `git clone https://https://github.com/chaitanya2903/fetch_takehome_asgn.git`
- Open up a different shell, cd into the repo and enter `docker-compose up`
- Once the docker containers are up and running,  type `python fetch_sqs_etl.py` to run the application

### Next Steps:
1. Modularize the code, ideally the part where we get the messages from the queue and loop through them could be a function that takes in db_params and key for encryption as input
2. Update to pass database connection params to the function created as per Step 1, so hardcoded connection params are not present
3. Update the code to pass the AWS credentials to the function created as per Step 1
4. Instead of looping through the messages and inserting the values row by row, write down a single INSERT query could be written to insert all messages.
5. Update the docker-compose so that the app can be run in a docker container.
6. Add scheduling functionality,  maybe using Orchestration tools 

###QnA:
1. How would you deploy this application in production?
Create a new docker container which will contain the application file and can run it. 
Once the docker containers for db and localstack are running the new docker container should be able to run the application.
Use some orchestration tool to schedule and automate running the application like AWS datapipeline or run Apache Airflow on AWS

2. What other components would you want to add to make this production ready?
An orchestration tool for scheduling and automating the task of running. Monitoring tool to keep an eye on the runtime envrionment in production.

3. How can this application scale with a growing dataset?
I am assuming this means that the number of messages increase, so we'd have to increase the visibility time out to account for increase in processing time.
Use a data-lake to store the intermediate messages before transforming and then apply ETL on the data from the data-lake.

4. How can PII be recovered later on?
Use the key used to encrypt the data to decrypt it using cryptography library in python

5. What are the assumptions you made?
The queue will always give out all avaiable messages.
The create_date parameter is the date the message was received.
The processing will be done within the default visibility time out of SQS messages.
App version field which is required to be an integer should only be the first part of the complete app version i.e. 1.2.3 => 1 
The message body will not contain empty values.
The key will be available when decrypting the masked values to original values
Random substitution or shuffling should not be used for masking to successful reversal of masking





