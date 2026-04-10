import os
from dotenv import load_dotenv
from pprint import pprint

from VideoIndexerClient.Consts import Consts
from VideoIndexerClient.VideoIndexerClient import VideoIndexerClient
from pathlib import Path
import json
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential # 追加
from azure.ai.vision.face import FaceClient
from azure.ai.vision.face.models import (
    FaceDetectionModel, FaceRecognitionModel,
    FaceAttributeTypeDetection03, FaceAttributeTypeRecognition04
)
ApiVersion = '2024-01-01'
ApiEndpoint = 'https://api.videoindexer.ai'
AzureResourceManager = 'https://management.azure.com'

def main():
    load_dotenv()
    ACCOUNT_NAME = os.getenv("AccountName")
    RESOURCE_GROUP = os.getenv("ResourceGroup")
    SUBSCRIPTION_ID = os.getenv("SubscriptionId")

    # Face API credentials
    FACE_ENDPOINT = os.getenv("FACE_ENDPOINT")

    consts = Consts(ApiVersion, ApiEndpoint, AzureResourceManager, ACCOUNT_NAME, RESOURCE_GROUP, SUBSCRIPTION_ID)

    file_video_id = 'f5510yhove'

    # create Video Indexer Client
    client = VideoIndexerClient()

    # Get access tokens (arm and Video Indexer account)
    client.authenticate_async(consts)

    # Initialize FaceClient
    face_client = FaceClient(
        endpoint=FACE_ENDPOINT.strip(),
        credential=DefaultAzureCredential()
    )
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

                        # サムネイル画像を取得したい場合は、thumbnailIdを使用します
                        thumbnail_id = instance.get('thumbnailId') or kf.get('thumbnailId')

                        if thumbnail_id:
                            # サムネイル画像をバイナリとして取得
                            thumbnail_bytes = client.get_thumbnail_async(file_video_id, thumbnail_id)

                            # Face APIで顔検出とランドマーク取得
                            print(f"    Detecting faces in thumbnail {thumbnail_id}...")
                            try:
                                detected_faces = face_client.detect(
                                    image_content=thumbnail_bytes,
                                    detection_model="detection_03",
                                    recognition_model="recognition_04",                                    return_face_id=True,
                                    return_face_landmarks=True
                                )

                                if not detected_faces:
                                    print("      No faces detected.")
                                else:
                                    for face in detected_faces:
                                        print(f"      Face ID: {face.face_id}")
                                        print(f"      Face Rectangle: {face.face_rectangle}")
                                        if face.face_landmarks:
                                            # ランドマーク情報を表示
                                            print(f"      Face Landmarks:")
                                            landmarks = face.face_landmarks
                                            # 主要なランドマークを表示する例
                                            print(f"        Pupil Left: {landmarks.pupil_left}")
                                            print(f"        Pupil Right: {landmarks.pupil_right}")
                                            print(f"        Nose Tip: {landmarks.nose_tip}")
                                            print(f"        Mouth Left: {landmarks.mouth_left}")
                                            print(f"        Mouth Right: {landmarks.mouth_right}")
                                            # 必要に応じて全ランドマークをループなどで表示可能
                                        else:
                                            print("      No landmarks detected for this face.")
                            except Exception as e:
                                print(f"      Error detecting faces: {e}")
                                print(e.__class__.__name__, e)

if __name__ == "__main__":
    main()
