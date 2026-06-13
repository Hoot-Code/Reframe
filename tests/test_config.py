"""Tests for config.py — configuration validation and edge cases."""

import os
import pytest
from unittest.mock import patch


class TestIntEnv:
    def test_valid_int(self):
        from config import _int_env
        with patch.dict(os.environ, {"TEST_KEY": "10"}):
            assert _int_env("TEST_KEY", 5) == 10

    def test_default_value(self):
        from config import _int_env
        assert _int_env("NONEXISTENT_KEY_12345", 7) == 7

    def test_non_numeric_returns_default(self):
        from config import _int_env
        with patch.dict(os.environ, {"TEST_KEY": "abc"}):
            assert _int_env("TEST_KEY", 5) == 5

    def test_zero_clamped_to_one(self):
        from config import _int_env
        with patch.dict(os.environ, {"TEST_KEY": "0"}):
            assert _int_env("TEST_KEY", 5) == 1

    def test_negative_clamped_to_one(self):
        from config import _int_env
        with patch.dict(os.environ, {"TEST_KEY": "-5"}):
            assert _int_env("TEST_KEY", 5) == 1

    def test_empty_string_returns_default(self):
        from config import _int_env
        with patch.dict(os.environ, {"TEST_KEY": ""}):
            assert _int_env("TEST_KEY", 5) == 5


class TestPresetSizes:
    def test_all_presets_have_valid_dimensions(self):
        from config import PRESET_SIZES
        for label, (w, h) in PRESET_SIZES.items():
            assert isinstance(w, int) and w > 0, f"Invalid width for {label}"
            assert isinstance(h, int) and h > 0, f"Invalid height for {label}"

    def test_no_duplicates(self):
        from config import PRESET_SIZES
        dims = list(PRESET_SIZES.values())
        assert len(dims) == len(set(dims)), "Duplicate preset dimensions found"

    def test_all_within_max_resolution(self):
        from config import PRESET_SIZES, CONFIG
        max_r = CONFIG["max_resolution"]
        for label, (w, h) in PRESET_SIZES.items():
            assert w <= max_r, f"{label} width {w} exceeds max {max_r}"
            assert h <= max_r, f"{label} height {h} exceeds max {max_r}"


class TestConversationStates:
    def test_states_are_unique(self):
        from config import (
            SELECT_LANG, SELECT_SIZE, CUSTOM_SIZE,
            SELECT_MODE, SELECT_FORMAT, ADMIN_MENU, ADMIN_INPUT
        )
        states = [SELECT_LANG, SELECT_SIZE, CUSTOM_SIZE,
                  SELECT_MODE, SELECT_FORMAT, ADMIN_MENU, ADMIN_INPUT]
        assert len(states) == len(set(states)), "Duplicate state values"

    def test_states_are_sequential(self):
        from config import (
            SELECT_LANG, SELECT_SIZE, CUSTOM_SIZE,
            SELECT_MODE, SELECT_FORMAT, ADMIN_MENU, ADMIN_INPUT
        )
        assert SELECT_LANG == 0
        assert SELECT_SIZE == 1
        assert CUSTOM_SIZE == 2
        assert SELECT_MODE == 3
        assert SELECT_FORMAT == 4
        assert ADMIN_MENU == 5
        assert ADMIN_INPUT == 6
