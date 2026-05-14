"""Unit tests for AudioProcessor — hardware and model are mocked."""
import numpy as np
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def processor():
    """AudioProcessor with no Whisper model loaded."""
    with patch('audio_processor.WhisperModel'), \
         patch('audio_processor.sd'):
        from audio_processor import AudioProcessor
        ap = AudioProcessor(model_size="tiny")
        ap.model = None
        return ap


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def test_config_loaded_on_init(processor):
    # config.json exists in the project root, so it should be loaded
    assert isinstance(processor.config, dict)


def test_config_contains_lang(processor):
    assert "lang" in processor.config or "lang_tts" in processor.config


# ---------------------------------------------------------------------------
# _get_input_device
# ---------------------------------------------------------------------------

def test_get_input_device_prefers_system_default(processor):
    """Must return the system default input index, not device 0 (raw hw:)."""
    import sounddevice as real_sd
    mock_sd = MagicMock()
    mock_sd.default.device = [18, 1]          # default input = 18
    mock_sd.query_devices.return_value = []    # fallback list unused
    processor._sd = mock_sd

    with patch('audio_processor.sd', mock_sd):
        result = processor._get_input_device()
    assert result == 18


def test_get_input_device_falls_back_to_pulse(processor):
    """When no system default, prefer 'pulse' over raw hw: device."""
    mock_sd = MagicMock()
    mock_sd.default.device = [-1, -1]
    mock_sd.query_devices.return_value = [
        {"name": "HDA Intel PCH: ALC3246 Analog (hw:0,0)", "max_input_channels": 2},
        {"name": "pulse",                                   "max_input_channels": 32},
        {"name": "pipewire",                                "max_input_channels": 128},
    ]
    with patch('audio_processor.sd', mock_sd):
        result = processor._get_input_device()
    assert result == 1   # pulse is at index 1


def test_get_input_device_falls_back_to_first_available(processor):
    """Last resort: first device with input channels."""
    mock_sd = MagicMock()
    mock_sd.default.device = [-1, -1]
    mock_sd.query_devices.return_value = [
        {"name": "hw:0,0", "max_input_channels": 2},
    ]
    with patch('audio_processor.sd', mock_sd):
        result = processor._get_input_device()
    assert result == 0


# ---------------------------------------------------------------------------
# stop_recording
# ---------------------------------------------------------------------------

def test_stop_recording_with_no_audio_returns_none(processor):
    processor.recording = False
    processor.audio_data = []
    processor._stream = None
    result = processor.stop_recording()
    assert result is None


def test_stop_recording_concatenates_audio(processor):
    processor.recording = False
    chunk = np.array([[0.1], [0.2], [0.3]], dtype=np.float32)
    processor.audio_data = [chunk, chunk]
    processor._stream = None
    result = processor.stop_recording()
    assert result is not None
    assert len(result) == 6


# ---------------------------------------------------------------------------
# transcribe
# ---------------------------------------------------------------------------

def test_transcribe_none_returns_empty_string(processor):
    result = processor.transcribe(None)
    assert result == ""


def test_transcribe_silent_audio_returns_empty_string(processor):
    silent = np.zeros(16000, dtype=np.float32)
    result = processor.transcribe(silent)
    assert result == ""


def test_transcribe_calls_model_when_audio_is_loud(processor):
    mock_model = MagicMock()
    mock_segment = MagicMock()
    mock_segment.text = "Hello world"
    mock_model.transcribe.return_value = ([mock_segment], MagicMock())
    processor.model = mock_model

    loud_audio = np.ones(16000, dtype=np.float32) * 0.5
    result = processor.transcribe(loud_audio)
    assert result == "Hello world"
    mock_model.transcribe.assert_called_once()


def test_transcribe_joins_multiple_segments(processor):
    mock_model = MagicMock()
    seg1, seg2 = MagicMock(), MagicMock()
    seg1.text = "Hello"
    seg2.text = "world"
    mock_model.transcribe.return_value = ([seg1, seg2], MagicMock())
    processor.model = mock_model

    loud_audio = np.ones(8000, dtype=np.float32) * 0.5
    result = processor.transcribe(loud_audio)
    assert result == "Hello world"
