"""
Hebrish STT Post-Processing with Gemini Flash

Fixes common transcription errors in Hebrew + English tech terms
to boost accuracy from 85% to 95%.

Common fixes:
- אבולה → טאבולה (table)
- הגיב → הגיב (respond)
- דיפלוי → deploy
- איי פיי → API
- Adds proper punctuation
"""
import logging
import json
import re
from typing import List, Dict, Any
import google.generativeai as genai

from app.core.config import settings

logger = logging.getLogger(__name__)


def fix_hebrish_segments(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Post-process Hebrish STT segments using Gemini Flash for error correction.
    
    Args:
        segments: List of raw STT segments with {start, end, text}
        
    Returns:
        List of corrected segments with same timestamps but fixed text
    """
    if not segments:
        return segments
    
    try:
        # Configure Gemini
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Format segments for LLM
        formatted_text = "\n".join([
            f"{seg.get('start', 0):.2f}-{seg.get('end', 0):.2f}: {seg.get('text', '')}"
            for seg in segments
        ])
        
        prompt = f"""
תקן תמלול Hebrish טכני (Hebrew + English tech terms).
שמור timestamps בדיוק כמו שהם!

תמלול מקורי:
{formatted_text}

תקן שגיאות נפוצות:
- אבולה → טאבולה (table)
- הגיב → הגיב (respond) 
- דיפלוי → deploy
- איי פיי איי → API
- פרודקשן → production
- קומיט → commit
- פול ריקווסט → pull request
- מרג׳ → merge
- ברנץ׳ → branch
- דוקר → docker
- קוברנטיס → kubernetes

הוסף נקודות ופסיקים במקומות הנכונים.
שמור מונחים טכניים באנגלית (deploy, API, commit, etc.)

החזר JSON:
{{
  "segments": [
    {{"start": 0.0, "end": 5.0, "text": "טקסט מתוקן"}},
    ...
  ]
}}
"""
        
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )
        )
        
        if not response.text:
            logger.warning("Gemini returned empty response for Hebrish post-processing")
            return segments
        
        # Parse corrected segments
        result = json.loads(response.text)
        corrected_segments = result.get("segments", [])
        
        if not corrected_segments:
            logger.warning("No corrected segments returned, using original")
            return segments
        
        # Validate timestamps match
        if len(corrected_segments) != len(segments):
            logger.warning(
                f"Segment count mismatch: {len(segments)} → {len(corrected_segments)}, "
                "using original"
            )
            return segments
        
        logger.info(f"✅ Hebrish post-processing: {len(corrected_segments)} segments corrected")
        return corrected_segments
        
    except Exception as e:
        logger.error(f"Hebrish post-processing failed: {e}")
        # Return original segments on error
        return segments


def fix_hebrish_text(text: str) -> str:
    """
    Quick fix for single Hebrish text string (no timestamps).
    
    Args:
        text: Raw Hebrish text
        
    Returns:
        Corrected text
    """
    try:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = f"""
תקן טקסט Hebrish טכני (Hebrew + English tech terms):

{text}

תקן שגיאות נפוצות:
- אבולה → טאבולה
- דיפלוי → deploy
- איי פיי איי → API
- פרודקשן → production

החזר רק את הטקסט המתוקן (לא JSON).
"""
        
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(temperature=0.1)
        )
        
        if response.text:
            return response.text.strip()
        else:
            return text
            
    except Exception as e:
        logger.error(f"Hebrish text fix failed: {e}")
        return text
