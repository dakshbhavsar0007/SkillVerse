from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime
import hashlib
import qrcode

# ── SECURITY ────────────────────────────────────────────────────
SECRET_KEY = "SKILLVERSE_PRIVATE_KEY_2026"  # keep this secret

# ── Canvas ──────────────────────────────────────────────────────
W, H = 2480, 1754  # A4 Landscape (300 DPI)

# ── Colors ──────────────────────────────────────────────────────
NAVY       = (8, 18, 36)
GOLD       = (212, 175, 55)
GOLD_LIGHT = (245, 222, 160)
GOLD_DIM   = (170, 140, 60)
WHITE      = (245, 245, 245)
SILVER     = (210, 210, 210)

# ── Font loader ─────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(BASE_DIR, "static", "fonts")

def _font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)

# ── Helpers ─────────────────────────────────────────────────────
def _tw(draw, text, font):
    return draw.textlength(text, font=font)

def _cx(draw, text, y, font, fill):
    w = _tw(draw, text, font)
    draw.text(((W - w) // 2, y), text, font=font, fill=fill)

def _cx_at(draw, text, y, font, fill, cx):
    w = _tw(draw, text, font)
    draw.text((cx - w // 2, y), text, font=font, fill=fill)

def _squiggle(draw, cx, y, color):
    draw.line([(cx-40, y), (cx-10, y+6), (cx+20, y-6), (cx+50, y)],
              fill=color, width=2)

# ── Hash Generator ──────────────────────────────────────────────
def generate_hash(student, skill, cert_id, order_id):
    raw = f"{student}{skill}{cert_id}{order_id}{SECRET_KEY}"
    return hashlib.sha256(raw.encode()).hexdigest()

# ── Decorative helpers ──────────────────────────────────────────

def _draw_corner_ornament(draw, cx, cy, size, angle_deg):
    """Draw a small diamond + lines corner ornament, rotated."""
    import math
    angle = math.radians(angle_deg)
    d = size // 2

    def rot(x, y):
        rx = x * math.cos(angle) - y * math.sin(angle)
        ry = x * math.sin(angle) + y * math.cos(angle)
        return (cx + rx, cy + ry)

    # Diamond
    pts = [rot(0, -d), rot(d*0.6, 0), rot(0, d), rot(-d*0.6, 0)]
    draw.polygon(pts, fill=GOLD)

    # Arms
    for dx, dy in [(0, d*1.6), (0, -d*1.6), (d*1.6, 0), (-d*1.6, 0)]:
        p1 = rot(dx * 0.55, dy * 0.55)
        p2 = rot(dx, dy)
        draw.line([p1, p2], fill=GOLD_DIM, width=3)


def _draw_medal(draw, cx, cy, r):
    """Draw a decorative circular medal / seal."""
    # Outer ring
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=GOLD, width=5)
    # Inner ring
    ri = int(r * 0.82)
    draw.ellipse([cx-ri, cy-ri, cx+ri, cy+ri], outline=GOLD_DIM, width=2)
    # Tick marks around ring
    import math
    for i in range(36):
        a = math.radians(i * 10)
        inner = r * 0.88
        outer = r * 0.97
        x1 = cx + inner * math.cos(a)
        y1 = cy + inner * math.sin(a)
        x2 = cx + outer * math.cos(a)
        y2 = cy + outer * math.sin(a)
        draw.line([(x1, y1), (x2, y2)], fill=GOLD_DIM, width=2)
    # Star in centre
    for i in range(8):
        a = math.radians(i * 45)
        x2 = cx + ri * 0.55 * math.cos(a)
        y2 = cy + ri * 0.55 * math.sin(a)
        draw.line([(cx, cy), (x2, y2)], fill=GOLD, width=3)
    draw.ellipse([cx-12, cy-12, cx+12, cy+12], fill=GOLD)


def _gradient_rect(img, x0, y0, x1, y1, col_top, col_bot):
    """Fill a vertical gradient stripe."""
    h = y1 - y0
    if h <= 0:
        return
    r0, g0, b0 = col_top
    r1, g1, b1 = col_bot
    pix = img.load()
    for dy in range(h):
        t   = dy / max(h - 1, 1)
        col = (int(r0 + (r1 - r0) * t),
               int(g0 + (g1 - g0) * t),
               int(b0 + (b1 - b0) * t))
        for x in range(x0, x1):
            pix[x, y0 + dy] = col


# ── Certificate Drawer ──────────────────────────────────────────
def draw_certificate(student_name, skill_name,
                     provider_name="SkillVerse",
                     order_id="SV-ORDER-001",
                     cert_id="CERT-XXXX",
                     completion_date=None):

    if completion_date is None:
        completion_date = datetime.now().strftime("%d %B %Y")

    # ── Generate Hash & QR ────────────────────────────────────
    cert_hash  = generate_hash(student_name, skill_name, cert_id, order_id)
    verify_url = f"https://skillverse.in/verify?cert_id={cert_id}&hash={cert_hash}"
    qr_size    = 300
    qr_img     = qrcode.make(verify_url).resize((qr_size, qr_size))

    # ── Canvas ────────────────────────────────────────────────
    img  = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(img)

    # ── Subtle gradient overlay (top lighter, bottom darker) ──
    NAVY_LIGHT = (14, 28, 54)
    NAVY_DARK  = (4, 10, 22)
    _gradient_rect(img, 0, 0, W, H, NAVY_LIGHT, NAVY_DARK)
    draw = ImageDraw.Draw(img)  # refresh after pixel manipulation

    # ── Left accent bar ───────────────────────────────────────
    bar_w = 18
    _gradient_rect(img, 0, 0, bar_w, H, GOLD, GOLD_DIM)
    _gradient_rect(img, W - bar_w, 0, W, H, GOLD_DIM, GOLD)
    draw = ImageDraw.Draw(img)

    # ── Outer border ─────────────────────────────────────────
    m = 52
    draw.rectangle([m, m, W-m, H-m], outline=GOLD, width=5)
    # Inner hairline
    draw.rectangle([m+14, m+14, W-m-14, H-m-14], outline=GOLD_DIM, width=1)

    # ── Corner ornaments ─────────────────────────────────────
    off = m + 6
    for (cx, cy, ang) in [
        (off, off, 45),
        (W-off, off, 135),
        (W-off, H-off, 225),
        (off, H-off, 315),
    ]:
        _draw_corner_ornament(draw, cx, cy, 28, ang)

    # ── Fonts ────────────────────────────────────────────────
    f_brand     = _font("Montserrat-SemiBold.ttf",  26)
    f_title     = _font("PlayfairDisplay-Bold.ttf",  72)
    f_sub       = _font("CormorantGaramond-Regular.ttf", 34)
    f_name      = _font("PlayfairDisplay-Bold.ttf",  100)
    f_skill     = _font("Montserrat-SemiBold.ttf",   48)
    f_prov      = _font("Montserrat-SemiBold.ttf",   32)
    f_small     = _font("Montserrat-Regular.ttf",    22)
    f_bold22    = _font("Montserrat-SemiBold.ttf",   24)
    f_tiny      = _font("Montserrat-Regular.ttf",    18)
    f_signature = _font("GreatVibes-Regular.ttf",    52)
    f_label     = _font("Montserrat-SemiBold.ttf",   19)

    # ── Decorative top rule (diamond + lines) ─────────────────
    top_rule_y = 148
    rule_cx    = W // 2
    draw.line([(m+30, top_rule_y), (rule_cx-50, top_rule_y)], fill=GOLD_DIM, width=1)
    draw.line([(rule_cx+50, top_rule_y), (W-m-30, top_rule_y)], fill=GOLD_DIM, width=1)
    draw.polygon([
        (rule_cx, top_rule_y-10),
        (rule_cx+10, top_rule_y),
        (rule_cx, top_rule_y+10),
        (rule_cx-10, top_rule_y),
    ], fill=GOLD)

    # ── Platform name ─────────────────────────────────────────
    _cx(draw, "S K I L L V E R S E", 170, f_brand, GOLD)

    # ── Main title ────────────────────────────────────────────
    _cx(draw, "Certificate of Completion", 218, f_title, WHITE)

    # ── Thin gold rule under title ────────────────────────────
    draw.line([(W//2-360, 314), (W//2+360, 314)], fill=GOLD_DIM, width=1)

    # ── Presented to ─────────────────────────────────────────
    _cx(draw, "This certificate is proudly presented to", 335, f_sub, SILVER)

    # ── Student name with glow shadow ────────────────────────
    name_y = 400
    # Shadow
    for ox, oy in [(-2, 2), (2, 2), (0, 3)]:
        nw = _tw(draw, student_name, f_name)
        draw.text(((W - nw) // 2 + ox, name_y + oy), student_name, font=f_name, fill=GOLD_DIM)
    _cx(draw, student_name, name_y, f_name, GOLD_LIGHT)

    # ── Ornamental divider under name ─────────────────────────
    div_y = 522
    draw.line([(W//2-500, div_y), (W//2-60, div_y)], fill=GOLD_DIM, width=1)
    draw.line([(W//2+60, div_y), (W//2+500, div_y)], fill=GOLD_DIM, width=1)
    draw.polygon([
        (W//2, div_y-12), (W//2+12, div_y),
        (W//2, div_y+12), (W//2-12, div_y),
    ], fill=GOLD)
    # Small dots flanking diamond
    for dx in [-30, 30]:
        draw.ellipse([W//2+dx-4, div_y-4, W//2+dx+4, div_y+4], fill=GOLD_DIM)

    # ── Course block ─────────────────────────────────────────
    _cx(draw, "for successfully completing", 552, f_sub, SILVER)

    # Skill name with background pill
    skill_w = int(_tw(draw, skill_name, f_skill))
    pill_pad = 40
    pill_x0  = (W - skill_w) // 2 - pill_pad
    pill_y0  = 598
    pill_x1  = (W + skill_w) // 2 + pill_pad
    pill_y1  = 668
    # Pill background
    draw.rounded_rectangle([pill_x0, pill_y0, pill_x1, pill_y1],
                            radius=12, fill=(20, 36, 68), outline=GOLD_DIM, width=1)
    _cx(draw, skill_name, 607, f_skill, GOLD)

    _cx(draw, "An online learning program offered by", 690, f_sub, SILVER)
    _cx(draw, provider_name, 732, f_prov, GOLD_LIGHT)

    # ── Horizontal separator ──────────────────────────────────
    sep_y = 800
    draw.line([(m+30, sep_y), (W-m-30, sep_y)], fill=GOLD_DIM, width=1)
    # Centre diamond on separator
    draw.polygon([
        (W//2, sep_y-8), (W//2+8, sep_y),
        (W//2, sep_y+8), (W//2-8, sep_y),
    ], fill=GOLD_DIM)

    # ── Info row (Order ID | Date | Cert ID) ──────────────────
    info_y   = 830
    col1     = W // 4
    col2     = W // 2
    col3     = 3 * W // 4

    # Labels
    for lbl, cx_ in [("ORDER ID", col1), ("DATE ISSUED", col2), ("CERTIFICATE ID", col3)]:
        _cx_at(draw, lbl, info_y, f_label, GOLD_DIM, cx_)

    # Values
    _cx_at(draw, f"#{order_id}", info_y + 32, f_bold22, WHITE, col1)
    _cx_at(draw, completion_date,              info_y + 32, f_bold22, WHITE, col2)
    _cx_at(draw, cert_id,                      info_y + 32, f_bold22, WHITE, col3)

    # ── Signature section ─────────────────────────────────────
    sig_y   = 940
    s1      = W // 3
    s2      = 2 * W // 3
    sig_len = 200

    # Left: SkillVerse founder
    sig      = "Daksh Bhavsar"
    sig_w_px = _tw(draw, sig, f_signature)
    sig_x    = int(s1 - sig_w_px // 2)
    # Shadow
    for ox, oy in [(-1, 1), (1, 1)]:
        draw.text((sig_x + ox, sig_y + oy), sig, font=f_signature, fill=GOLD_DIM)
    draw.text((sig_x, sig_y), sig, font=f_signature, fill=GOLD_LIGHT)

    draw.line([(s1 - sig_len//2, sig_y + 64), (s1 + sig_len//2, sig_y + 64)], fill=GOLD_DIM, width=1)
    _cx_at(draw, "Daksh Bhavsar", sig_y + 74, f_bold22, WHITE, s1)
    _cx_at(draw, "Founder & Director, SkillVerse", sig_y + 102, f_label, GOLD_DIM, s1)

    # Centre medal / seal
    _draw_medal(draw, W//2, sig_y + 60, 75)

    # Right: Provider authorized signature
    _squiggle(draw, s2, sig_y + 22, GOLD_LIGHT)
    _squiggle(draw, s2, sig_y + 36, GOLD_DIM)
    draw.line([(s2 - sig_len//2, sig_y + 64), (s2 + sig_len//2, sig_y + 64)], fill=GOLD_DIM, width=1)
    _cx_at(draw, provider_name, sig_y + 74, f_bold22, WHITE, s2)
    _cx_at(draw, "Authorized Signature", sig_y + 102, f_label, GOLD_DIM, s2)

    # ── Bottom bar: hash + QR label ───────────────────────────
    bottom_rule_y = H - m - 60
    draw.line([(m+30, bottom_rule_y), (W-m-30, bottom_rule_y)], fill=GOLD_DIM, width=1)

    draw.text((m + 30, bottom_rule_y + 12),
              f"Verification Hash: {cert_hash[:40]}...",
              font=f_tiny, fill=GOLD_DIM)
    _cx_at(draw, "Scan to Verify", bottom_rule_y + 12, f_tiny, GOLD_DIM, W - m - 80)

    # ── QR Code (bottom-right, inside border) ─────────────────
    qr_x = W - m - 30 - qr_size
    qr_y = H - m - 30 - qr_size
    # White background pad for QR
    pad = 8
    draw.rectangle([qr_x - pad, qr_y - pad,
                    qr_x + qr_size + pad, qr_y + qr_size + pad],
                   fill=WHITE)
    img.paste(qr_img, (qr_x, qr_y))

    return img


# ── Public API ──────────────────────────────────────────────────

def generate_cert_id():
    """
    Generate a unique certificate ID in the format CERT-XXXXXXXX.

    Returns:
        str: e.g. 'CERT-A1B2C3D4'
    """
    import uuid
    return f"CERT-{uuid.uuid4().hex[:8].upper()}"


def generate_certificate(student_name, skill_name,
                         provider_name="SkillVerse",
                         order_id="SV-ORDER-001",
                         cert_id=None,
                         template_path=None,
                         completion_date=None):
    """
    Generate a certificate, save it as a PDF, and return the saved file path.

    The file is always saved to  <app>/static/certificates/<cert_id>.pdf
    so that the download_certificate route (which looks in static/certificates/)
    can find it correctly.

    Args:
        student_name   (str): Full name of the student.
        skill_name     (str): Name of the completed skill / course.
        provider_name  (str): Issuing organisation / provider display name.
        order_id       (str|int): Order reference (stored on the certificate).
        cert_id        (str|None): Certificate ID; auto-generated if None.
        template_path  (str|None): Accepted for compatibility; not used.
        completion_date (str|None): Human-readable date; defaults to today.

    Returns:
        str: Absolute path to the saved certificate PDF file.
    """
    if cert_id is None:
        cert_id = generate_cert_id()

    if completion_date is None:
        completion_date = datetime.now().strftime("%d %B %Y")

    # Always save into static/certificates/ — this is where the download
    # route expects to find the file (routes.py line ~1651).
    output_dir = os.path.join(BASE_DIR, "static", "certificates")
    os.makedirs(output_dir, exist_ok=True)

    # Save as PDF (the download route sets mimetype='application/pdf').
    filename    = f"{cert_id}.pdf"
    output_path = os.path.join(output_dir, filename)

    img = draw_certificate(
        student_name    = student_name,
        skill_name      = skill_name,
        provider_name   = provider_name,
        order_id        = str(order_id),
        cert_id         = cert_id,
        completion_date = completion_date,
    )

    # Pillow can save directly as PDF when the path ends in .pdf
    img.save(output_path, "PDF", resolution=300)
    return output_path


# ── Test ────────────────────────────────────────────────────────
if __name__ == "__main__":
    cert = draw_certificate(
        student_name="John Doe",
        skill_name="Python Programming",
        order_id="SV-2026-001",
        cert_id="CERT-9E9077"
    )
    cert.save("skillverse_certificate_verified.png")
    print("✅ Secure certificate generated with QR + hash!")