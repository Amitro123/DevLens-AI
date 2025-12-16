"""Tests for Groq STT Integration (GroqTranscriber)"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from app.services.ai_generator import GroqTranscriber, AIGenerationError


class TestGroqTranscriber:
    """Test suite for GroqTranscriber class"""
    
    @pytest.fixture
    def mock_groq_client(self):
        """Create a mock Groq client"""
        with patch('app.services.ai_generator.settings') as mock_settings:
            mock_settings.groq_api_key = "test_api_key"
            with patch('groq.Groq') as mock_groq:
                mock_client = MagicMock()
                mock_groq.return_value = mock_client
                yield mock_client

    def test_transcriber_init_with_api_key(self, mock_groq_client):
        """Test GroqTranscriber initializes with valid API key"""
        with patch('app.services.ai_generator.settings') as mock_settings:
            mock_settings.groq_api_key = "test_api_key"
            with patch('groq.Groq') as mock_groq:
                mock_groq.return_value = MagicMock()
                transcriber = GroqTranscriber()
                assert transcriber.client is not None

    def test_transcriber_init_without_api_key(self):
        """Test GroqTranscriber warns when API key is missing"""
        with patch('app.services.ai_generator.settings') as mock_settings:
            mock_settings.groq_api_key = ""
            with patch.dict('os.environ', {'GROQ_API_KEY': ''}, clear=True):
                transcriber = GroqTranscriber()
                assert transcriber.client is None

    def test_transcribe_success_with_segments(self, mock_groq_client):
        """Test successful transcription with segment timestamps"""
        # Mock the transcription response
        mock_response = MagicMock()
        mock_response.text = "Hello, this is a test transcription."
        mock_response.segments = [
            {"start": 0.0, "end": 2.5, "text": "Hello, this is"},
            {"start": 2.5, "end": 5.0, "text": "a test transcription."}
        ]
        
        mock_groq_client.audio.transcriptions.create.return_value = mock_response
        
        with patch('app.services.ai_generator.settings') as mock_settings:
            mock_settings.groq_api_key = "test_api_key"
            with patch('groq.Groq') as mock_groq:
                mock_groq.return_value = mock_groq_client
                transcriber = GroqTranscriber()
                
                with patch("builtins.open", mock_open(read_data=b"audio data")):
                    result = transcriber.transcribe("test_audio.wav")
        
        assert result["text"] == "Hello, this is a test transcription."
        assert len(result["segments"]) == 2
        assert result["segments"][0]["start"] == 0.0
        assert result["segments"][1]["end"] == 5.0

    def test_transcribe_success_without_segments(self, mock_groq_client):
        """Test transcription fallback when no segments available"""
        mock_response = MagicMock()
        mock_response.text = "No segments available."
        mock_response.segments = None
        
        mock_groq_client.audio.transcriptions.create.return_value = mock_response
        
        with patch('app.services.ai_generator.settings') as mock_settings:
            mock_settings.groq_api_key = "test_api_key"
            with patch('groq.Groq') as mock_groq:
                mock_groq.return_value = mock_groq_client
                transcriber = GroqTranscriber()
                
                with patch("builtins.open", mock_open(read_data=b"audio data")):
                    result = transcriber.transcribe("test_audio.wav")
        
        assert result["text"] == "No segments available."
        assert len(result["segments"]) == 1
        assert result["segments"][0]["text"] == "No segments available."

    def test_transcribe_without_client_raises_error(self):
        """Test transcription fails gracefully without client"""
        with patch('app.services.ai_generator.settings') as mock_settings:
            mock_settings.groq_api_key = ""
            with patch.dict('os.environ', {'GROQ_API_KEY': ''}, clear=True):
                transcriber = GroqTranscriber()
                
                with pytest.raises(AIGenerationError) as exc_info:
                    transcriber.transcribe("test_audio.wav")
                
                assert "GROQ_API_KEY is missing" in str(exc_info.value)

    def test_transcribe_api_error_handling(self, mock_groq_client):
        """Test transcription handles API errors gracefully"""
        mock_groq_client.audio.transcriptions.create.side_effect = Exception("API Error")
        
        with patch('app.services.ai_generator.settings') as mock_settings:
            mock_settings.groq_api_key = "test_api_key"
            with patch('groq.Groq') as mock_groq:
                mock_groq.return_value = mock_groq_client
                transcriber = GroqTranscriber()
                
                with patch("builtins.open", mock_open(read_data=b"audio data")):
                    with pytest.raises(AIGenerationError) as exc_info:
                        transcriber.transcribe("test_audio.wav")
                
                assert "Failed to transcribe audio" in str(exc_info.value)
