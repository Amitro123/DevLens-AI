"""AI documentation generation service using Google Gemini"""

import google.generativeai as genai
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
import json
import re

from app.core.config import settings
from app.core.observability import trace_pipeline, record_event, EventType

logger = logging.getLogger(__name__)


class AIGenerationError(Exception):
    """Custom exception for AI generation errors"""
    pass


class DocumentationGenerator:
    """Service for generating documentation using Google Gemini"""
    
    def __init__(self):
        """Initialize the Gemini API clients"""
        try:
            genai.configure(api_key=settings.gemini_api_key)
            self.model_pro = genai.GenerativeModel('gemini-2.5-flash-lite')
            self.model_flash = genai.GenerativeModel('gemini-2.5-flash-lite')
            logger.info("Gemini API clients initialized successfully")
        except Exception as e:
            raise AIGenerationError(f"Failed to initialize Gemini API: {str(e)}")
    
    
    def _analyze_multimodal_fast(self, video_file, context_keywords: List[str] = None):
        """
        Internal method to analyze video proxy with Gemini Flash.
        Uses multimodal understanding to find technical segments and quality frames.
        """
        keywords_str = ", ".join(context_keywords) if context_keywords else "general technical content"
        prompt = f"""
        Analyze this video demonstration. 
        1. Identify segments where TECHNICAL content related to "{keywords_str}" is discussed or shown.
        2. Within those segments, identify the EXACT timestamps for high-quality screenshots.
        3. Visual Quality Control: NEVER select a frame that shows a blank/white screen, a loading spinner, or a blurred transition.
        4. If a key moment happens during a loading state, look forward/backward by 2-3 seconds to find the fully rendered UI.
        
        Return STRICTLY JSON:
        {{
          "relevant_segments": [
            {{
              "start": float,
              "end": float,
              "reason": "string",
              "key_timestamps": [float, float]
            }}
          ],
          "technical_percentage": float
        }}
        """
        
        response = self.model_flash.generate_content(
            [video_file, prompt],
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                top_p=0.95,
                max_output_tokens=2048,
                response_mime_type="application/json"
            )
        )
        return response

    @trace_pipeline
    def analyze_video_relevance(
        self,
        video_path: str,
        context_keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Analyze video (usually a low-FPS proxy) to identify relevant segments and key timestamps.
        Replaces audio-only analysis for better accuracy.
        """
        try:
            logger.info(f"Performing multimodal analysis on: {video_path}")
            
            # Upload video file (Gemini handles video files directly)
            logger.info("Uploading video proxy to Gemini Flash...")
            video_file = genai.upload_file(video_path)
            
            # Wait for file to be processed if needed (Gemini backend async)
            # For small proxies it's usually fast, but let's be safe
            import time
            while video_file.state.name == "PROCESSING":
                time.sleep(1)
                video_file = genai.get_file(video_file.name)
            
            if video_file.state.name == "FAILED":
                raise AIGenerationError(f"Video file processing failed: {video_file.name}")

            # Call internal analysis method
            logger.info("Analyzing video with Gemini Flash (Multimodal)...")
            response = self._analyze_multimodal_fast(video_file, context_keywords)
            
            if not response.text:
                raise AIGenerationError("Gemini Flash returned empty response")
            
            # Parse JSON response
            try:
                result = json.loads(response.text)
                segments = result.get("relevant_segments", [])
                logger.info(f"Found {len(segments)} relevant segments via multimodal analysis")
                
                return segments
            
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {response.text}")
                raise AIGenerationError(f"Invalid JSON from video analysis: {str(e)}")
        
        except Exception as e:
            logger.error(f"Video analysis failed: {str(e)}")
            raise AIGenerationError(f"Failed to analyze video proxy: {str(e)}")
    
    @trace_pipeline
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
            
            # --- Post-Processing: Embed Images ---
            # Replace [Frame X] with actual image Markdown
            
            def _get_web_url(local_path: str) -> str:
                try:
                    rel_path = Path(local_path).relative_to(settings.get_upload_path().resolve())
                    return f"/uploads/{rel_path.as_posix()}"
                except ValueError:
                    # Try non-resolved path too
                    try:
                        rel_path = Path(local_path).relative_to(settings.get_upload_path())
                        return f"/uploads/{rel_path.as_posix()}"
                    except ValueError:
                        return f"/uploads/{Path(local_path).name}"

            def replace_match(match):
                try:
                    idx = int(match.group(1)) - 1 # 1-based index to 0-based
                    if 0 <= idx < len(frame_paths):
                        url = _get_web_url(frame_paths[idx])
                        return f"![Frame {idx+1}]({url})"
                except Exception:
                    pass
                return match.group(0)

            # Replace [Frame X] patterns
            documentation = re.sub(r'\[Frame (\d+)\]', replace_match, documentation)
            
            logger.info(f"Successfully generated {len(documentation)} characters of documentation")
            
            return documentation
        
        except Exception as e:
            logger.error(f"Documentation generation failed: {str(e)}")
            raise AIGenerationError(f"Failed to generate documentation: {str(e)}")
    
    def generate_segment_doc(
        self,
        segment: Dict[str, Any],
        frame_paths: List[str],
        prompt_config: 'PromptConfig',
        project_name: str = "Project",
        audio_summary: Optional[str] = None
    ) -> str:
        """
        Generate documentation for a single video segment (chunk).
        
        Args:
            segment: Segment descriptor with start, end, index
            frame_paths: List of frame paths for this segment
            prompt_config: PromptConfig object with system instructions
            project_name: Name of the project
            audio_summary: Optional audio transcript/summary for segment
        
        Returns:
            Generated Markdown for this segment only
        
        Raises:
            AIGenerationError: If generation fails
        """
        try:
            seg_start = segment.get("start", 0)
            seg_end = segment.get("end", 0)
            seg_index = segment.get("index", 0)
            
            logger.info(f"Generating doc for segment {seg_index} ({seg_start:.1f}s - {seg_end:.1f}s) with {len(frame_paths)} frames")
            
            # Build segment-specific prompt
            user_prompt = f"# Segment {seg_index + 1} Documentation\n\n"
            user_prompt += f"**Project:** {project_name}\n"
            user_prompt += f"**Time Range:** {seg_start:.1f}s - {seg_end:.1f}s\n\n"
            
            if audio_summary:
                user_prompt += f"**Audio Summary:**\n{audio_summary}\n\n"
            
            user_prompt += f"**Visual Frames:** {len(frame_paths)} screenshots from this segment.\n\n"
            user_prompt += "Please analyze the frames and document what's shown in this segment.\n"
            user_prompt += "Focus on the key actions, UI elements, and any important details visible.\n"
            
            # Upload frames
            uploaded_files = []
            for i, frame_path in enumerate(frame_paths):
                try:
                    file = genai.upload_file(frame_path)
                    uploaded_files.append(file)
                except Exception as e:
                    logger.warning(f"Failed to upload frame {frame_path}: {str(e)}")
            
            if not uploaded_files:
                # Return placeholder if no frames uploaded
                return f"## Segment {seg_index + 1} ({seg_start:.1f}s - {seg_end:.1f}s)\n\n*No frames available for this segment.*\n\n"
            
            # Construct prompt with system instruction
            prompt_parts = [prompt_config.system_instruction, user_prompt]
            prompt_parts.extend(uploaded_files)
            
            # Generate with Flash model for speed (segments are smaller)
            response = self.model_flash.generate_content(
                prompt_parts,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,
                    top_p=0.95,
                    max_output_tokens=4096,
                )
            )
            
            if not response.text:
                return f"## Segment {seg_index + 1}\n\n*No content generated.*\n\n"
            
            segment_doc = response.text.strip()
            
            # Post-process: Replace [Frame X] with actual images
            def _get_web_url(local_path: str) -> str:
                try:
                    rel_path = Path(local_path).relative_to(settings.get_upload_path().resolve())
                    return f"/uploads/{rel_path.as_posix()}"
                except ValueError:
                    try:
                        rel_path = Path(local_path).relative_to(settings.get_upload_path())
                        return f"/uploads/{rel_path.as_posix()}"
                    except ValueError:
                        return f"/uploads/{Path(local_path).name}"

            def replace_match(match):
                try:
                    idx = int(match.group(1)) - 1
                    if 0 <= idx < len(frame_paths):
                        url = _get_web_url(frame_paths[idx])
                        return f"![Frame {idx+1}]({url})"
                except Exception:
                    pass
                return match.group(0)

            segment_doc = re.sub(r'\[Frame (\d+)\]', replace_match, segment_doc)
            
            logger.info(f"Generated {len(segment_doc)} characters for segment {seg_index}")
            
            return segment_doc
        
        except Exception as e:
            logger.error(f"Segment doc generation failed: {str(e)}")
            raise AIGenerationError(f"Failed to generate segment documentation: {str(e)}")
    
    def merge_segments(
        self,
        segment_docs: List[Dict[str, Any]],
        project_name: str = "Project"
    ) -> str:
        """
        Merge segment documentations into a cohesive final document.
        
        Args:
            segment_docs: List of [{"index": 0, "doc": "...", "start": 0, "end": 30}, ...]
            project_name: Project name for the header
        
        Returns:
            Merged Markdown documentation
        """
        if not segment_docs:
            return "# Documentation\n\n*No content generated.*\n"
        
        # Sort by index
        sorted_docs = sorted(segment_docs, key=lambda x: x.get("index", 0))
        
        # Build merged document
        merged = f"# {project_name} Documentation\n\n"
        merged += f"*Generated from {len(sorted_docs)} video segments*\n\n"
        merged += "---\n\n"
        
        for seg in sorted_docs:
            seg_index = seg.get("index", 0)
            seg_start = seg.get("start", 0)
            seg_end = seg.get("end", 0)
            doc = seg.get("doc", "")
            
            # Add segment header
            merged += f"## Part {seg_index + 1} ({seg_start:.0f}s - {seg_end:.0f}s)\n\n"
            
            # Add segment content (strip duplicate headers if any)
            content = doc.strip()
            # Remove any leading # headers since we add our own
            lines = content.split("\n")
            if lines and lines[0].startswith("#"):
                lines = lines[1:]
            content = "\n".join(lines).strip()
            
            merged += content + "\n\n"
            merged += "---\n\n"
        
        logger.info(f"Merged {len(sorted_docs)} segments into {len(merged)} character document")
        
        return merged


# Singleton instance
_generator: Optional[DocumentationGenerator] = None


def get_generator() -> DocumentationGenerator:
    """Get or create the documentation generator singleton"""
    global _generator
    if _generator is None:
        _generator = DocumentationGenerator()
    return _generator
