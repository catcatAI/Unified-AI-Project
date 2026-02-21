import numpy as np
import logging
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AudioProcessing:
    """
    Audio processing module for Angela AI.
    Handles Voice Activity Detection (VAD) and feature extraction.
    """
    
    def __init__(self, sample_rate: int = 16000, energy_threshold: float = 0.01):
        self.sample_rate = sample_rate
        self.energy_threshold = energy_threshold
        logger.info(f"AudioProcessing initialized (SR: {sample_rate}, Threshold: {energy_threshold})")
        
    def detect_voice_activity(self, audio_chunk: bytes) -> bool:
        """
        Simple energy-based VAD.
        
        Args:
            audio_chunk: Raw bytes (assumed 16-bit PCM)
            
        Returns:
            True if voice is detected, False otherwise.
        """
        if not audio_chunk:
            return False
            
        try:
            # Convert bytes to numpy array (assumes 16-bit PCM)
            audio_data = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Calculate root mean square (RMS) energy
            energy = float(np.sqrt(np.mean(np.square(audio_data))))
            
            is_active = energy > self.energy_threshold
            if is_active:
                logger.debug(f"[AudioProcessing] VAD Active: Energy={energy:.4f}")
                
            return is_active
        except Exception as e:
            logger.error(f"VAD Error: {e}")
            return False

    def extract_features(self, audio_chunk: bytes) -> Dict[str, Any]:
        """
        Extract basic audio features. Placeholder for spectral features like MFCC.
        """
        if not audio_chunk:
            return {"energy": 0.0, "timestamp": time.time()}
            
        audio_data = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
        energy = float(np.sqrt(np.mean(np.square(audio_data))))
        
        return {
            "energy": energy,
            "peak": float(np.max(np.abs(audio_data))),
            "timestamp": time.time()
        }
