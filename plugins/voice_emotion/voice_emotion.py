# plugins/voice_emotion/voice_emotion.py
import os
import json
from typing import Dict
from collections import defaultdict

try:
    import requests
except ImportError:
    requests = None

from plugin_manager import AlleyBotPlugin

class VoiceEmotionPlugin(AlleyBotPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.name = "voice_emotion"
        self.version = "1.0.0"
        self.hume_key = config.get("hume_api_key", "")
        self.openai_key = config.get("openai_api_key", "")

    def get_commands(self) -> Dict[str, callable]:
        return {
            "voice_emotion": self.voice_emotion_analyze,
            "vemotion": self.voice_emotion_analyze,
        }

    def voice_emotion_analyze(self, args: list) -> str:
        if not requests:
            return "Requests library not available. Install with: pip install requests"
        if not args:
            return "Usage: !voice_emotion <path_to_audio_file>\nSupported: wav, mp3, flac, m4a"
        audio_path = args[0].strip()
        if not os.path.isfile(audio_path):
            return f"Audio file not found: {audio_path}"
        try:
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
        except Exception as e:
            return f"Failed to read audio file: {str(e)}"
        ext = os.path.splitext(audio_path)[1].lower()
        if ext == ".wav":
            content_type = "audio/wav"
        elif ext == ".mp3":
            content_type = "audio/mpeg"
        elif ext == ".flac":
            content_type = "audio/flac"
        elif ext == ".m4a":
            content_type = "audio/mp4"
        else:
            return "Unsupported format. Use: wav, mp3, flac, m4a"
        transcript = "No transcript (OpenAI key missing)"
        if self.openai_key:
            try:
                whisper_url = "https://api.openai.com/v1/audio/transcriptions"
                headers = {"Authorization": f"Bearer {self.openai_key}"}
                files = {"file": (os.path.basename(audio_path), audio_bytes, content_type)}
                data = {
                    "model": "whisper-1",
                    "response_format": "verbose_json",
                }
                resp = requests.post(whisper_url, headers=headers, files=files, data=data)
                if resp.status_code == 200:
                    transcript = resp.json()["text"]
                else:
                    transcript = f"Whisper failed ({resp.status_code})"
            except Exception as e:
                transcript = f"Whisper error: {str(e)}"
        voice_emotions_str = "No voice emotions (Hume key missing)"
        avg_emotions = {}
        if self.hume_key:
            try:
                hume_url = "https://api.hume.ai/v0/voice/predict"
                headers = {
                    "Authorization": f"Bearer {self.hume_key}",
                    "Content-Type": content_type,
                }
                resp = requests.post(hume_url, headers=headers, data=audio_bytes, stream=True)
                if resp.status_code == 200:
                    emotions = defaultdict(list)
                    for line in resp.iter_lines(decode_unicode=True):
                        if line and line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                pred = json.loads(data_str)
                                if "results" in pred and pred["results"]:
                                    res = pred["results"][0]
                                    if "emotions" in res:
                                        for emo in res["emotions"]:
                                            emotions[emo["name"]].append(emo["score"])
                            except json.JSONDecodeError:
                                continue
                    if emotions:
                        avg_emotions = {k: sum(v) / len(v) for k, v in emotions.items()}
                        sorted_emotions = sorted(avg_emotions.items(), key=lambda x: -x[1])[:5]
                        top = sorted_emotions[0]
                        voice_emotions_str = f"Top: {top[0]} ({top[1]:.3f})\nTop 5: {', '.join(f'{k}: {v:.3f}' for k, v in sorted_emotions)}"
                else:
                    voice_emotions_str = f"Hume API error ({resp.status_code}): {resp.text[:200]}"
            except Exception as e:
                voice_emotions_str = f"Hume error: {str(e)}"
        overall = "No overall analysis"
        if self.openai_key and avg_emotions:
            try:
                gpt_url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json",
                }
                gpt_prompt = f"Transcript: {transcript}\nVoice emotions (prosody): {dict(avg_emotions)}\n\nAnalyze the overall emotion in 1-2 words:"
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": gpt_prompt}],
                    "max_tokens": 20,
                }
                resp = requests.post(gpt_url, headers=headers, json=payload)
                if resp.status_code == 200:
                    overall = resp.json()["choices"][0]["message"]["content"].strip()
                else:
                    overall = f"GPT error ({resp.status_code})"
            except Exception as e:
                overall = f"GPT error: {str(e)}"
        return f"**Transcript:** {transcript}\n**Voice Emotions:** {voice_emotions_str}\n**Overall Emotion:** {overall}"

PLUGIN_INFO = {
    "name": "voice_emotion",
    "version": "1.0.0",
    "description": "Emotion detection pipeline for voice using OpenAI Whisper, Hume Voice API, and OpenAI analysis",
    "author": "AlleyBot",
}

def create_plugin(config=None):
    return VoiceEmotionPlugin(config or {})