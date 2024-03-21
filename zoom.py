import os
import requests
from dotenv import load_dotenv
import argparse
import json

load_dotenv()
UPSCALE_URL = os.getenv('UPSCALE_URL')
PAI_API_KEY = os.getenv('PAI_API_KEY')
WORK_FOLDER = 'tmp'

def upscale_4x(init_b64: str):
    body = {
        'init_image': init_b64,
        'height': 1024,
        'width': 1024,
        'scale': 2,

        # TODO: Can we do something interesting w/ prompt?
        # Typically just provide the original, but we could add a captioning step, ex. llava
        'prompt': ''
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {PAI_API_KEY}'
    }
    response = requests.post('', json=body, headers=headers)
    if (response.status_code != 200):
        print('Error:', response.text)
        raise Exception(response.text)
    output_b64 = json.loads(response.text)
    return output_b64

def mock_upscale_4x(input_file: str, output_file: str):
    cmd = '''
        ffmpeg -i {input_file} -vf "zoompan=z='min(zoom+0.0025,1.25)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'" -frames:v 1 {output_file}
        '''

def convert_img_to_zoomed_video(input_img_path: str, output_vid_path: str):
    cmd = f'''
        ffmpeg -loop 1 -i {input_img_path} -vf "zoompan=z='min(zoom+0.0035,2.0)':d=125:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'" -t 5 -s 1080x1080 {output_vid_path}
    '''
    os.system(cmd)

def save_last_frame(vid_path: str, output_img_path):
    os.system(f'ffmpeg -sseof -3 -i {vid_path} -update 1 -q:v 1 {output_img_path}')

def infinite_zoom(base_img_path: str, steps: int):
    base_img = base_img_path
    video_segments = []
    for i in range(steps):
        # TODO: resize image to 1024x1024 (or w/e the init size is)

        segment = f'{WORK_FOLDER}/segment-{i}.png'
        convert_img_to_zoomed_video(base_img, segment)
        video_segments.append(segment)

        last_frame_path = f'{WORK_FOLDER}/base-frame-{i}.png'
        save_last_frame(segment, last_frame_path)

        # base_b64 = open(last_frame_path, 'rb').read()
        # upscaled_b64 = upscale_4x(base_b64)

        upscaled_path = f'{WORK_FOLDER}/upscaled-frame-{i}.png'
        # with open(upscaled_path, 'wb') as f:
        #     f.write(upscaled_b64)

        mock_upscale_4x(last_frame_path, upscaled_path)

        base_img = upscaled_path

    print('Done upscaling images.')
    print('Creating video...')
    os.system(f'ffmpeg -r 30 -i {WORK_FOLDER}/upscaled-frame-%d.png -vcodec libx264 -crf 25 -pix_fmt yuv420p zoom.mp4')
    print('Done creating video.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Infinitely zoom in on an image.')
    parser.add_argument('image', help='A path to the init image.')
    parser.add_argument('-s', '--steps', type=int, default=10, help='The number of steps to zoom in.')
    args = parser.parse_args()

    print(f'Running infinite zoom on {args.image} with {args.steps} steps.')

    # TODO: create the WORK_FOLDER if it doesn't exist

    infinite_zoom(args.image, args.steps)
    