"""
Helper to save STT segments to segments.json for frontend display.

This ensures transcript timeline appears in SessionDetails.tsx.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def save_segments_to_file(session_id: str, segments: List[Dict[str, Any]], upload_path: Path) -> None:
    """
    Save STT segments to segments.json for a session.
    
    Args:
        session_id: Session identifier
        segments: List of segment dicts with {start, end, text}
        upload_path: Base upload directory path
    """
    try:
        session_dir = upload_path / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        segments_file = session_dir / "segments.json"
        
        # Normalize segment format for frontend
        normalized_segments = []
        for seg in segments:
            normalized_segments.append({
                "start_sec": seg.get("start", seg.get("start_sec", 0)),
                "end_sec": seg.get("end", seg.get("end_sec", 0)),
                "text": seg.get("text", "")
            })
        
        with open(segments_file, 'w', encoding='utf-8') as f:
            json.dump(normalized_segments, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(normalized_segments)} segments to {segments_file}")
        
    except Exception as e:
        logger.error(f"Failed to save segments for {session_id}: {e}")
