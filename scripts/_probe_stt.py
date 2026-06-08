import os, json, base64, time, requests, urllib3
from dotenv import load_dotenv
load_dotenv()
urllib3.disable_warnings()

API_KEY = os.environ['API_KEY']
FOLDER_ID = os.environ['FOLDER_ID']
headers = {'Authorization': f'Api-Key {API_KEY}', 'x-folder-id': FOLDER_ID, 'Content-Type': 'application/json'}

tts = requests.post('https://tts.api.yandexcloud.kz/tts/v3/utteranceSynthesis',
    headers=headers,
    data=json.dumps({'text': 'привет как дела', 'outputAudioSpec': {'containerAudio': {'containerAudioType': 'WAV'}}, 'hints': [{'voice': 'jane'}]}),
    verify=False)
audio = bytearray()
for line in tts.text.splitlines():
    try:
        chunk = json.loads(line.strip())
        b64 = (chunk.get('result') or chunk).get('audioChunk', {}).get('data', '')
        if b64: audio.extend(base64.b64decode(b64))
    except: pass

body = {
    'recognitionModel': {
        'audioFormat': {'containerAudio': {'containerAudioType': 'WAV'}},
        'languageRestriction': {'languageCode': ['ru-RU']},
    },
    'content': base64.b64encode(bytes(audio)).decode(),
}
resp = requests.post('https://stt.api.yandexcloud.kz/stt/v3/recognizeFileAsync',
    headers=headers, data=json.dumps(body), verify=False)
op_id = resp.json()['id']
print(f'Operation: {op_id}')

for i in range(15):
    time.sleep(2)
    raw = requests.get(f'https://stt.api.yandexcloud.kz/stt/v3/getRecognition?operationId={op_id}', headers=headers, verify=False).text
    print(f'poll {i+1} raw: {raw[:600]}')
    break
