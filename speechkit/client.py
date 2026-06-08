import base64
import json
import time
import requests
from dotenv import load_dotenv
load_dotenv(override=True)


class SpeechKitError(Exception):
    pass


class SpeechKitClient:
    def __init__(self, api_key: str, folder_id: str, timeout: int = 120):
        if not api_key:
            raise EnvironmentError("API_KEY is not set. Add it to your .env file.")
        if not folder_id:
            raise EnvironmentError("FOLDER_ID is not set. Add it to your .env file.")
        self._api_key = api_key
        self._folder_id = folder_id
        self._timeout = timeout
        self._headers = {
            "Authorization": f"Api-Key {api_key}",
            "x-folder-id": folder_id,
            "Content-Type": "application/json",
        }

    def _request(self, method: str, url: str, max_retries: int = 3, **kwargs):
        import os, urllib3
        verify = os.environ.get("SSL_VERIFY", "true").lower() not in ("0", "false", "no")
        if not verify:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        # Use proxy from environment; skip if empty or missing host
        proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") \
             or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy") or ""
        proxy = proxy.strip()
        proxies = {"https": proxy, "http": proxy} if proxy and "://" in proxy else None
        delay = 1.0
        for attempt in range(max_retries):
            try:
                resp = requests.request(
                    method, url,
                    headers=self._headers,
                    timeout=self._timeout,
                    verify=verify,
                    proxies=proxies,
                    **kwargs,
                )
            except (requests.Timeout, requests.ConnectionError) as exc:
                if attempt == max_retries - 1:
                    raise SpeechKitError(f"Request failed after {max_retries} attempts: {exc}") from exc
                time.sleep(delay)
                delay *= 2
                continue

            if resp.status_code in (500, 502, 503, 504):
                if attempt == max_retries - 1:
                    raise SpeechKitError(f"Server error {resp.status_code}: {resp.text}")
                time.sleep(delay)
                delay *= 2
                continue

            if not resp.ok:
                raise SpeechKitError(f"API error {resp.status_code}: {resp.text}")

            return resp
        raise SpeechKitError("Max retries exceeded")

    def tts_synthesize(self, text: str, lang: str = "ru-RU", voice: str = "jane", fmt: str = "WAV") -> bytes:
        """v3 utteranceSynthesis — returns raw audio bytes decoded from streaming JSON chunks."""
        from config import TTS_URL
        body = {
            "text": text,
            "outputAudioSpec": {"containerAudio": {"containerAudioType": fmt}},
            "hints": [{"voice": voice}],
        }
        resp = self._request("POST", TTS_URL, data=json.dumps(body))
        # Response is a stream of JSON lines, each may contain audioChunk.data (base64)
        audio = bytearray()
        for line in resp.text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                chunk = json.loads(line)
            except json.JSONDecodeError:
                continue
            b64 = (chunk.get("result") or chunk).get("audioChunk", {}).get("data", "")
            if b64:
                audio.extend(base64.b64decode(b64))
        return bytes(audio)

    def stt_recognize(self, pcm: bytes, rate: int, lang: str = "ru-RU") -> str:
        """v3 recognizeFileAsync — submit then fetch via getRecognition (streaming JSON lines)."""
        from config import STT_URL
        audio_b64 = base64.b64encode(pcm).decode()
        body = {
            "recognitionModel": {
                "audioFormat": {"containerAudio": {"containerAudioType": "WAV"}},
                "languageRestriction": {"languageCode": [lang]},
            },
            "content": audio_b64,
        }
        resp = self._request("POST", STT_URL, data=json.dumps(body))
        op_id = resp.json().get("id")
        if not op_id:
            raise SpeechKitError(f"No operation id in STT response: {resp.text}")

        get_url = STT_URL.replace("recognizeFileAsync", "getRecognition")
        import os, urllib3
        verify = os.environ.get("SSL_VERIFY", "true").lower() not in ("0", "false", "no")
        if not verify:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") \
             or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
        proxies = {"https": proxy, "http": proxy} if proxy else None
        # Poll until result is ready (404 = not yet done)
        for attempt in range(30):
            r = requests.get(get_url, headers=self._headers, params={"operationId": op_id},
                             timeout=self._timeout, verify=verify, proxies=proxies)
            if r.status_code == 404:
                time.sleep(2)
                continue
            if not r.ok:
                raise SpeechKitError(f"getRecognition error {r.status_code}: {r.text}")
            return self._parse_stt_stream(r.text)
        raise SpeechKitError(f"STT result not ready after 30 polls for operation {op_id}")

    @staticmethod
    def _parse_stt_stream(text: str) -> str:
        """Extract final transcript text from streaming JSON lines."""
        phrases = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                chunk = json.loads(line)
            except json.JSONDecodeError:
                continue
            result = chunk.get("result", chunk)
            final = result.get("final", {})
            alternatives = final.get("alternatives", [])
            if alternatives:
                phrases.append(alternatives[0].get("text", ""))
        return " ".join(p for p in phrases if p)
