import pytest
import os
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock

from aider.handover_manager import HandoverManager, HandoverState

@pytest.fixture
def mock_coder():
    coder = Mock()
    coder.__class__.__name__ = "BaseCoder"
    coder.main_model.name = "test-model"
    coder.main_model.max_tokens = 1024
    coder.main_model.info = {}
    coder.editor_model = None
    coder.weak_model = None
    coder.model_settings = {}
    coder.abs_fnames = set()
    coder.abs_read_only_fnames = set()
    coder.repo_map = {}
    coder.chat_completion_call_hashes = []
    coder.root = "/test"
    coder.total_cost = 0.0
    coder.num_exhausted_context_windows = 0
    coder.edit_format = "diff"
    return coder

@pytest.fixture
def handover_manager(tmp_path):
    manager = HandoverManager()
    manager.handover_state_file = tmp_path / ".aider.handover.state.json"
    manager.handover_history_file = tmp_path / ".aider.handover.history.jsonl"
    return manager

def test_capture_and_save_handover_state(handover_manager, mock_coder, tmp_path):
    # Create a dummy file for the test
    test_file = tmp_path / "file1.py"
    test_file.write_text("print('hello')")
    mock_coder.abs_fnames = {str(test_file)}

    state = handover_manager.capture_current_state(coder=mock_coder)
    handover_manager.save_handover_state(state)

    assert os.path.exists(handover_manager.handover_state_file)

    with open(handover_manager.handover_state_file, 'r') as f:
        saved_state = json.load(f)

    assert saved_state["session_id"] == state.session_id
    assert saved_state["main_model"]["name"] == "test-model"
    assert str(test_file) in saved_state["active_files"]

def test_load_and_validate_handover_state(handover_manager, mock_coder, tmp_path):
    test_file = tmp_path / "file1.py"
    test_file.write_text("print('hello')")
    mock_coder.abs_fnames = {str(test_file)}

    state = handover_manager.capture_current_state(coder=mock_coder)
    handover_manager.save_handover_state(state)

    loaded_state = handover_manager.load_handover_state()

    assert loaded_state is not None
    assert loaded_state.session_id == state.session_id
    assert loaded_state.main_model["name"] == "test-model"

def test_file_integrity_check_fails_on_modified_file(handover_manager, mock_coder, tmp_path):
    test_file = tmp_path / "file1.py"
    test_file.write_text("print('hello')")
    mock_coder.abs_fnames = {str(test_file)}

    state = handover_manager.capture_current_state(coder=mock_coder)
    handover_manager.save_handover_state(state)

    # Modify the file after saving the state
    test_file.write_text("print('world')")

    loaded_state = handover_manager.load_handover_state()

    assert loaded_state is None

def test_restore_coder_from_handover_state(handover_manager, mock_coder, tmp_path):
    test_file = tmp_path / "file1.py"
    test_file.write_text("print('hello')")
    mock_coder.abs_fnames = {str(test_file)}

    state = handover_manager.capture_current_state(coder=mock_coder)
    handover_manager.save_handover_state(state)

    loaded_state = handover_manager.load_handover_state()

    new_coder = Mock()
    new_coder.main_model = {}
    new_coder.abs_fnames = set()

    # Restore the new_coder from the loaded_state
    new_coder.main_model["name"] = loaded_state.main_model["name"]
    new_coder.abs_fnames = set(loaded_state.active_files)

    assert new_coder.main_model["name"] == "test-model"
    assert str(test_file) in new_coder.abs_fnames