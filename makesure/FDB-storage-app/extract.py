
import requests
import json
import openai
# from langchain.llms import AzureOpenAI
import openai
import os
import time
import csv
from dotenv import load_dotenv
import pandas as pd
import re
from typing import List
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain.pydantic_v1 import BaseModel, Field, validator
load_dotenv()

subscription_key= os.environ.get('SUBSCRIPTION_KEY')
deployment_name=os.environ.get('DEPLOYMENT_NAME')

def ocr(img,mime_type='image/jpeg',count=0):

    """

    Ocr extraction from Image or Image at local path

    Input: Image or Image local path

    Output: Cognitive Services OCR output response json

    """
    ocr_out={}
    status_code=0
    try:
        url = "https://visionaiscnonprod1.cognitiveservices.azure.com/vision/v3.2/read/analyze?language=en"
        payload={}
        img_bytes=None
        if type(img)==str:

            files=[('image',('tmp.jpg',open(img,"rb"),mime_type))]

        else:

            img_bytes=img

            files=[('image',('tmp.jpg',img_bytes,mime_type))]

        headers = {'Ocp-Apim-Subscription-Key': subscription_key}

        response = requests.request("POST", url, headers=headers, data=payload, files=files, verify=False)

        status_code = response.status_code
        print('status_code',status_code)
        ocr_out=response.headers
        if status_code== 202:
            url=ocr_out['Operation-Location']
            response = requests.request("GET", url, headers=headers, data=payload, verify=False)
            ocr_out=response.json()
            status_code = response.status_code
            try:
                while ocr_out["status"]=="running":
                    time.sleep(1)
                    response = requests.request("GET", url, headers=headers, data=payload, verify=False)
                    status_code = response.status_code
                    ocr_out=response.json()
            except:
                time.sleep(20)
                
    except Exception as e:
        print(e)
        time.sleep(20)
        
    if status_code in [200,202]:
        pass
    else:
        count+=1
        if count<10:
            return ocr(img,count=count)
            
    return dict(ocr_out),img_bytes


def extract_text(ocr_text):
    try:
        text=''
        for i in ocr_text['analyzeResult']['readResults']:
                    for j,x in enumerate(i['lines']):
                        text='\n'.join([text,x['text']])
        return text
    except:
        return None

def ndc_regex(ocr_text):   
    pattern = r'\b(\d{4}-\d{4}-\d{2}|\d{5}-\d{3}-\d{2}|\d{5}-\d{4}-\d{1}|\d{5}-\d{4}-\d{2})\b'
    match = re.search(pattern, ocr_text)
    if match:
        return match.group(0)
    else:
        return None
    
def ndc_conversion(x):
        print('*')
        if x==None:
            return None
        pattern_11= r'\b(\d{5}-\d{4}-\d{2})\b'
        pattern = r'\b(\d{4}-\d{4}-\d{2}|\d{5}-\d{3}-\d{2}|\d{5}-\d{4}-\d{1})\b'
        match = re.search(pattern_11, x)
        if match:
            return x
        else:
            match = re.search(pattern, x)
            if match:
                l=x.split('-')
                if len(l[0])==5:
                    pass
                else:
                    temp = '{:>05}'
                    l[0] = temp.format(l[0])
                if len(l[1])==4:
                    pass
                else:
                    temp = '{:>04}'
                    l[1] = temp.format(l[1])
                if len(l[2])==2:
                    pass
                else:
                    temp = '{:>02}'
                    l[2] = temp.format(l[2])
                x= '-'.join(l)
                return x
            else:
                return None
    
def get_completion(prompt, model="gpt-3.5-turbo"): 
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0, 
        deployment_id=deployment_name,
    )
    return response.choices[0].message["content"]


class storage(BaseModel):
    NDC: str = Field(description="ndc")
    Storage_Condition: str = Field(description="storage")
    Reason: str = Field(description="Reason")

def llm_response(ocr_text,prompt,ndc):

    # parser = PydanticOutputParser(pydantic_object=storage)

    # prompt = PromptTemplate(
    #     template="Answer the user query.\n{format_instructions}\n{query}\n",
    #     input_variables=["query"],
    #     partial_variables={"format_instructions": parser.get_format_instructions()},
    # )

    # _input = prompt.format_prompt(query=prompt_ocr)
    # print(_input.to_string())
    
    # response from llm model 
    response = get_completion(prompt.format(ocr_text=ocr_text))
    # response = get_completion(_input.to_string())
    print('llm response',response)
    #convert response to json
    response='{'+response.split('{')[1]
    response=response.split('}')[0]+'}'
    response=json.loads(response)
    
    ## validation script
         
    llm_ndc=response['NDC']
    
    #convert ndc into standard format
    llm_ndc=ndc_conversion(llm_ndc)
    
    if  llm_ndc==None or llm_ndc=='':
        response['NDC']=ndc
    else:
        response['NDC']=llm_ndc

    return response

def response_validation(response):
     if response.get('NDC')!=None and response.get('Storage_Condition')!=None and response.get('Reason')!=None:
         return True
     else:
         return False

def unique_ndc(results):
    df=pd.DataFrame(columns=results.columns)
    k=results.groupby('NDC').groups.keys()
    results=results.drop_duplicates(['NDC','Storage_Condition'])
    for i in k:
        df_ndc=results[results["NDC"]==i]
        und_count=df_ndc[df_ndc['Storage_Condition']=='Undetermined'].shape[0]
        st_count=df_ndc[df_ndc['Storage_Condition']!='Undetermined'].shape[0]
        if st_count>1:
            df_ndc['Storage_Condition']='Undetermined'
            df_ndc['Reason']='Ambiguity in storage conditions'
            df=pd.concat([df, df_ndc.iloc[0:1,:]],axis=0)
        elif st_count==1:
            df=pd.concat([df,  df_ndc[df_ndc['Storage_Condition']!='Undetermined']],axis=0)
        elif und_count==1 and st_count==0:
            df=pd.concat([df, df_ndc[df_ndc['Storage_Condition']=='Undetermined']],axis=0)
    return df


