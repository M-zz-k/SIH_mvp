if __package__:
    from .data_contract import (
        CONTRACT_VERSION,
        ExtractedField,
        FieldName,
        LabelExtractionResult,
        TextBlock,
    )
    from .field_extractor import extract_fields
    from .ocr_engine import MockOCREngine, OCREngine, get_engine
    from .pipeline import process_batch, process_label_image
else:
    from data_contract import (
        CONTRACT_VERSION,
        ExtractedField,
        FieldName,
        LabelExtractionResult,
        TextBlock,
    )
    from field_extractor import extract_fields
    from ocr_engine import MockOCREngine, OCREngine, get_engine
    from pipeline import process_batch, process_label_image

__all__ = [
    "CONTRACT_VERSION",
    "ExtractedField",
    "FieldName",
    "LabelExtractionResult",
    "TextBlock",
    "extract_fields",
    "MockOCREngine",
    "OCREngine",
    "get_engine",
    "process_batch",
    "process_label_image",
]
