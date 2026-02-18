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
    import math
    angle = math.radians(angle_deg)
    d = size // 2
    def rot(x, y):
        return (cx + x*math.cos(angle) - y*math.sin(angle),
                cy + x*math.sin(angle) + y*math.cos(angle))
    pts = [rot(0,-d), rot(d*0.6,0), rot(0,d), rot(-d*0.6,0)]
    draw.polygon(pts, fill=GOLD)
    for dx, dy in [(0,d*1.8),(0,-d*1.8),(d*1.8,0),(-d*1.8,0)]:
        draw.line([rot(dx*0.5,dy*0.5), rot(dx,dy)], fill=GOLD_DIM, width=3)

def _draw_medal(draw, cx, cy, r):
    import math
    draw.ellipse([cx-r,cy-r,cx+r,cy+r], outline=GOLD, width=6)
    ri = int(r*0.82)
    draw.ellipse([cx-ri,cy-ri,cx+ri,cy+ri], outline=GOLD_DIM, width=2)
    for i in range(36):
        a = math.radians(i*10)
        x1,y1 = cx+r*0.88*math.cos(a), cy+r*0.88*math.sin(a)
        x2,y2 = cx+r*0.97*math.cos(a), cy+r*0.97*math.sin(a)
        draw.line([(x1,y1),(x2,y2)], fill=GOLD_DIM, width=2)
    for i in range(8):
        a = math.radians(i*45)
        draw.line([(cx,cy),(cx+ri*0.52*math.cos(a),cy+ri*0.52*math.sin(a))],
                  fill=GOLD, width=4)
    draw.ellipse([cx-14,cy-14,cx+14,cy+14], fill=GOLD)

def _gradient_bg(img):
    NAVY_LIGHT = (14, 28, 54)
    NAVY_DARK  = (4, 10, 22)
    pix = img.load()
    for dy in range(H):
        t = dy / (H-1)
        col = (int(NAVY_LIGHT[0]+(NAVY_DARK[0]-NAVY_LIGHT[0])*t),
               int(NAVY_LIGHT[1]+(NAVY_DARK[1]-NAVY_LIGHT[1])*t),
               int(NAVY_LIGHT[2]+(NAVY_DARK[2]-NAVY_LIGHT[2])*t))
        for dx in range(W):
            pix[dx, dy] = col

def _diamond(draw, cx, cy, r, fill):
    draw.polygon([(cx,cy-r),(cx+r,cy),(cx,cy+r),(cx-r,cy)], fill=fill)


# ── Certificate Drawer ──────────────────────────────────────────
def draw_certificate(student_name, skill_name,
                     provider_name="SkillVerse",
                     order_id="SV-ORDER-001",
                     cert_id="CERT-XXXX",
                     completion_date=None):

    if completion_date is None:
        completion_date = datetime.now().strftime("%d %B %Y")

    cert_hash  = generate_hash(student_name, skill_name, cert_id, order_id)
    verify_url = f"https://skillverse.in/verify?cert_id={cert_id}&hash={cert_hash}"

    # ── QR (larger for clarity) ────────────────────────────────
    QR = 320
    qr_img = qrcode.make(verify_url).resize((QR, QR))

    # ── Canvas + gradient ─────────────────────────────────────
    img = Image.new("RGB", (W, H), NAVY)
    _gradient_bg(img)
    draw = ImageDraw.Draw(img)

    # ── Side accent bars ──────────────────────────────────────
    BAR = 20
    for x in range(BAR):
        t = x / BAR
        c = (int(GOLD[0]*(1-t)+GOLD_DIM[0]*t),
             int(GOLD[1]*(1-t)+GOLD_DIM[1]*t),
             int(GOLD[2]*(1-t)+GOLD_DIM[2]*t))
        draw.line([(x,0),(x,H)], fill=c)
        draw.line([(W-1-x,0),(W-1-x,H)], fill=c)

    # ── Borders ───────────────────────────────────────────────
    m = 60
    draw.rectangle([m,m,W-m,H-m], outline=GOLD, width=5)
    draw.rectangle([m+16,m+16,W-m-16,H-m-16], outline=GOLD_DIM, width=1)

    # ── Corner ornaments ──────────────────────────────────────
    off = m + 4
    for cx_, cy_, ang in [(off,off,45),(W-off,off,135),(W-off,H-off,225),(off,H-off,315)]:
        _draw_corner_ornament(draw, cx_, cy_, 30, ang)

    # ── Fonts ─────────────────────────────────────────────────
    f_brand  = _font("Montserrat-SemiBold.ttf",  30)
    f_title  = _font("PlayfairDisplay-Bold.ttf",  80)
    f_sub    = _font("CormorantGaramond-Regular.ttf", 38)
    f_name   = _font("PlayfairDisplay-Bold.ttf",  110)
    f_skill  = _font("Montserrat-SemiBold.ttf",   52)
    f_prov   = _font("Montserrat-SemiBold.ttf",   36)
    f_label  = _font("Montserrat-SemiBold.ttf",   22)
    f_val    = _font("Montserrat-SemiBold.ttf",   28)
    f_sig    = _font("GreatVibes-Regular.ttf",     60)
    f_signame= _font("Montserrat-SemiBold.ttf",   26)
    f_sigrole= _font("Montserrat-SemiBold.ttf",   20)
    f_tiny   = _font("Montserrat-Regular.ttf",    19)

    # ═══════════════════════════════════════════════════════════
    # LAYOUT — all Y coords proportional to H=1754
    # ═══════════════════════════════════════════════════════════

    # ── Top ornamental rule  y≈130 ────────────────────────────
    ry = 132
    draw.line([(m+40, ry),(W//2-60, ry)], fill=GOLD_DIM, width=1)
    draw.line([(W//2+60, ry),(W-m-40, ry)], fill=GOLD_DIM, width=1)
    _diamond(draw, W//2, ry, 12, GOLD)

    # ── Platform name  y≈160 ─────────────────────────────────
    _cx(draw, "S K I L L V E R S E", 158, f_brand, GOLD)

    # ── Main title  y≈210 ────────────────────────────────────
    _cx(draw, "Certificate of Completion", 205, f_title, WHITE)

    # ── Rule under title  y≈305 ──────────────────────────────
    draw.line([(W//2-380, 308),(W//2+380, 308)], fill=GOLD_DIM, width=1)

    # ── Presented to  y≈325 ──────────────────────────────────
    _cx(draw, "This certificate is proudly presented to", 325, f_sub, SILVER)

    # ── Student name  y≈390 ──────────────────────────────────
    # Shadow
    nw = int(_tw(draw, student_name, f_name))
    nx = (W - nw) // 2
    for ox, oy in [(-2,3),(2,3),(0,4)]:
        draw.text((nx+ox, 390+oy), student_name, font=f_name, fill=GOLD_DIM)
    _cx(draw, student_name, 390, f_name, GOLD_LIGHT)

    # ── Divider under name  y≈520 ────────────────────────────
    draw.line([(W//2-520, 524),(W//2-65, 524)], fill=GOLD_DIM, width=1)
    draw.line([(W//2+65, 524),(W//2+520, 524)], fill=GOLD_DIM, width=1)
    _diamond(draw, W//2,    524, 14, GOLD)
    _diamond(draw, W//2-38, 524,  6, GOLD_DIM)
    _diamond(draw, W//2+38, 524,  6, GOLD_DIM)

    # ── "for successfully completing"  y≈555 ─────────────────
    _cx(draw, "for successfully completing", 555, f_sub, SILVER)

    # ── Skill pill  y≈610 ────────────────────────────────────
    sk_w = int(_tw(draw, skill_name, f_skill))
    pp   = 44
    px0, py0 = (W-sk_w)//2 - pp, 608
    px1, py1 = (W+sk_w)//2 + pp, 682
    draw.rounded_rectangle([px0,py0,px1,py1], radius=14,
                            fill=(18,34,62), outline=GOLD_DIM, width=1)
    _cx(draw, skill_name, 616, f_skill, GOLD)

    # ── "offered by"  y≈705 ──────────────────────────────────
    _cx(draw, "An online learning program offered by", 705, f_sub, SILVER)

    # ── Provider name  y≈755 ─────────────────────────────────
    _cx(draw, provider_name, 754, f_prov, GOLD_LIGHT)

    # ── Main separator  y≈830 ────────────────────────────────
    sep = 832
    draw.line([(m+40, sep),(W-m-40, sep)], fill=GOLD_DIM, width=1)
    _diamond(draw, W//2, sep, 10, GOLD_DIM)

    # ── Info row  y≈860 ──────────────────────────────────────
    info_y = 862
    c1, c2, c3 = W//4, W//2, 3*W//4

    _cx_at(draw, "ORDER ID",       info_y,      f_label, GOLD_DIM, c1)
    _cx_at(draw, "DATE ISSUED",    info_y,      f_label, GOLD_DIM, c2)
    _cx_at(draw, "CERTIFICATE ID", info_y,      f_label, GOLD_DIM, c3)

    _cx_at(draw, f"#{order_id}",   info_y + 40, f_val,   WHITE,    c1)
    _cx_at(draw, completion_date,  info_y + 40, f_val,   WHITE,    c2)
    _cx_at(draw, cert_id,          info_y + 40, f_val,   WHITE,    c3)

    # Vertical dividers between info cols
    for vx in [W//4 + W//8, W//2 + W//8]:
        draw.line([(vx, info_y-4),(vx, info_y+80)], fill=GOLD_DIM, width=1)

    # ── Second separator  y≈970 ──────────────────────────────
    sep2 = 972
    draw.line([(m+40, sep2),(W-m-40, sep2)], fill=GOLD_DIM, width=1)
    _diamond(draw, W//2, sep2, 10, GOLD_DIM)

    # ── Signatures  y≈1010–1160 ──────────────────────────────
    s1, s2 = W//3, 2*W//3
    sig_script_y  = 1010
    sig_line_y    = 1108
    sig_name_y    = 1118
    sig_role_y    = 1150

    # Left: Daksh Bhavsar
    sig_txt = "Daksh Bhavsar"
    sw = int(_tw(draw, sig_txt, f_sig))
    sx = s1 - sw//2
    for ox,oy in [(-1,2),(1,2)]:
        draw.text((sx+ox, sig_script_y+oy), sig_txt, font=f_sig, fill=GOLD_DIM)
    draw.text((sx, sig_script_y), sig_txt, font=f_sig, fill=GOLD_LIGHT)

    draw.line([(s1-180, sig_line_y),(s1+180, sig_line_y)], fill=GOLD_DIM, width=1)
    _cx_at(draw, "Daksh Bhavsar",              sig_name_y, f_signame, WHITE,    s1)
    _cx_at(draw, "Founder & Director, SkillVerse", sig_role_y, f_sigrole, GOLD_DIM, s1)

    # Centre: medal
    _draw_medal(draw, W//2, sig_line_y - 20, 90)

    # Right: provider
    _squiggle(draw, s2-30, sig_script_y + 30, GOLD_LIGHT)
    _squiggle(draw, s2-30, sig_script_y + 56, GOLD_DIM)
    _squiggle(draw, s2-30, sig_script_y + 82, GOLD_LIGHT)

    draw.line([(s2-180, sig_line_y),(s2+180, sig_line_y)], fill=GOLD_DIM, width=1)
    _cx_at(draw, provider_name,        sig_name_y, f_signame, WHITE,    s2)
    _cx_at(draw, "Authorized Signature", sig_role_y, f_sigrole, GOLD_DIM, s2)

    # ── Bottom rule  y≈1240 ───────────────────────────────────
    bot_rule = 1244
    draw.line([(m+40, bot_rule),(W-m-40, bot_rule)], fill=GOLD_DIM, width=1)
    _diamond(draw, W//2, bot_rule, 8, GOLD_DIM)

    # ── Decorative ribbon / pattern band  y≈1260–1360 ─────────
    band_y = 1264
    band_h = 96
    # Subtle dark band
    draw.rectangle([m+20, band_y, W-m-20, band_y+band_h], fill=(10,22,44))
    draw.rectangle([m+20, band_y, W-m-20, band_y+band_h], outline=GOLD_DIM, width=1)
    # Repeating diamond pattern inside band
    import math
    step = 80
    for bx in range(m+60, W-m-40, step):
        _diamond(draw, bx, band_y + band_h//2, 8, GOLD_DIM)
        draw.line([(bx+10, band_y+band_h//2),(bx+step-10, band_y+band_h//2)],
                  fill=GOLD_DIM, width=1)

    # ── Achievement text in band ──────────────────────────────
    band_text = f"  ·  SkillVerse Certified Achievement  ·  Certificate of Excellence  ·  Verified & Authenticated  ·  "
    bt_w = int(_tw(draw, band_text, f_tiny))
    # Centre it
    bx0 = (W - bt_w) // 2
    draw.text((bx0, band_y + 32), band_text, font=f_tiny, fill=GOLD_DIM)

    # ── QR + hash row  y≈1400 ────────────────────────────────
    qr_y   = 1400
    qr_x   = W//2 - QR//2       # centred horizontally
    pad    = 10
    # White pad behind QR
    draw.rectangle([qr_x-pad, qr_y-pad, qr_x+QR+pad, qr_y+QR+pad], fill=WHITE)
    img.paste(qr_img, (qr_x, qr_y))

    # "Scan to verify" above QR
    _cx(draw, "— Scan QR Code to Verify Authenticity —", qr_y - 44, f_label, GOLD_DIM)

    # Hash below QR
    hash_y = qr_y + QR + pad + 20
    _cx(draw, f"Verification Hash: {cert_hash[:48]}...", hash_y, f_tiny, GOLD_DIM)

    # Bottom border gap fills to H-m naturally
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