from backend.app.utils.file_utils import get_file_extension

def test_file_extension_check():
    assert get_file_extension("invoice.PDF") == ".pdf"
    assert get_file_extension("malicious.exe") == ".exe"
