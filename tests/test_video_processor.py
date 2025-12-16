"""Tests for Video Processor Service"""

import pytest
from pathlib import Path


class TestVideoProcessor:
    """Test suite for video processing functions"""
    
    def test_video_processor_imports(self):
        """Test video processor can be imported"""
        from app.services.video_processor import (
            extract_frames,
            extract_audio,
            get_video_duration,
            VideoProcessingError
        )
        assert extract_frames is not None
        assert extract_audio is not None
        assert get_video_duration is not None

    def test_video_processing_error(self):
        """Test VideoProcessingError exception"""
        from app.services.video_processor import VideoProcessingError
        
        with pytest.raises(VideoProcessingError):
            raise VideoProcessingError("Test error")

    def test_video_processing_error_message(self):
        """Test VideoProcessingError has correct message"""
        from app.services.video_processor import VideoProcessingError
        
        error = VideoProcessingError("Custom error message")
        assert "Custom error message" in str(error)

    def test_extract_frames_nonexistent_file(self):
        """Test extract_frames with non-existent file raises error"""
        from app.services.video_processor import extract_frames, VideoProcessingError
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(VideoProcessingError):
                extract_frames("nonexistent_video_12345.mp4", tmpdir)

    def test_extract_audio_nonexistent_file(self):
        """Test extract_audio with non-existent file raises error"""
        from app.services.video_processor import extract_audio, VideoProcessingError
        
        with pytest.raises((VideoProcessingError, Exception)):
            extract_audio("nonexistent_audio_12345.mp4")

    def test_get_video_duration_nonexistent_file(self):
        """Test get_video_duration with non-existent file raises error"""
        from app.services.video_processor import get_video_duration, VideoProcessingError
        
        with pytest.raises(VideoProcessingError):
            get_video_duration("nonexistent_duration_12345.mp4")


class TestExtractFramesAtTimestamps:
    """Test suite for timestamp-based frame extraction"""
    
    def test_extract_frames_at_timestamps_import(self):
        """Test extract_frames_at_timestamps can be imported"""
        from app.services.video_processor import extract_frames_at_timestamps
        assert extract_frames_at_timestamps is not None

    def test_extract_frames_at_timestamps_nonexistent(self):
        """Test extract_frames_at_timestamps with non-existent file"""
        from app.services.video_processor import extract_frames_at_timestamps, VideoProcessingError
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(VideoProcessingError):
                extract_frames_at_timestamps(
                    "nonexistent_video_timestamps.mp4",
                    tmpdir,
                    [1.0, 2.0, 3.0]
                )
