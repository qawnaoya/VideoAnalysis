import os
from dotenv import load_dotenv
from pprint import pprint

from VideoIndexerClient.Consts import Consts
from VideoIndexerClient.VideoIndexerClient import VideoIndexerClient
from pathlib import Path
import json

ApiVersion = '2024-01-01'
ApiEndpoint = 'https://api.videoindexer.ai'
AzureResourceManager = 'https://management.azure.com'

def main():
    load_dotenv()
    ACCOUNT_NAME = os.getenv("AccountName")
    RESOURCE_GROUP = os.getenv("ResourceGroup")
    SUBSCRIPTION_ID = os.getenv("SubscriptionId")
    consts = Consts(ApiVersion, ApiEndpoint, AzureResourceManager, ACCOUNT_NAME, RESOURCE_GROUP, SUBSCRIPTION_ID)

    file_video_id = 'f5510yhove'

    # Authenticate

    # create Video Indexer Client
    client = VideoIndexerClient()

    # Get access tokens (arm and Video Indexer account)
    client.authenticate_async(consts)


    insights = client.get_video_async(file_video_id)

    # キーフレームは 'videos' リスト内の各ビデオの 'insights' -> 'shots' の中に含まれます
    if 'videos' in insights:
        for video in insights['videos']:
            print(f"Video ID: {video['id']}")

            insights_data = video.get('insights', {})
            shots = insights_data.get('shots', [])

            for shot in shots:
                print(f"--- Shot ID: {shot.get('id')} ---")

                # ショット内のキーフレームをループ
                keyframes = shot.get('keyFrames', [])
                for kf in keyframes:
                    kf_id = kf.get('id')
                    # キーフレームの時間情報（instances）を取得
                    for instance in kf.get('instances', []):
                        start_time = instance.get('start')
                        end_time = instance.get('end')
                        print(f"  Keyframe ID: {kf_id} | Start: {start_time} | End: {end_time}")

                        # サムネイル画像を取得したい場合は、このID（kf_id）を使用します

                        thumbnail = client.get_thumbnail_async(file_video_id, kf_id)

                        print(f"    Thumbnail URL: {thumbnail}")

if __name__ == "__main__":
    main()
