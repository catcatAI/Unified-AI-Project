import unittest
import asyncio
import uuid
from unittest.mock import MagicMock, AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from apps.backend.src.agents.audio_processing_agent import AudioProcessingAgent
from apps.backend.src.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope

class TestAudioProcessingAgent(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.agent_id = f"did:hsp:test_audio_agent_{uuid.uuid4().hex[:6]}"
        self.agent = AudioProcessingAgent(agent_id=self.agent_id)
        
        # Mock the HSP connector
        self.agent.hsp_connector = MagicMock()
        self.agent.hsp_connector.send_task_result = AsyncMock()

    def test_initialization(self):
        """Test AudioProcessingAgent initialization."""
        self.assertEqual(self.agent.agent_id, self.agent_id)
        
        # Check that capabilities are properly set
        self.assertEqual(len(self.agent.capabilities), 3)
        
        # Check capability names
        capability_names = [cap['name'] for cap in self.agent.capabilities]
        self.assertIn('speech_recognition', capability_names)
        self.assertIn('audio_classification', capability_names)
        self.assertIn('audio_enhancement', capability_names)

    def test_perform_speech_recognition(self):
        """Test speech recognition functionality."""
        params = {
            'audio_file': 'test_audio.wav',
            'language': 'en'
        }
        
        result = self.agent._perform_speech_recognition(params)
        
        # Check that result contains expected keys
        self.assertIn('transcription', result)
        self.assertIn('language', result)
        self.assertIn('confidence', result)
        self.assertIn('words', result)
        self.assertIn('duration', result)
        
        # Check specific values
        self.assertEqual(result['language'], 'en')
        self.assertEqual(result['duration'], '00:00:05')

    def test_perform_speech_recognition_missing_file(self):
        """Test speech recognition with missing audio file."""
        params = {}
        
        with self.assertRaises(ValueError) as context:
            self.agent._perform_speech_recognition(params)
        
        self.assertIn("No audio file provided", str(context.exception))

    def test_classify_audio(self):
        """Test audio classification functionality."""
        params = {
            'audio_file': 'test_audio.wav'
        }
        
        result = self.agent._classify_audio(params)
        
        # Check that result contains expected keys
        self.assertIn('primary_category', result)
        self.assertIn('categories', result)
        self.assertIn('confidence_scores', result)
        self.assertIn('top_category', result)
        self.assertIn('top_confidence', result)

    def test_classify_audio_missing_file(self):
        """Test audio classification with missing audio file."""
        params = {}
        
        with self.assertRaises(ValueError) as context:
            self.agent._classify_audio(params)
        
        self.assertIn("No audio file provided", str(context.exception))

    def test_enhance_audio(self):
        """Test audio enhancement functionality."""
        params = {
            'audio_file': 'test_audio.wav',
            'enhancement_type': 'noise_reduction'
        }
        
        result = self.agent._enhance_audio(params)
        
        # Check that result contains expected keys
        self.assertIn('original_file', result)
        self.assertIn('enhanced_file', result)
        self.assertIn('enhancement_type', result)
        self.assertIn('improvement_score', result)
        self.assertIn('processing_time', result)
        
        # Check specific values
        self.assertEqual(result['original_file'], 'test_audio.wav')
        self.assertEqual(result['enhancement_type'], 'noise_reduction')

    def test_enhance_audio_missing_file(self):
        """Test audio enhancement with missing audio file."""
        params = {}
        
        with self.assertRaises(ValueError) as context:
            self.agent._enhance_audio(params)
        
        self.assertIn("No audio file provided", str(context.exception))

    async def async_test_handle_speech_recognition_task(self):
        """Test handling a speech recognition task request."""
        # Create a mock task payload
        task_payload = HSPTaskRequestPayload(
            request_id="test_request_001",
            capability_id_filter=f"{self.agent_id}_speech_recognition_v1.0",
            parameters={
                "audio_file": "test_audio.wav",
                "language": "en"
            },
            callback_address="hsp/results/test_callback"
        )
        
        # Create a mock envelope
        envelope = HSPMessageEnvelope(
            message_id="test_msg_001",
            sender_ai_id="test_sender",
            recipient_ai_id=self.agent_id,
            timestamp_sent="2023-01-01T00:00:00Z",
            message_type="task_request",
            protocol_version="1.0"
        )
        
        # Handle the task request
        await self.agent.handle_task_request(task_payload, "test_sender", envelope)
        
        # Verify that send_task_result was called
        self.agent.hsp_connector.send_task_result.assert_called_once()
        
        # Get the call arguments
        call_args = self.agent.hsp_connector.send_task_result.call_args
        result_payload = call_args[0][0]
        
        # Verify the result payload
        self.assertEqual(result_payload['status'], 'success')
        self.assertIn('transcription', result_payload['payload'])
        self.assertEqual(result_payload['request_id'], 'test_request_001')

    def test_handle_speech_recognition_task(self):
        """Test handling a speech recognition task request."""
        asyncio.run(self.async_test_handle_speech_recognition_task())

    async def async_test_handle_unsupported_capability(self):
        """Test handling an unsupported capability."""
        # Create a mock task payload with unsupported capability
        task_payload = HSPTaskRequestPayload(
            request_id="test_request_002",
            capability_id_filter=f"{self.agent_id}_unsupported_v1.0",
            parameters={},
            callback_address="hsp/results/test_callback"
        )
        
        # Create a mock envelope
        envelope = HSPMessageEnvelope(
            message_id="test_msg_002",
            sender_ai_id="test_sender",
            recipient_ai_id=self.agent_id,
            timestamp_sent="2023-01-01T00:00:00Z",
            message_type="task_request",
            protocol_version="1.0"
        )
        
        # Handle the task request
        await self.agent.handle_task_request(task_payload, "test_sender", envelope)
        
        # Verify that send_task_result was called
        self.agent.hsp_connector.send_task_result.assert_called_once()
        
        # Get the call arguments
        call_args = self.agent.hsp_connector.send_task_result.call_args
        result_payload = call_args[0][0]
        
        # Verify the result payload
        self.assertEqual(result_payload['status'], 'failure')
        self.assertEqual(result_payload['error_details']['error_code'], 'CAPABILITY_NOT_SUPPORTED')
        self.assertEqual(result_payload['request_id'], 'test_request_002')

    def test_handle_unsupported_capability(self):
        """Test handling an unsupported capability."""
        asyncio.run(self.async_test_handle_unsupported_capability())

if __name__ == '__main__':
    unittest.main()