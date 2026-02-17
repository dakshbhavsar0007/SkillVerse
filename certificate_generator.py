"""
Certificate Generator for SkillVerse

Overlays real user data onto the Antigravity-designed certificate template.
Generates a downloadable PDF certificate when an order is marked complete.

Usage:
    from certificate_generator import generate_certificate
    pdf_path = generate_certificate(
        student_name="John Doe",
        skill_name="1-on-1 Python Programming Lessons",
        provider_name="Daksh Bhavsar",
        order_id=145,
        cert_id="CERT-A1B2C3"
    )
"""

import os
import uuid
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
import io


# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR        = os.path.abspath(os.path.dirname(__file__))
TEMPLATE_PATH   = os.path.join(BASE_DIR, 'static', 'certificate_template.png')
CERTS_FOLDER    = os.path.join(BASE_DIR, 'static', 'certificates')
FONTS_DIR       = os.path.join(BASE_DIR, 'static', 'fonts')

os.makedirs(CERTS_FOLDER, exist_ok=True)
os.makedirs(FONTS_DIR,    exist_ok=True)


# ── Font helpers ─────────────────────────────────────────────────────────────

def _load_font(filename, size):
    """Load a font file, falling back to PIL default if not found."""
    path = os.path.join(FONTS_DIR, filename)
    try:
        return ImageFont.truetype(path, size)
    except (IOError, OSError):
        # Try system fonts as fallback
        for sys_path in [
            f'/usr/share/fonts/truetype/dejavu/{filename}',
            f'/usr/share/fonts/truetype/liberation/{filename}',
            f'/System/Library/Fonts/{filename}',
        ]:
            try:
                return ImageFont.truetype(sys_path, size)
            except (IOError, OSError):
                continue
        return ImageFont.load_default()


def _draw_centered_text(draw, text, y, font, color):
    """Draw text horizontally centered on a 2480px wide canvas."""
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
    except AttributeError:
        text_width = draw.textlength(text, font=font)
    x = (2480 - text_width) // 2
    draw.text((x, y), text, font=font, fill=color)


# ── Core generator ────────────────────────────────────────────────────────────

def generate_certificate(student_name: str,
                         skill_name: str,
                         provider_name: str,
                         order_id: int,
                         cert_id: str = None,
                         completion_date: str = None,
                         template_path: str = None) -> str:
    """
    Overlay student data onto the certificate template and save as PDF.

    Args:
        student_name    : Full name of the student/buyer
        skill_name      : Name of the completed skill/service
        provider_name   : Name of the provider/instructor
        order_id        : Order ID number
        cert_id         : Certificate ID (auto-generated if None)
        completion_date : Date string e.g. "February 17, 2026" (today if None)
        template_path   : Optional absolute path to override default template location

    Returns:
        str: Absolute path to the generated PDF file
    """
    if not cert_id:
        cert_id = f"CERT-{uuid.uuid4().hex[:6].upper()}"
    if not completion_date:
        completion_date = datetime.now().strftime("%B %d, %Y")

    # ── Load template ─────────────────────────────────────────────────────
    if not template_path:
        template_path = TEMPLATE_PATH

    print(f"[CertGen] Looking for template at: {template_path}")
    
    if not os.path.exists(template_path):
        # Debugging info for logs
        error_msg = (
            f"Certificate template not found at {template_path}. "
            f"CWD: {os.getcwd()}, Base: {BASE_DIR}. "
            f"Exists? {os.path.exists(template_path)}"
        )
        print(error_msg)
        raise FileNotFoundError(error_msg)

    img = Image.open(template_path).convert('RGBA')
    # Work at high resolution — template is ~2480x2480 (square from Antigravity)
    W, H = img.size

    draw = ImageDraw.Draw(img)

    # ── Colours ───────────────────────────────────────────────────────────
    GOLD      = (184, 134,  11)   # dark gold, readable on cream background
    DARK_NAVY = ( 15,  15,  60)
    DARK_GREY = ( 60,  60,  60)

    # ── Font sizes (scale relative to image width) ─────────────────────
    scale = W / 2480

    # Try to use elegant fonts; falls back to system fonts gracefully
    name_font     = _load_font('GreatVibes-Regular.ttf',   int(160 * scale))
    skill_font    = _load_font('MontserratBold.ttf',       int(80  * scale))
    body_font     = _load_font('Montserrat-Regular.ttf',   int(55  * scale))
    small_font    = _load_font('Montserrat-Regular.ttf',   int(42  * scale))

    # ── Y-positions (tuned to the Antigravity template layout) ───────────
    # These percentages match where the placeholder text sits in the design
    NAME_Y      = int(H * 0.445)   # [USER NAME] cursive line
    SKILL_Y     = int(H * 0.555)   # [SKILL NAME] bold line
    PROVIDER_Y  = int(H * 0.615)   # Under the guidance of...
    DATE_Y      = int(H * 0.835)   # bottom detail line
    CERT_Y      = int(H * 0.860)
    ORDER_Y     = int(H * 0.885)

    # ── Draw student name (large gold cursive) ────────────────────────────
    _draw_centered_text(draw, student_name, NAME_Y, name_font, GOLD)

    # ── Draw skill name (bold navy) ───────────────────────────────────────
    _draw_centered_text(draw, skill_name, SKILL_Y, skill_font, DARK_NAVY)

    # ── Draw provider line ────────────────────────────────────────────────
    provider_text = f"Under the guidance of {provider_name}"
    _draw_centered_text(draw, provider_text, PROVIDER_Y, body_font, DARK_GREY)

    # ── Draw bottom details ───────────────────────────────────────────────
    _draw_centered_text(draw, f"Date: {completion_date}", DATE_Y, small_font, DARK_GREY)
    _draw_centered_text(draw, f"Certificate ID: {cert_id}", CERT_Y, small_font, DARK_GREY)
    _draw_centered_text(draw, f"Order #{order_id}", ORDER_Y, small_font, DARK_GREY)

    # ── Save as PNG in memory, then embed in PDF ──────────────────────────
    img_rgb = img.convert('RGB')
    img_buffer = io.BytesIO()
    img_rgb.save(img_buffer, format='PNG', dpi=(300, 300))
    img_buffer.seek(0)

    # ── Create PDF (A4 landscape) ─────────────────────────────────────────
    pdf_filename = f"certificate_order{order_id}_{cert_id}.pdf"
    pdf_path     = os.path.join(CERTS_FOLDER, pdf_filename)

    page_w, page_h = landscape(A4)  # 841.9 x 595.3 points

    c = canvas.Canvas(pdf_path, pagesize=landscape(A4))
    c.setTitle(f"SkillVerse Certificate - {student_name}")
    c.setAuthor("SkillVerse Platform")
    c.setSubject(f"Certificate of Completion: {skill_name}")

    # Draw the certificate image filling the whole A4 landscape page
    c.drawImage(
        img_buffer,
        0, 0,
        width=page_w,
        height=page_h,
        preserveAspectRatio=True,
        anchor='c'
    )

    c.save()
    return pdf_path


# ── Convenience: generate cert_id ─────────────────────────────────────────────

def generate_cert_id() -> str:
    return f"CERT-{uuid.uuid4().hex[:6].upper()}"
