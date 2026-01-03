"""
Tests for Hebrish STT post-processing functionality.

Validates that the LLM-based post-processing correctly fixes
common Hebrish transcription errors.
"""
import pytest
from unittest.mock import Mock, patch
from app.services.stt_postprocess import fix_hebrish_segments, fix_hebrish_text


class TestHebrishPostProcessing:
    """Test suite for Hebrish STT post-processing"""
    
    def test_fix_hebrish_segments_empty_list(self):
        """Test that empty segment list returns empty"""
        result = fix_hebrish_segments([])
        assert result == []
    
    def test_fix_hebrish_segments_preserves_timestamps(self):
        """Test that timestamps are preserved exactly"""
        mock_segments = [
            {"start": 0.0, "end": 5.0, "text": "אבולה של דאטה"},
            {"start": 5.0, "end": 10.0, "text": "צריך לעשות דיפלוי"}
        ]
        
        # Mock Gemini response
        mock_response = Mock()
        mock_response.text = '''
        {
          "segments": [
            {"start": 0.0, "end": 5.0, "text": "טאבולה של דאטה"},
            {"start": 5.0, "end": 10.0, "text": "צריך לעשות deploy"}
          ]
        }
        '''
        
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_instance = Mock()
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance
            
            result = fix_hebrish_segments(mock_segments)
            
            # Verify timestamps preserved
            assert len(result) == 2
            assert result[0]["start"] == 0.0
            assert result[0]["end"] == 5.0
            assert result[1]["start"] == 5.0
            assert result[1]["end"] == 10.0
    
    def test_fix_hebrish_segments_corrects_common_errors(self):
        """Test that common Hebrish errors are corrected"""
        mock_segments = [
            {"start": 0.0, "end": 5.0, "text": "אבולה"}
        ]
        
        mock_response = Mock()
        mock_response.text = '''
        {
          "segments": [
            {"start": 0.0, "end": 5.0, "text": "טאבולה"}
          ]
        }
        '''
        
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_instance = Mock()
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance
            
            result = fix_hebrish_segments(mock_segments)
            
            # Verify correction
            assert result[0]["text"] == "טאבולה"
    
    def test_fix_hebrish_segments_handles_api_error(self):
        """Test that API errors return original segments"""
        mock_segments = [
            {"start": 0.0, "end": 5.0, "text": "test"}
        ]
        
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_model.side_effect = Exception("API Error")
            
            result = fix_hebrish_segments(mock_segments)
            
            # Should return original on error
            assert result == mock_segments
    
    def test_fix_hebrish_segments_handles_segment_count_mismatch(self):
        """Test that segment count mismatch returns original"""
        mock_segments = [
            {"start": 0.0, "end": 5.0, "text": "test1"},
            {"start": 5.0, "end": 10.0, "text": "test2"}
        ]
        
        mock_response = Mock()
        mock_response.text = '''
        {
          "segments": [
            {"start": 0.0, "end": 5.0, "text": "corrected"}
          ]
        }
        '''
        
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_instance = Mock()
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance
            
            result = fix_hebrish_segments(mock_segments)
            
            # Should return original due to count mismatch
            assert result == mock_segments
    
    def test_fix_hebrish_text_simple(self):
        """Test simple text correction"""
        mock_response = Mock()
        mock_response.text = "טאבולה של deploy"
        
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_instance = Mock()
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance
            
            result = fix_hebrish_text("אבולה של דיפלוי")
            
            assert result == "טאבולה של deploy"
    
    def test_fix_hebrish_text_handles_error(self):
        """Test that text correction handles errors gracefully"""
        original_text = "test text"
        
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_model.side_effect = Exception("API Error")
            
            result = fix_hebrish_text(original_text)
            
            # Should return original on error
            assert result == original_text
    
    def test_fix_hebrish_segments_tech_terms(self):
        """Test that technical terms are preserved in English"""
        mock_segments = [
            {"start": 0.0, "end": 5.0, "text": "צריך לעשות איי פיי איי קול"}
        ]
        
        mock_response = Mock()
        mock_response.text = '''
        {
          "segments": [
            {"start": 0.0, "end": 5.0, "text": "צריך לעשות API call"}
          ]
        }
        '''
        
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_instance = Mock()
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance
            
            result = fix_hebrish_segments(mock_segments)
            
            # Verify tech terms in English
            assert "API" in result[0]["text"]
    
    def test_fix_hebrish_segments_adds_punctuation(self):
        """Test that punctuation is added appropriately"""
        mock_segments = [
            {"start": 0.0, "end": 5.0, "text": "זה עובד טוב"}
        ]
        
        mock_response = Mock()
        mock_response.text = '''
        {
          "segments": [
            {"start": 0.0, "end": 5.0, "text": "זה עובד טוב."}
          ]
        }
        '''
        
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_instance = Mock()
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance
            
            result = fix_hebrish_segments(mock_segments)
            
            # Verify punctuation added
            assert result[0]["text"].endswith(".")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
