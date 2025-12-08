import base64
import wave
from io import BytesIO
from pydub import AudioSegment


def ensure_bytes(data) -> bytes:
    """Gemini inline_data가 bytes 또는 base64 string일 수 있으므로 항상 bytes로 변환"""
    if isinstance(data, bytes):
        return data
    if isinstance(data, str):
        try:
            return base64.b64decode(data)
        except Exception:
            return data.encode("utf-8", "ignore")
    raise TypeError(f"Unsupported audio payload type: {type(data)}")


def pcm_to_mp3_file(
    pcm_bytes: bytes, mp3_path: str, sample_rate: int = 24000, channels: int = 1
):
    """
    Raw 16-bit LE PCM → MP3
    pydub이 PCM raw를 직접 읽지 못하므로 메모리 상에서 임시 WAV 헤더를 붙여 변환
    """
    with BytesIO() as wav_buf:
        with wave.open(wav_buf, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)  # 16bit = 2 bytes
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_bytes)
        wav_buf.seek(0)
        seg = AudioSegment.from_file(wav_buf, format="wav")
        seg.export(mp3_path, format="mp3")


def add_mp3_ext(path: str) -> str:
    """파일 경로에 .mp3 확장자 추가"""
    return path if path.lower().endswith(".mp3") else f"{path}.mp3"
