import pathlib
from unittest import TestCase

import png
from pyexpect import expect

from mariner.file_formats.ctb_encrypted import CTBEncryptedFile, check_encrypted
from mariner.file_formats.utils import get_file_format


class BoltsEncryptedCTBTest(TestCase):
    def test_bolts_ctb_is_detected_as_encrypted(self) -> None:
        path = pathlib.Path(__file__).parent.absolute() / "bolts.ctb"
        expect(check_encrypted(str(path))).to_equal(CTBEncryptedFile)
        expect(get_file_format(str(path))).to_equal(CTBEncryptedFile)

    def test_bolts_ctb_metadata_and_layer_end_offsets(self) -> None:
        path = pathlib.Path(__file__).parent.absolute() / "bolts.ctb"
        ctb = CTBEncryptedFile.read(path)
        expect(ctb.filename).to_equal("bolts.ctb")
        expect(ctb.layer_count).to_equal(110)
        expect(len(ctb.end_byte_offset_by_layer)).to_equal(110)
        expect(ctb.resolution).to_equal((4098, 2560))
        expect(ctb.print_time_secs).to_equal(872)
        expect(ctb.bed_size_mm[0]).close_to(143.43, max_delta=1e-2)
        offs = ctb.end_byte_offset_by_layer
        expect(offs[0]).to_equal(177413)
        expect(offs[1]).to_equal(184178)
        expect(offs[-1]).to_equal(866843)
        self.assertEqual(offs, sorted(offs))

    def test_bolts_ctb_preview_renders(self) -> None:
        path = pathlib.Path(__file__).parent.absolute() / "bolts.ctb"
        preview: png.Image = CTBEncryptedFile.read_preview(path)
        expect(preview.info["bitdepth"]).to_equal(5)
        expect(preview.info["alpha"]).is_false()
