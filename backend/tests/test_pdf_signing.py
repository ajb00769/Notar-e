import io
import pytest
from pypdf import PdfReader
from app.utils import pdf_signing


@pytest.fixture
def sample_signatures():
    return [
        {
            "role": "notary",
            "user_id": 1,
            "signature": "sig1",
            "timestamp": "2024-01-01T12:00:00Z",
        },
        {
            "role": "client",
            "user_id": 2,
            "signature": "sig2",
            "timestamp": "2024-01-01T12:05:00Z",
        },
    ]


@pytest.fixture
def blank_pdf_bytes():
    # Create a simple 1-page blank PDF in memory
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.drawString(100, 500, "Test PDF")
    can.save()
    packet.seek(0)
    return packet.read()


def test_create_signature_overlay(sample_signatures):
    # Use standard letter size for test
    width, height = 612, 792  # points for letter
    overlay_pdf = pdf_signing.create_signature_overlay(sample_signatures, width, height)
    assert isinstance(overlay_pdf, PdfReader)
    assert len(overlay_pdf.pages) == 1


def test_embed_signatures_in_pdf(blank_pdf_bytes, sample_signatures):
    signed_pdf_bytes = pdf_signing.embed_signatures_in_pdf(
        blank_pdf_bytes, sample_signatures
    )
    assert isinstance(signed_pdf_bytes, bytes)
    reader = PdfReader(io.BytesIO(signed_pdf_bytes))
    assert len(reader.pages) == 1
    # Optionally, check that the PDF content has changed (overlay applied)
    # This is a basic check: the content stream should be longer
    original_len = len(blank_pdf_bytes)
    signed_len = len(signed_pdf_bytes)
    assert signed_len > original_len
