from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union

class SongRequest(BaseModel):
    lyrics: List[str] = []
    songTitle: Optional[str] = None

class SongResponse(BaseModel):
    mp3_url: str
    image_url: str
    video_url: str
    state: str
    executionTimes: Optional[Dict[str, float]] = None