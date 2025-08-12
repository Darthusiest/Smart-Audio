import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
from typing import Optional
from utils.logger import get_logger
from config import AUDIO_SETTINGS, TEMP_DIR
from scipy.signal import butter, lfilter


logger = get_logger("audio_cleaner")

class AudioCleaner:
    """Handles audio preprocessing and cleaning"""
    
    def __init__(self):
        self.target_sample_rate = AUDIO_SETTINGS["standard_sample_rate"]
    
    def clean_audio(self, input_path: Path, output_path: Optional[Path] = None) -> Path:
        """Clean and normalize audio for better transcription"""
        
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Audio file not found: {input_path}")
        
        # Generate output path if not provided
        if output_path is None:
            output_path = TEMP_DIR / f"{input_path.stem}_cleaned.wav"
        
        try:
            logger.info(f"Cleaning audio: {input_path}")
            
            # Load audio
            audio, sr = librosa.load(str(input_path), sr=self.target_sample_rate)
            
            # Apply cleaning steps
            cleaned_audio = self._apply_cleaning_pipeline(audio, sr)
            
            # Save cleaned audio
            sf.write(str(output_path), cleaned_audio, self.target_sample_rate)
            
            logger.info(f"Successfully cleaned audio: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to clean audio: {e}")
            raise
    
    def _apply_cleaning_pipeline(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Apply various cleaning techniques to audio"""
        
        # 1. Remove silence from beginning and end
        audio = self._trim_silence(audio)
        
        # 2. Normalize volume
        audio = self._normalize_volume(audio)
        
        # 3. Reduce noise
        audio = self._reduce_noise(audio, sr)
        
        # 4. Apply high-pass filter to remove low-frequency noise
        audio = self._apply_high_pass_filter(audio, sr)
        
        return audio
    
    def _trim_silence(self, audio: np.ndarray, threshold_db: float = -40.0) -> np.ndarray:
        """Remove silence from beginning and end of audio"""
        
        # Convert threshold to amplitude
        threshold = 10 ** (threshold_db / 20)
        
        # Find non-silent regions
        non_silent = np.where(np.abs(audio) > threshold)[0]
        
        if len(non_silent) > 0:
            start = non_silent[0]
            end = non_silent[-1] + 1
            audio = audio[start:end]
            logger.debug(f"Trimmed {start} samples from start, {len(audio) - end} from end")
        
        return audio
    
    def _normalize_volume(self, audio: np.ndarray, target_db: float = -20.0) -> np.ndarray:
        """Normalize audio volume to target level"""
        
        # Calculate RMS
        rms = np.sqrt(np.mean(audio ** 2))
        
        if rms > 0:
            # Convert target dB to amplitude
            target_amplitude = 10 ** (target_db / 20)
            
            # Calculate gain
            gain = target_amplitude / rms
            
            # Apply gain (with limiting to prevent clipping)
            gain = min(gain, 10.0)  # Limit maximum gain
            audio = audio * gain
            
            logger.debug(f"Normalized volume with gain: {gain:.2f}")
        
        return audio
    
    def _reduce_noise(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Apply spectral gating to reduce noise"""
        
        # Compute spectrogram
        stft = librosa.stft(audio)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Estimate noise floor (using first 0.5 seconds)
        noise_samples = int(0.5 * sr)
        noise_magnitude = magnitude[:, :noise_samples//512]
        noise_floor = np.mean(noise_magnitude, axis=1, keepdims=True)
        
        # Apply spectral gating
        gate_threshold = noise_floor * 2.0
        mask = magnitude > gate_threshold
        magnitude = magnitude * mask
        
        # Reconstruct audio
        cleaned_stft = magnitude * np.exp(1j * phase)
        cleaned_audio = librosa.istft(cleaned_stft)
        
        logger.debug("Applied spectral noise reduction")
        return cleaned_audio
    
    def _apply_high_pass_filter(self, audio: np.ndarray, sr: int, cutoff: float = 80.0) -> np.ndarray:
        """Apply a real high-pass filter to remove low-frequency noise."""
    # 1st-order Butterworth high-pass
        nyquist = 0.5 * sr
        normal_cutoff = cutoff / nyquist
        b, a = butter(N=1, Wn=normal_cutoff, btype='high', analog=False)
        filtered_audio = lfilter(b, a, audio)
        logger.debug(f"Applied high-pass filter with {cutoff}Hz cutoff")
        return filtered_audio
    
    def enhance_speech(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Apply speech enhancement techniques"""
        
        # Apply pre-emphasis filter to boost high frequencies
        pre_emphasis = 0.97
        emphasized = np.append(audio[0], audio[1:] - pre_emphasis * audio[:-1])
        
        # Apply spectral subtraction for noise reduction
        stft = librosa.stft(emphasized)
        magnitude = np.abs(stft)
        
        # Estimate noise spectrum from first 0.5 seconds
        noise_samples = int(0.5 * sr)
        noise_frames = noise_samples // 512
        noise_spectrum = np.mean(magnitude[:, :noise_frames], axis=1, keepdims=True)
        
        # Spectral subtraction
        alpha = 2.0  # Over-subtraction factor
        beta = 0.01  # Spectral floor
        subtracted = magnitude - alpha * noise_spectrum
        subtracted = np.maximum(subtracted, beta * magnitude)
        
        # Reconstruct
        enhanced_stft = subtracted * np.exp(1j * np.angle(stft))
        enhanced = librosa.istft(enhanced_stft)
        
        logger.debug("Applied speech enhancement")
        return enhanced 