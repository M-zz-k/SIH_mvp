import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_contract import FieldName, TextBlock  # noqa: E402
from field_extractor import extract_fields  # noqa: E402
from ocr_engine import MockOCREngine  # noqa: E402


def make_block(text, confidence=0.95, height=14.0, y=0.0):
    return TextBlock(
        text=text,
        confidence=confidence,
        bbox=((0, y), (100, y), (100, y + height), (0, y + height)),
        line_height_px=height,
    )


def test_mrp_extraction():
    blocks = [make_block("MRP: Rs. 199.00 (Incl. of all taxes)")]
    fields = extract_fields(blocks)
    mrp = next(f for f in fields if f.field == FieldName.MRP)
    assert mrp.found
    assert mrp.value == "199.00"


def test_mrp_extraction_alt_format():
    blocks = [make_block("M.R.P. ₹499")]
    fields = extract_fields(blocks)
    mrp = next(f for f in fields if f.field == FieldName.MRP)
    assert mrp.found
    assert mrp.value == "499"


def test_net_quantity_grams():
    blocks = [make_block("Net Qty: 250 g")]
    fields = extract_fields(blocks)
    qty = next(f for f in fields if f.field == FieldName.NET_QUANTITY)
    assert qty.found
    assert qty.value == "250"
    assert qty.unit.lower() == "g"


def test_net_quantity_ml():
    blocks = [make_block("Net Volume: 500ml")]
    fields = extract_fields(blocks)
    qty = next(f for f in fields if f.field == FieldName.NET_QUANTITY)
    assert qty.found
    assert qty.value == "500"
    assert qty.unit.lower() == "ml"


def test_mfg_date():
    blocks = [make_block("Mfg. Date: 03/2026")]
    fields = extract_fields(blocks)
    mfg = next(f for f in fields if f.field == FieldName.MFG_DATE)
    assert mfg.found
    assert mfg.value == "03/2026"


def test_consumer_care_phone_and_email():
    blocks = [make_block("Customer Care: 1800-123-4567, care@brand.com")]
    fields = extract_fields(blocks)
    care = next(f for f in fields if f.field == FieldName.CONSUMER_CARE)
    assert care.found
    assert "1800" in care.value


def test_country_of_origin():
    blocks = [make_block("Country of Origin: India")]
    fields = extract_fields(blocks)
    coo = next(f for f in fields if f.field == FieldName.COUNTRY_OF_ORIGIN)
    assert coo.found
    assert coo.value.strip() == "India"


def test_manufacturer_name_and_address_multiline():
    blocks = [
        make_block("Manufactured by: Sunrise Foods Pvt. Ltd.,", y=0.0),
        make_block("Plot 12, MIDC, Pune, Maharashtra - 411019", y=20.0),
    ]
    fields = extract_fields(blocks)
    mfr = next(f for f in fields if f.field == FieldName.MANUFACTURER_NAME)
    addr = next(f for f in fields if f.field == FieldName.MANUFACTURER_ADDRESS)
    assert mfr.found
    assert "Sunrise Foods" in mfr.value
    assert addr.found
    assert "MIDC" in addr.value


def test_missing_field_is_reported_not_found():
    blocks = [make_block("Some unrelated packaging text with no fields")]
    fields = extract_fields(blocks)
    mrp = next(f for f in fields if f.field == FieldName.MRP)
    assert mrp.found is False
    assert mrp.value is None


def test_batch_number():
    blocks = [make_block("Batch No: AB1234/26")]
    fields = extract_fields(blocks)
    batch = next(f for f in fields if f.field == FieldName.BATCH_NUMBER)
    assert batch.found
    assert batch.value == "AB1234/26"


def test_end_to_end_with_mock_ocr_engine():
    """Simulates the full pipeline (minus image I/O) using MockOCREngine's
    deterministic fake label, to prove OCR output -> field extraction wiring
    works before a real image/PaddleOCR is available."""
    engine = MockOCREngine()
    blocks = engine.extract("fake_path.jpg")
    fields = extract_fields(blocks)
    found = {f.field: f for f in fields if f.found}

    assert FieldName.MRP in found
    assert found[FieldName.MRP].value == "199.00"
    assert FieldName.NET_QUANTITY in found
    assert found[FieldName.NET_QUANTITY].value == "250"
    assert FieldName.MFG_DATE in found
    assert FieldName.MANUFACTURER_NAME in found
    assert FieldName.MANUFACTURER_ADDRESS in found
    assert FieldName.CONSUMER_CARE in found
    assert FieldName.COUNTRY_OF_ORIGIN in found
