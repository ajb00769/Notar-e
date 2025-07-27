import io
import copy
from typing import List, Dict
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch


def create_signature_overlay(signatures: List[Dict], page_width, page_height):
    """
    Create a PDF overlay with all signatures as text at the bottom of the page.
    signatures: List of dicts with keys: role, user_id, signature, timestamp
    """
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(page_width, page_height))
    y = 0.5 * inch
    for sig in signatures:
        text = f"Signed by {sig['role']} (user {sig['user_id']}) at {sig['timestamp']}"
        can.drawString(1 * inch, y, text)
        y += 0.3 * inch
    can.save()
    packet.seek(0)
    return PdfReader(packet)


def embed_signatures_in_pdf(original_pdf_bytes: bytes, signatures: List[Dict]) -> bytes:
    """
    Returns a new PDF with signatures overlaid on the first page.
    """
    reader = PdfReader(io.BytesIO(original_pdf_bytes))
    writer = PdfWriter()
    first_page = reader.pages[0]
    page_width = float(first_page.mediabox.width)
    page_height = float(first_page.mediabox.height)
    overlay_pdf = create_signature_overlay(signatures, page_width, page_height)
    overlay_page = overlay_pdf.pages[0]
    # Deep copy the first page before merging
    merged_page = copy.deepcopy(first_page)
    merged_page.merge_page(overlay_page)
    writer.add_page(merged_page)
    # Add remaining pages unchanged
    for page in reader.pages[1:]:
        writer.add_page(page)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()
