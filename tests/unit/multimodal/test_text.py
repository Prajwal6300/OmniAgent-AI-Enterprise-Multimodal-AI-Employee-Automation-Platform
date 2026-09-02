from multimodal.text.processor import TextProcessor

def test_text_processor_clean():
    processor = TextProcessor()
    raw = "  Enterprise    Multimodal \n\n AI  "
    cleaned = processor.clean(raw)
    assert cleaned == "Enterprise Multimodal AI"
