"""Unit tests for M4000 D: field interpretation (no Flask / pyfakefs)."""

from unittest import TestCase
from unittest.mock import patch

from mariner.printer import PrinterState
from mariner.server.api import _file_byte_for_layer_lookup, reset_m4000_d_tracking


class M4000FileByteTest(TestCase):
    def tearDown(self) -> None:
        reset_m4000_d_tracking()

    def test_auto_read_single_sample(self) -> None:
        reset_m4000_d_tracking()
        pos = _file_byte_for_layer_lookup(256537, 832745, PrinterState.PRINTING)
        self.assertEqual(pos, 256537)

    def test_auto_bytes_remaining_after_starting_print(self) -> None:
        reset_m4000_d_tracking()
        self.assertEqual(
            _file_byte_for_layer_lookup(0, 832745, PrinterState.STARTING_PRINT), 0
        )
        pos = _file_byte_for_layer_lookup(800000, 832745, PrinterState.PRINTING)
        self.assertEqual(pos, 32745)

    def test_auto_detect_remaining_from_decreasing_sequence(self) -> None:
        reset_m4000_d_tracking()
        self.assertEqual(
            _file_byte_for_layer_lookup(500000, 832745, PrinterState.PRINTING), 500000
        )
        pos = _file_byte_for_layer_lookup(490000, 832745, PrinterState.PRINTING)
        self.assertEqual(pos, 832745 - 490000)

    def test_idle_resets_tracking(self) -> None:
        reset_m4000_d_tracking()
        _file_byte_for_layer_lookup(100, 1000, PrinterState.PRINTING)
        _file_byte_for_layer_lookup(0, 0, PrinterState.IDLE)
        pos = _file_byte_for_layer_lookup(256537, 832745, PrinterState.PRINTING)
        self.assertEqual(pos, 256537)

    @patch("mariner.server.api.config.get_m4000_d_field", return_value="remaining")
    def test_config_forces_remaining(self, _: object) -> None:
        reset_m4000_d_tracking()
        pos = _file_byte_for_layer_lookup(800000, 832745, PrinterState.PRINTING)
        self.assertEqual(pos, 32745)
