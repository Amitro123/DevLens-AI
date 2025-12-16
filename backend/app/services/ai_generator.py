"""AI documentation generation service using Google Gemini"""

import google.generativeai as genai
from pathlib import Path
from typing import List, Optional, Dict
import logging
import json

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIGenerationError(Exception):
    """Custom exception for AI generation errors"""
    pass


class GroqTranscriber:
    """
    Service for transcribing audio using Groq's Whisper Large V3 model.
    Returns segments with timestamps for smart sampling.
    """
    
    def __init__(self):
        """Initialize the Groq client"""
        import os
        from groq import Groq
        
        api_key = settings.groq_api_key
        if not api_key:
            api_key = os.environ.get("GROQ_API_KEY", "")
        
        if not api_key:
            logger.warning("GROQ_API_KEY not set. GroqTranscriber will not function.")
            self.client = None
        else:
            self.client = Groq(api_key=api_key)
            logger.info("GroqTranscriber initialized successfully")
    
    def transcribe(self, audio_file_path: str) -> Dict:
        """
        Transcribe audio file using Groq Whisper.
        
        Args:
            audio_file_path: Path to the audio file (WAV, MP3, etc.)
        
        Returns:
            Dict with 'text' (full transcript), 'segments' (list of timestamped segments)
        
        Raises:
            AIGenerationError if transcription fails
        """
        if not self.client:
            raise AIGenerationError("GroqTranscriber not initialized. GROQ_API_KEY is missing.")
        
        try:
            logger.info(f"Transcribing audio with Groq Whisper: {audio_file_path}")
            
            with open(audio_file_path, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    model="whisper-large-v3",
                    file=audio_file,
                    response_format="verbose_json",  # Returns timestamps
                    language="en"  # Auto-detect if not specified
                )
            
            # Parse response
            result = {
                "text": transcription.text,
                "segments": []
            }
            
            # Extract segments with timestamps if available
            if hasattr(transcription, 'segments') and transcription.segments:
                for seg in transcription.segments:
                    result["segments"].append({
                        "start": seg.get("start", 0),
                        "end": seg.get("end", 0),
                        "text": seg.get("text", "")
                    })
                logger.info(f"Transcription complete: {len(result['segments'])} segments")
            else:
                # Fallback: create single segment for entire audio
                result["segments"] = [{
                    "start": 0,
                    "end": 0,  # Unknown duration
                    "text": transcription.text
                }]
                logger.info("Transcription complete (no segment timestamps available)")
            
            return result
        
        except Exception as e:
            logger.error(f"Groq transcription failed: {str(e)}")
            raise AIGenerationError(f"Failed to transcribe audio: {str(e)}")


class DocumentationGenerator:
    """Service for generating documentation using Google Gemini"""
    
    def __init__(self):
        """Initialize the Gemini API clients"""
        try:
            genai.configure(api_key=settings.gemini_api_key)
            self.model_pro = genai.GenerativeModel('gemini-1.5-pro')
            self.model_flash = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Gemini API clients initialized successfully")
        except Exception as e:
            raise AIGenerationError(f"Failed to initialize Gemini API: {str(e)}")
    
    
    def _transcribe_audio_fast(self, audio_file):
        """
        Internal method to analyze audio with Gemini Flash.
        Isolated for easier mocking in tests.
        """
        prompt = "Analyze this audio and return JSON with relevant segments and their start/end timestamps. Also output a technical_percentage score."
        
        response = self.model_flash.generate_content(
            [audio_file, prompt],
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                top_p=0.95,
                max_output_tokens=2048,
                response_mime_type="application/json"
            )
        )
        return response

    def analyze_audio_relevance(
        self,
        audio_path: str,
        context_keywords: List[str]
    ) -> List[Dict[str, float]]:
        """
        Analyze audio to identify timestamps where technical content is discussed.
        """
        try:
            logger.info(f"Analyzing audio relevance: {audio_path}")
            
            # Load audio filter prompt (optional, we use internal prompt for strict JSON)
            # from app.services.prompt_loader import get_prompt_loader
            
            # Upload audio file
            logger.info("Uploading audio to Gemini Flash...")
            audio_file = genai.upload_file(audio_path)
            
            # Call internal transcription method
            logger.info("Analyzing audio with Gemini Flash...")
            response = self._transcribe_audio_fast(audio_file)
            
            if not response.text:
                raise AIGenerationError("Gemini Flash returned empty response")
            
            # Parse JSON response
            try:
                # Direct JSON parsing since we requested mime_type="application/json"
                result = json.loads(response.text)
                segments = result.get("relevant_segments", [])
                
                # Filter segments based on keywords if provided (simple keyword matching simulation)
                # In a real scenario, the LLM prompt would do this, but we can double check here
                if context_keywords:
                    # Rerank or filter logic could go here
                    pass

                logger.info(f"Found {len(segments)} relevant segments")
                
                return segments
            
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {response.text}")
                raise AIGenerationError(f"Invalid JSON from audio analysis: {str(e)}")
        
        except Exception as e:
            logger.error(f"Audio analysis failed: {str(e)}")
            raise AIGenerationError(f"Failed to analyze audio: {str(e)}")
    
    def generate_documentation(
        self,
        frame_paths: List[str],
        prompt_config: 'PromptConfig',
        context: str = "",
        project_name: str = "Project",
        audio_transcript: Optional[str] = None
    ) -> str:
        """
        Generate technical documentation from video frames using dynamic prompts.
        
        Args:
            frame_paths: List of paths to extracted frame images
            prompt_config: PromptConfig object with system instructions
            context: Optional organizational context from RAG
            project_name: Name of the project being documented
            audio_transcript: Optional audio transcript to include
        
        Returns:
            Generated Markdown documentation
        
        Raises:
            AIGenerationError: If generation fails
        """
        try:
            logger.info(f"Generating documentation for {project_name} with {len(frame_paths)} frames")
            logger.info(f"Using prompt mode: {prompt_config.name}")
            
            # Prepare the prompt
            user_prompt = f"# Documentation Request\n\n"
            user_prompt += f"**Project:** {project_name}\n\n"
            
            
            # TODO: IMPLEMENT RBAC - Filter context by user.department
            # Ensure developers cannot access HR vector embeddings, and vice versa.
            # Example: if user.department != prompt_config.department: filter_or_deny_context()
            if context:
                user_prompt += f"**Organizational Context:**\n{context}\n\n"
            
            if audio_transcript:
                user_prompt += f"**Audio Transcript:**\n{audio_transcript}\n\n"
            
            user_prompt += f"**Visual Frames:** {len(frame_paths)} screenshots from a video demonstration.\n\n"
            user_prompt += "Please analyze the frames"
            if audio_transcript:
                user_prompt += " and transcript"
            user_prompt += " and create documentation according to your instructions.\n"
            
            # Upload frames
            uploaded_files = []
            for i, frame_path in enumerate(frame_paths):
                try:
                    file = genai.upload_file(frame_path)
                    uploaded_files.append(file)
                    logger.debug(f"Uploaded frame {i + 1}/{len(frame_paths)}")
                except Exception as e:
                    logger.warning(f"Failed to upload frame {frame_path}: {str(e)}")
            
            if not uploaded_files:
                raise AIGenerationError("Failed to upload any frames to Gemini")
            
            # Construct the full prompt with dynamic system instruction
            prompt_parts = [prompt_config.system_instruction, user_prompt]
            prompt_parts.extend(uploaded_files)
            
            # Generate content with Pro model
            logger.info("Sending generation request to Gemini Pro...")
            response = self.model_pro.generate_content(
                prompt_parts,
                generation_config=genai.GenerationConfig(
                    temperature=0.4,  # Lower temperature for more focused output
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=8192,
                )
            )
            
            # Extract text from response
            if not response.text:
                raise AIGenerationError("Gemini returned empty response")
            
            documentation = response.text.strip()
            
            logger.info(f"Successfully generated {len(documentation)} characters of documentation")
            
            return documentation
        
        except Exception as e:
            logger.error(f"Documentation generation failed: {str(e)}")
            raise AIGenerationError(f"Failed to generate documentation: {str(e)}")


# Singleton instance
_generator: Optional[DocumentationGenerator] = None


def get_generator() -> DocumentationGenerator:
    """Get or create the documentation generator singleton"""
    global _generator
    if _generator is None:
        _generator = DocumentationGenerator()
    return _generator
