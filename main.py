import os
from dotenv import load_dotenv
from pprint import pprint

from VideoIndexerClient.Consts import Consts
from VideoIndexerClient.VideoIndexerClient import VideoIndexerClient
from pathlib import Path

ApiVersion = '2024-01-01'
ApiEndpoint = 'https://api.videoindexer.ai'
AzureResourceManager = 'https://management.azure.com'

def main():
    load_dotenv()
    ACCOUNT_NAME = os.getenv("AccountName")
    RESOURCE_GROUP = os.getenv("ResourceGroup")
    SUBSCRIPTION_ID = os.getenv("SubscriptionId")
    consts = Consts(ApiVersion, ApiEndpoint, AzureResourceManager, ACCOUNT_NAME, RESOURCE_GROUP, SUBSCRIPTION_ID)

    print(consts)

    # Authenticate

    # create Video Indexer Client
    client = VideoIndexerClient()

    # Get access tokens (arm and Video Indexer account)
    client.authenticate_async(consts)

    LocalVideoPath = Path('Data\\1772077782299.avi').resolve()

    file_video_id = client.file_upload_async(LocalVideoPath, video_name=None, excluded_ai='')
    client.wait_for_index_async(file_video_id)

    insights = client.get_video_async(file_video_id)
    pprint(insights)

if __name__ == "__main__":
    main()
