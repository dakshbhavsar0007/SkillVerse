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

# ── Certificate Drawer ──────────────────────────────────────────
def draw_certificate(student_name, skill_name,
                     provider_name="SkillVerse",
                     order_id="SV-ORDER-001",
                     cert_id="CERT-XXXX",
                     completion_date=None):

    if completion_date is None:
        completion_date = datetime.now().strftime("%d %B %Y")

    # ── Generate Hash ──────────────────────────────────────────
    cert_hash = generate_hash(student_name, skill_name, cert_id, order_id)

    verify_url = f"https://skillverse.in/verify?cert_id={cert_id}&hash={cert_hash}"

    # ── QR Code ────────────────────────────────────────────────
    qr = qrcode.make(verify_url).resize((260, 260))

    img  = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(img)

    # ── Fonts ───────────────────────────────────────────────────
    f_brand     = _font("Montserrat-SemiBold.ttf", 28)
    f_title     = _font("PlayfairDisplay-Bold.ttf", 68)
    f_sub       = _font("CormorantGaramond-Regular.ttf", 30)
    f_name      = _font("PlayfairDisplay-Bold.ttf", 90)
    f_skill     = _font("Montserrat-SemiBold.ttf", 50)
    f_prov      = _font("Montserrat-SemiBold.ttf", 36)
    f_small     = _font("Montserrat-Regular.ttf", 20)
    f_bold24    = _font("Montserrat-SemiBold.ttf", 25)
    f_bold20    = _font("Montserrat-SemiBold.ttf", 22)
    f_signature = _font("GreatVibes-Regular.ttf", 46)

    # ── Border ──────────────────────────────────────────────────
    m = 70
    draw.rectangle([m, m, W-m, H-m], outline=GOLD, width=6)
    draw.rectangle([m+18, m+18, W-m-18, H-m-18], outline=GOLD_DIM, width=2)

    # ── Header ──────────────────────────────────────────────────
    _cx(draw, provider_name.upper(), 140, f_brand, GOLD)
    _cx(draw, "CERTIFICATE OF COMPLETION", 210, f_title, WHITE)
    _cx(draw, "This certificate is proudly presented to", 310, f_sub, SILVER)

    # ── Name ────────────────────────────────────────────────────
    _cx(draw, student_name, 380, f_name, GOLD_LIGHT)
    draw.line([(W//2-420, 490), (W//2+420, 490)], fill=GOLD_DIM, width=2)

    # ── Course ──────────────────────────────────────────────────
    _cx(draw, "for successfully completing", 520, f_sub, SILVER)
    _cx(draw, skill_name, 580, f_skill, GOLD)
    _cx(draw, "An online learning program by", 650, f_sub, SILVER)
    _cx(draw, provider_name, 690, f_prov, GOLD_LIGHT)

    # ── Details ────────────────────────────────────────────────
    info_y = 760
    draw.line([(W//2-500, info_y), (W//2+500, info_y)], fill=GOLD_DIM, width=1)

    _cx_at(draw, f"Order ID : {order_id}", info_y+24, f_bold24, WHITE, W//4)
    _cx_at(draw, f"Certificate ID : {cert_id}", info_y+24, f_bold24, WHITE, 3*W//4)

    _cx_at(draw, f"Date : {completion_date}", info_y+62, f_small, SILVER, W//4)
    _cx_at(draw, "Scan QR to Verify", info_y+62, f_small, SILVER, 3*W//4)

    # ── QR Placement ───────────────────────────────────────────
    img.paste(qr, (W - 360, H - 360))

    # ── Hash Print (tiny, secure) ──────────────────────────────
    draw.text((90, H - 110),
              f"Verification Hash: {cert_hash[:32]}...",
              font=f_small, fill=GOLD_DIM)

    # ── Signatures ──────────────────────────────────────────────
    sy = 860
    s1 = W // 4
    s2 = 3 * W // 4

    sig = "Daksh Bhavsar"
    sig_w = _tw(draw, sig, f_signature)
    sig_x = s1 - sig_w // 2

    for ox, oy in [(-1,1),(1,1),(0,2)]:
        draw.text((sig_x+ox, sy+18+oy), sig, font=f_signature, fill=GOLD_DIM)

    draw.text((sig_x, sy+18), sig, font=f_signature, fill=GOLD_LIGHT)

    draw.line([(s1-140, sy+58), (s1+140, sy+58)], fill=GOLD_DIM, width=1)
    _cx_at(draw, "Founder & Director", sy+64, f_bold20, SILVER, s1)
    _cx_at(draw, provider_name, sy+90, f_small, GOLD_DIM, s1)

    draw.line([(s2-140, sy+52), (s2+140, sy+52)], fill=GOLD_DIM, width=1)
    _squiggle(draw, s2, sy+34, GOLD_LIGHT)
    _cx_at(draw, provider_name, sy+64, f_bold20, SILVER, s2)
    _cx_at(draw, "AUTHORIZED SIGNATURE", sy+90, f_small, GOLD_DIM, s2)

    return img


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
