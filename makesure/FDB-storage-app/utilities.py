from azure.storage.blob import BlobClient
from azure.storage.blob import BlobServiceClient
from azure.cosmosdb.table.tableservice import TableService
import json,os,csv
import pandas as pd
import uuid
from io import BytesIO
from datetime import datetime

def upload_json_to_blob(folder_name,file_name,data):
    '''
    Uploads the document text extracted json in blob
    Param:folder name, file name , dictionary
    Return: none
    
    '''
    connection_string = str(os.environ.get('BLOB_STORAGE_CONNECTION_STRING'))
    blob = BlobClient.from_connection_string(conn_str=connection_string, container_name=str(os.environ.get('CONTAINER_NAME')), blob_name=folder_name+'/'+file_name)
    blob.upload_blob(json.dumps(data))
    

def read_from_blob(folder_name,file_name):
    '''
    Read elements in a blob
    Param:folder name, file name 
    Return: file in bytes
    
    '''
    connection_string = str(os.environ.get('BLOB_STORAGE_CONNECTION_STRING'))
    container_name=os.environ.get('CONTAINER_NAME')
    blob_name=file_name
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client=blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_name)
    streamdownloader=blob_client.download_blob()
    return streamdownloader.readall()

def read_blob_batch(folder_name):
    '''
    Read elements of a folder in azure storage
    Param:folder name 
    Return: file in bytes
    
    '''
    container_name=os.environ.get('CONTAINER_NAME')
    blob_service_client = BlobServiceClient.from_connection_string(str(os.environ.get('BLOB_STORAGE_CONNECTION_STRING')), container_name=container_name)
    container_client=blob_service_client.get_container_client(container_name)
    blob_list = container_client.list_blobs(name_starts_with=folder_name+"/")
    return blob_list

def write_to_csv(response,csv_file):
    # response=json.loads(response)
    with open(csv_file,'a',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=response.keys())
        writer.writerow(response)

#create table service in azure tables
table_service=TableService(connection_string=os.environ.get('BLOB_STORAGE_CONNECTION_STRING'))

# def upload_to_table(file2,response):
#     # try:
#         data=pd.DataFrame(response)
#         df2=pd.read_csv(BytesIO(file2))
#         # try:
#         table_service.create_table(os.environ.get('TABLE_NAME'))
#         # except Exception as e:
#         #     print(e)
#         df2.rename(columns = {"NDCF": "NDC"},inplace = True)
#         if 'NDC' in data.columns:
#             df3=data.merge(df2[['ProprietaryName','DocID','SetID','NDC','S3Key',]],on='NDC',how='left')
#         for _, row in df3.iterrows():
#             entity={
#                 'PartitionKey':str(row['Storage_Condition']),
#                 'RowKey':str(uuid.uuid4()),
#                 'NDC':str(row['NDC']),
#                 'Status':str(row['Status']),
#                 'Reason':str(row['Reason']),
#                 'created_date':str(row['created_date']),
#                 'Drug_Name':str(row['ProprietaryName']),
#                 'DocID':str(row['DocID']),
#                 'SetID':str(row['SetID']),
#                 'S3Key':str(row['S3Key'])
#             }
#             table_service.insert_entity(os.environ.get('TABLE_NAME'),entity)
#     # except Exception as e:
#     #      print(e)


def upload_to_table(response,final_df):
    try:
        table_service.create_table(os.environ.get('TABLE_NAME'))
    except Exception as e:
        print(e)
    
    for _, row in final_df.iterrows():
            # ipdb.set_trace()
            entity={
                'PartitionKey':str(row['Storage_Condition']),
                'RowKey':str(row['GUID']),
                'NDC':str(row['NDC']),
                'NDC10':str(row['NDC']),
                'NDC11':str(row['NDC11']),
                'Status':str(row['Status']),
                'Reason':str(row['Reason']),
                #'Created_Date':row['created_date'],
                'Created_Date':datetime.now(),
                'Drug_Name':str(row['ProprietaryName']),
                'DocID':str(row['DocID']),
                'SetID':str(row['SetID']),
                'S3Key':str(row['S3Key']),
                'Prompt':str(row['prompt_id']),
                'Response':json.dumps(response),
                'Execution_time':str(row['execution_time']),
                'Error_Message':str(row['error_msg']),
                'ImageLoc':str(row['img_loc']),
                "BatchId":str(row['batch_id'])     
            }
            table_service.insert_entity(os.environ.get('TABLE_NAME'),entity)



def upload_img_to_blob(folder_name,file_name,data):
    '''
    Uploads the document image to storage account
    Param:folder name, file name , binary image
    Return: none
    
    '''
    connection_string = str(os.environ.get('BLOB_STORAGE_CONNECTION_STRING'))
    blob = BlobClient.from_connection_string(conn_str=connection_string, container_name=str(os.environ.get('CONTAINER_NAME')), blob_name=folder_name+'/'+file_name)
    blob.upload_blob(data)