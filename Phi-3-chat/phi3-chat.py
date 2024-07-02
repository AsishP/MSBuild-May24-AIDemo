from azure.search.documents.indexes import SearchIndexerClient
from azure.ai.ml import MLClient
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
import os
import azure.identity.aio
import asyncio
from chat import ChatThread, create_search_client, create_openai_client, SearchType

## Load variables and environment variables
print("\n Loading Variables: \n")
load_dotenv()
k=50
search_type="text"
use_semantic_reranker=False
sources_to_include=5

## Get secrets from Azure Key Vault
print("\n Fetching values from Key Vault \n")
keyvault_url = os.getenv("AZURE_KEYVAULT_URL")
secret_client = SecretClient(vault_url=keyvault_url, credential=DefaultAzureCredential())
subscriptionGUID = secret_client.get_secret(os.getenv("AZURE_KEYVAULT_SECRET_NAME")).value
searchKey = secret_client.get_secret(os.getenv("AZURE_KEYVAULT_SEARCHKEY")).value

# Phi-3 Chat Example
print("\n Connecting to Azure AI Studio instance to fetch Phi-3 deployment \n")
workspace_ml_client = MLClient(
    DefaultAzureCredential(),
    subscription_id=subscriptionGUID,
    resource_group_name=os.getenv("AZURE_RESOURCE_GROUP"),
    workspace_name=os.getenv("AZUREAI_PROJECT_NAME")
)

phi3_url = workspace_ml_client.serverless_endpoints.get(name=os.getenv("AZUREAI_ONLINE_ENDPOINT_NAME")).scoring_uri
phi3_key = workspace_ml_client.serverless_endpoints.get_keys(name=os.getenv("AZUREAI_ONLINE_ENDPOINT_NAME")).primary_key

chat_thread = ChatThread()

print("\n Searching and displaying results using Phi-3 Mini model ...")
async def chat_caller():
    async with create_search_client(AzureKeyCredential(searchKey)) as search_client:
        await chat_thread.append_grounded_message(
            search_client=search_client,
            query="What is included in my Northwind Health Plus plan that is not in standard?",
            search_type=SearchType(search_type),
            use_semantic_reranker=use_semantic_reranker,
            sources_to_include=sources_to_include,
            k=k)
        await chat_thread.get_phi3_response(
            endpoint_scoring_uri=phi3_url + "/v1/chat/completions",
            endpoint_authorization="Bearer " + phi3_key,
            deployment=os.getenv("AZUREAI_DEPLOYMENT_NAME"),
            max_new_tokens=1024)

asyncio.run(chat_caller())
print("\n Phi-3 Chat output: \n")
print(chat_thread.get_last_message()["content"])

# GPT Chat Example
chat_deployment = os.getenv("AZURE_OPENAI_GPT4_DEPLOYMENT_NAME") # replace with AZURE_OPENAI_GPT35TURBO_DEPLOYMENT_NAME to use gpt-35-turbo

print("\n Searching and displaying results using GPT model...")
async def gptchat_caller():
    async with azure.identity.aio.DefaultAzureCredential() as credential, create_search_client(AzureKeyCredential(searchKey)) as search_client, create_openai_client(credential) as openai_client:
        await chat_thread.append_grounded_message(
            search_client=search_client,
            query="What is included in my Northwind Health Plus plan that is not in standard?",
            search_type=SearchType(search_type),
            use_semantic_reranker=use_semantic_reranker,
            sources_to_include=sources_to_include,
            k=k)
        await chat_thread.get_openai_response(openai_client=openai_client, model=chat_deployment, max_new_tokens=1024)

print("\n GPT Chat output: \n")
print(chat_thread.get_last_message()["content"])