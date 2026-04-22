import os
import math
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

def timestamp_to_seconds(timestamp):
    # "0:00:00.404" -> ["0", "00", "00.404"]
    parts = timestamp.split(':')
    hours = float(parts[0])
    minutes = float(parts[1])
    seconds = float(parts[2])
    
    return hours * 3600 + minutes * 60 + seconds

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

    keyframe_info_list = []

    # キーフレームは 'videos' リスト内の各ビデオの 'insights' -> 'shots' の中に含まれます
    if 'videos' in insights:
        for video in insights['videos']:
            print(f"Video ID: {video['id']}")

            insights_data = video.get('insights', {})
            print(f"Insights Data: {json.dumps(insights_data, indent=2)}")  # 追加: insights_dataの内容を表示
            shots = insights_data.get('shots', [])

            for shot in shots:
                print(f"--- Shot ID: {shot.get('id')} ---")

                # ショット内のキーフレームをループ
                keyframes = shot.get('keyFrames', [])
                for kf in keyframes:
                    keyframe_infos = process_key_frames(file_video_id, client, face_client, kf)
                    keyframe_info_list.extend(keyframe_infos)

    keyframes = []

    for idx, info in enumerate(keyframe_info_list):
        for key, value in info.items():
            print(f"Keyframe {idx} - {key}: {value}")
        
        keyframes.append(info)

    degree_info_list = []

    if len(keyframe_info_list) > 0:
        for keyframe in keyframe_info_list:
            print(f"Keyframe Pose: {keyframe.get('pose')}")

            landmark = keyframe.get('landmarks')
            rect = keyframe.get('rect')

            try:
                mouth_degree = math.fabs(math.degrees(math.atan2(landmark.mouth_left.y / rect.height - landmark.mouth_right.y / rect.height, landmark.mouth_left.x / rect.width - landmark.mouth_right.x / rect.width)))
                pupil_degree = math.fabs(math.degrees(math.atan2(landmark.pupil_left.y / rect.height - landmark.pupil_right.y / rect.height, landmark.pupil_left.x / rect.width - landmark.pupil_right.x / rect.width)))
                eyebrow_left_degree = math.fabs(math.degrees(math.atan2(landmark.eyebrow_left_inner.y / rect.height - landmark.eyebrow_left_outer.y / rect.height, landmark.eyebrow_left_inner.x / rect.width - landmark.eyebrow_left_outer.x / rect.width)))
                eyebrow_right_degree = math.fabs(math.degrees(math.atan2(landmark.eyebrow_right_outer.y / rect.height - landmark.eyebrow_right_inner.y / rect.height, landmark.eyebrow_right_outer.x / rect.width - landmark.eyebrow_right_inner.x / rect.width)))

                if mouth_degree > 90:
                        mouth_degree = 180 - mouth_degree
                if pupil_degree > 90:
                        pupil_degree = 180 - pupil_degree
                if eyebrow_left_degree > 90:
                        eyebrow_left_degree = 180 - eyebrow_left_degree
                if eyebrow_right_degree > 90:
                        eyebrow_right_degree = 180 - eyebrow_right_degree

                print(f"  Mouth Degree: {mouth_degree}")
                print(f"  Pupil Degree: {pupil_degree}")
                print(f"  Eyebrow Left Degree: {eyebrow_left_degree}")
                print(f"  Eyebrow Right Degree: {eyebrow_right_degree}")

                degree_info_list.append({
                    "mouth_degree": mouth_degree,
                    "pupil_degree": pupil_degree,
                    "eyebrow_left_degree": eyebrow_left_degree,
                    "eyebrow_right_degree": eyebrow_right_degree
                })                
       
            except (AttributeError, ZeroDivisionError):
                mouth_degree = None

    if len(keyframe_info_list) > 1:
        start_keyframe = keyframe_info_list[0]
        start_degree_info = degree_info_list[0]
        start_time = timestamp_to_seconds(start_keyframe.get('start_time'))

        for i in range(1, len(keyframe_info_list)):
            current_time = timestamp_to_seconds(keyframe_info_list[i].get('start_time'))
            print(f"\nComparing Keyframe at {start_time} with Keyframe at {current_time}...")
            time_diff = current_time - start_time
            print(f"  Time Difference: {time_diff} seconds")

            current_keyframe = keyframe_info_list[i]
            current_degree_info = degree_info_list[i]

            print(f"Comparing Keyframe {i-1} with Keyframe {i}...")

            mouth_degree_diff = math.fabs(start_degree_info['mouth_degree'] - current_degree_info['mouth_degree']) if start_degree_info['mouth_degree'] is not None and current_degree_info['mouth_degree'] is not None else None
            pupil_degree_diff = math.fabs(start_degree_info['pupil_degree'] - current_degree_info['pupil_degree']) if start_degree_info['pupil_degree'] is not None and current_degree_info['pupil_degree'] is not None else None
            eyebrow_left_degree_diff = math.fabs(start_degree_info['eyebrow_left_degree'] - current_degree_info['eyebrow_left_degree']) if start_degree_info['eyebrow_left_degree'] is not None and current_degree_info['eyebrow_left_degree'] is not None else None
            eyebrow_right_degree_diff = math.fabs(start_degree_info['eyebrow_right_degree'] - current_degree_info['eyebrow_right_degree']) if start_degree_info['eyebrow_right_degree'] is not None and current_degree_info['eyebrow_right_degree'] is not None else None

            print(f"  Mouth Degree Difference: {mouth_degree_diff}")
            print(f"  Pupil Degree Difference: {pupil_degree_diff}")
            print(f"  Eyebrow Left Degree Difference: {eyebrow_left_degree_diff}")
            print(f"  Eyebrow Right Degree Difference: {eyebrow_right_degree_diff}")

            mouth_degree_diff_velo = mouth_degree_diff / time_diff if mouth_degree_diff is not None else None
            pupil_degree_diff_velo = pupil_degree_diff / time_diff if pupil_degree_diff is not None else None
            eyebrow_left_degree_diff_velo = eyebrow_left_degree_diff / time_diff if eyebrow_left_degree_diff is not None else None
            eyebrow_right_degree_diff_velo = eyebrow_right_degree_diff / time_diff if eyebrow_right_degree_diff is not None else None

            print(f"  Mouth Degree Difference velocity: {mouth_degree_diff_velo}")
            print(f"  Pupil Degree Difference velocity: {pupil_degree_diff_velo}")
            print(f"  Eyebrow Left Degree Difference velocity: {eyebrow_left_degree_diff_velo}")
            print(f"  Eyebrow Right Degree Difference velocity: {eyebrow_right_degree_diff_velo}")

            # ここでは単純にピッチ、ロール、ヨーの差を計算してみます
            if 'pose' in start_keyframe and 'pose' in current_keyframe:
                start_pose = start_keyframe['pose']
                current_pose = current_keyframe['pose']

                pitch_diff = abs(start_pose.pitch - current_pose.pitch)
                roll_diff = abs(start_pose.roll - current_pose.roll)
                yaw_diff = abs(start_pose.yaw - current_pose.yaw)

                print(f"  Pitch Difference: {pitch_diff}")
                print(f"  Roll Difference: {roll_diff}")
                print(f"  Yaw Difference: {yaw_diff}")
            
            if 'landmarks' in start_keyframe and 'landmarks' in current_keyframe:
                start_landmarks = start_keyframe['landmarks']
                current_landmarks = current_keyframe['landmarks']

                # 例として、鼻の位置の差を計算してみます
                if hasattr(start_landmarks, 'nose_tip') and hasattr(current_landmarks, 'nose_tip'):
                    nose_diff_x = abs(start_landmarks.nose_tip.x - current_landmarks.nose_tip.x)
                    nose_diff_y = abs(start_landmarks.nose_tip.y - current_landmarks.nose_tip.y)
                    pupil_left_diff_x = abs(start_landmarks.pupil_left.x - current_landmarks.pupil_left.x)
                    pupil_left_diff_y = abs(start_landmarks.pupil_left.y - current_landmarks.pupil_left.y)
                    pupil_right_diff_x = abs(start_landmarks.pupil_right.x - current_landmarks.pupil_right.x)
                    pupil_right_diff_y = abs(start_landmarks.pupil_right.y - current_landmarks.pupil_right.y)
                    mouth_left_diff_x = abs(start_landmarks.mouth_left.x - current_landmarks.mouth_left.x)
                    mouth_left_diff_y = abs(start_landmarks.mouth_left.y - current_landmarks.mouth_left.y)
                    mouth_right_diff_x = abs(start_landmarks.mouth_right.x - current_landmarks.mouth_right.x)
                    mouth_right_diff_y = abs(start_landmarks.mouth_right.y - current_landmarks.mouth_right.y)
                    eyebrow_left_outer_diff_x = abs(start_landmarks.eyebrow_left_outer.x - current_landmarks.eyebrow_left_outer.x)
                    eyebrow_left_outer_diff_y = abs(start_landmarks.eyebrow_left_outer.y - current_landmarks.eyebrow_left_outer.y)
                    eyebrow_left_inner_diff_x = abs(start_landmarks.eyebrow_left_inner.x - current_landmarks.eyebrow_left_inner.x)
                    eyebrow_left_inner_diff_y = abs(start_landmarks.eyebrow_left_inner.y - current_landmarks.eyebrow_left_inner.y)                    

                    print(f"  Nose Tip Difference: X={nose_diff_x}, Y={nose_diff_y}")
                    print(f"  Pupil Left Difference: X={pupil_left_diff_x}, Y={pupil_left_diff_y}")
                    print(f"  Pupil Right Difference: X={pupil_right_diff_x}, Y={pupil_right_diff_y}")
                    print(f"  Mouth Left Difference: X={mouth_left_diff_x}, Y={mouth_left_diff_y}")
                    print(f"  Mouth Right Difference: X={mouth_right_diff_x}, Y={mouth_right_diff_y}")
                    print(f"  Eyebrow Left Outer Difference: X={eyebrow_left_outer_diff_x}, Y={eyebrow_left_outer_diff_y}")
                    print(f"  Eyebrow Left Inner Difference: X={eyebrow_left_inner_diff_x}, Y={eyebrow_left_inner_diff_y}")

            # 次の比較のために現在のキーフレームを基準にします
            start_keyframe = current_keyframe
            start_time = current_time

def process_key_frames(file_video_id, client, face_client, kf):
    kf_id = kf.get('id')
    keyframe_infos = []
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
            keyframe_info = process_thumbnail(face_client, thumbnail_id, thumbnail_bytes)
            if keyframe_info:
                keyframe_info['start_time'] = start_time
                keyframe_info['end_time'] = end_time
                keyframe_infos.append(keyframe_info)

    return keyframe_infos

def process_thumbnail(face_client, thumbnail_id, thumbnail_bytes):
    keyframe_info = None

    print(f"    Detecting faces in thumbnail {thumbnail_id}...")
    try:
        detected_faces = face_client.detect(
                                    image_content=thumbnail_bytes,
                                    detection_model="detection_01", # Head Pose取得には 01 が安定しています
                                    recognition_model="recognition_04",
                                    return_face_id=True,
                                    return_face_landmarks=True,     # 眉のために必要
                                    return_face_attributes=["headPose"] # Head Poseを指定
                                )
        if not detected_faces:
            print("      No faces detected.")
        else:
            for face in detected_faces:
                print(f"      Face Info: {face}")
                print(f"      Face ID: {face.face_id}")
                print(f"      Face Rectangle: {face.face_rectangle}")

                fr = face.face_rectangle
                                        # 1. Head Pose (ピッチ, ロール, ヨー)
                if face.face_attributes and face.face_attributes.head_pose:
                    hp = face.face_attributes.head_pose
                    print(f"      Head Pose: Pitch={hp.pitch}, Roll={hp.roll}, Yaw={hp.yaw}")

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
                    print(f"        Eyebrow Left: Outer({landmarks.eyebrow_left_outer}), Inner({landmarks.eyebrow_left_inner})")
                    print(f"        Eyebrow Right: Inner({landmarks.eyebrow_right_inner}), Outer({landmarks.eyebrow_right_outer})")

                    keyframe_info = {"rect": fr, "pose": hp, "landmarks": landmarks}
                                            # 必要に応じて全ランドマークをループなどで表示可能
                else:
                    print("      No landmarks detected for this face.")
    except Exception as e:
        print(f"      Error detecting faces: {e}")
        print(e.__class__.__name__, e)

    return keyframe_info            

if __name__ == "__main__":
    main()
