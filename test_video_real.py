import sys
sys.path.append('.')
from pipelines.video_pipeline import process_video
import os

video_path = 'data/inputs/01_03__hugging_happy__ISF9SP4G.mp4'
if os.path.exists(video_path):
    result = process_video(video_path)
    print('Video processing result:')
    print(f'Prediction: {result.get("prediction", "N/A")}')
    print(f'Confidence: {result.get("confidence", "N/A")}')
    print(f'Fake frames: {len(result.get("fake_frames", []))}')
    if result.get('fake_frames'):
        print('First few fake frames:')
        for frame in result['fake_frames'][:3]:
            print(f'  Timestamp: {frame["timestamp"]:.2f}s, Score: {frame["score"]:.3f}')
else:
    print(f'Video file not found: {video_path}')