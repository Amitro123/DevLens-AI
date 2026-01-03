"""
Helper to extract visible JSON/code from frame images using Gemini Vision.

This enables the "Copy JSON" button to copy actual code visible in screenshots,
not just frame metadata.
"""
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any
import google.generativeai as genai

from app.core.config import settings

logger = logging.getLogger(__name__)


def extract_json_from_frame(frame_path: str) -> Optional[Dict[str, Any]]:
    """
    Extract visible JSON/code from a frame image using Gemini Vision.
    
    Args:
        frame_path: Absolute path to frame image
        
    Returns:
        Dict with extracted data or None if no code visible
    """
    try:
        # Configure Gemini
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Upload frame
        frame_file = genai.upload_file(frame_path)
        
        # Prompt for code extraction
        prompt = """
        Analyze this screenshot and extract any visible code, JSON, or structured data.
        
        If you see:
        - JSON objects/arrays
        - Code snippets (Python, JavaScript, etc.)
        - API responses
        - Configuration files
        - Error messages with stack traces
        
        Return STRICTLY valid JSON in this format:
        {
          "has_code": true/false,
          "code_type": "json|python|javascript|yaml|other",
          "extracted_code": "the actual code as a string",
          "parsed_json": {...} // if it's valid JSON, parse it here
        }
        
        If NO code is visible (just UI, blank screen, etc.), return:
        {
          "has_code": false
        }
        """
        
        response = model.generate_content(
            [frame_file, prompt],
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )
        )
        
        if not response.text:
            return None
            
        result = json.loads(response.text)
        
        if result.get("has_code"):
            logger.info(f"Extracted {result.get('code_type', 'unknown')} code from frame")
            return result
        else:
            logger.debug("No code visible in frame")
            return None
            
    except Exception as e:
        logger.warning(f"Failed to extract JSON from frame: {e}")
        return None


def extract_and_save_frame_json(session_id: str, frame_index: int, frame_path: str, upload_path: Path) -> None:
    """
    Extract JSON from a frame and save to frame_data.json.
    
    Args:
        session_id: Session identifier
        frame_index: Index of the frame
        frame_path: Path to frame image
        upload_path: Base upload directory
    """
    try:
        session_dir = upload_path / session_id
        frame_data_file = session_dir / "frame_data.json"
        
        # Load existing frame data or create new
        if frame_data_file.exists():
            with open(frame_data_file, 'r', encoding='utf-8') as f:
                frame_data = json.load(f)
        else:
            frame_data = {}
        
        # Extract JSON from frame
        extracted = extract_json_from_frame(frame_path)
        
        if extracted and extracted.get("has_code"):
            # Store extracted data
            frame_data[str(frame_index)] = {
                "code_type": extracted.get("code_type"),
                "extracted_code": extracted.get("extracted_code"),
                "parsed_json": extracted.get("parsed_json")
            }
            
            # Save updated frame data
            with open(frame_data_file, 'w', encoding='utf-8') as f:
                json.dump(frame_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Saved extracted code for frame {frame_index} in session {session_id}")
        
    except Exception as e:
        logger.error(f"Failed to save frame JSON: {e}")
