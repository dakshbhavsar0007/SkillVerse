"""
Certificate Generator for SkillVerse - Premium Design v3
Perfectly balanced layout, no empty spaces.
"""

import os
import uuid
import math
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4

BASE_DIR     = os.path.abspath(os.path.dirname(__file__))
CERTS_FOLDER = os.path.join(BASE_DIR, 'static', 'certificates')
FONTS_DIR    = os.path.join(BASE_DIR, 'static', 'fonts')

os.makedirs(CERTS_FOLDER, exist_ok=True)
os.makedirs(FONTS_DIR,    exist_ok=True)

W, H = 1754, 1240

NAVY       = (8,  18,  55)
NAVY2      = (16, 32,  85)
GOLD       = (200, 160, 40)
GOLD_LIGHT = (255, 220, 90)
GOLD_DIM   = (130, 100, 20)
WHITE      = (255, 255, 255)
SILVER     = (185, 192, 215)


def _font(name, size):
    for path in [
        os.path.join(FONTS_DIR, name),
        f'/usr/share/fonts/truetype/dejavu/{name}',
        f'/usr/share/fonts/truetype/liberation/{name}',
    ]:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def _tw(draw, text, font):
    try:
        b = draw.textbbox((0, 0), text, font=font)
        return b[2] - b[0]
    except AttributeError:
        w, _ = draw.textsize(text, font=font)
        return w


def _cx(draw, text, y, font, color):
    x = (W - _tw(draw, text, font)) // 2
    draw.text((x, y), text, font=font, fill=color)


def _cx_at(draw, text, y, font, color, center_x):
    tw = _tw(draw, text, font)
    draw.text((center_x - tw // 2, y), text, font=font, fill=color)


def _star(draw, cx, cy, r, fill):
    pts = []
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        radius = r if i % 2 == 0 else r * 0.42
        pts.append((cx + radius * math.cos(angle),
                    cy + radius * math.sin(angle)))
    draw.polygon(pts, fill=fill)


def _divider(draw, y):
    pad = 150
    draw.line([(pad, y), (W//2 - 20, y)], fill=GOLD_DIM, width=1)
    draw.line([(W//2 + 20, y), (W - pad, y)], fill=GOLD_DIM, width=1)
    draw.polygon([(W//2, y-8), (W//2+8, y), (W//2, y+8), (W//2-8, y)], fill=GOLD)


def _corner(draw, cx, cy):
    for r, w in [(46, 2), (35, 1), (22, 1)]:
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=GOLD, width=w)
    draw.ellipse([cx-7, cy-7, cx+7, cy+7], fill=GOLD)
    for dx, dy in [(0,-54),(0,54),(-54,0),(54,0)]:
        draw.ellipse([cx+dx-3, cy+dy-3, cx+dx+3, cy+dy+3], fill=GOLD_DIM)


def _squiggle(draw, cx, cy, color):
    pts = [(cx - 80 + i*4, cy + int(7 * math.sin(i * 0.65))) for i in range(41)]
    draw.line(pts, fill=color, width=2)


def _draw_certificate(student_name, skill_name, provider_name,
                       order_id, cert_id, completion_date):

    img  = Image.new('RGB', (W, H), NAVY)
    draw = ImageDraw.Draw(img)

    # Gradient background
    for i in range(H):
        t = abs(i / H - 0.5) * 2
        r = int(NAVY[0] * (1-t*0.3) + NAVY2[0] * t * 0.3)
        g = int(NAVY[1] * (1-t*0.3) + NAVY2[1] * t * 0.3)
        b = int(NAVY[2] + (NAVY2[2]-NAVY[2]) * t * 0.4)
        draw.line([(0, i), (W, i)], fill=(r, g, b))

    # Triple border
    M = 22
    draw.rectangle([M,    M,    W-M,    H-M],    outline=GOLD,     width=3)
    draw.rectangle([M+8,  M+8,  W-M-8,  H-M-8],  outline=GOLD_DIM, width=1)
    draw.rectangle([M+15, M+15, W-M-15, H-M-15], outline=GOLD,     width=1)

    # Corner ornaments
    _corner(draw, 72, 72)
    _corner(draw, W-72, 72)
    _corner(draw, 72, H-72)
    _corner(draw, W-72, H-72)

    # Top accent bar
    draw.rectangle([M+18, 46, W-M-18, 52], fill=GOLD)
    # Bottom accent bar
    draw.rectangle([M+18, H-52, W-M-18, H-46], fill=GOLD)

    # Fonts
    f_brand  = _font('DejaVuSans-Bold.ttf', 28)
    f_title  = _font('DejaVuSans-Bold.ttf', 68)
    f_sub    = _font('DejaVuSans.ttf',      27)
    f_name   = _font('DejaVuSans-Bold.ttf', 90)
    f_skill  = _font('DejaVuSans-Bold.ttf', 50)
    f_prov   = _font('DejaVuSans-Bold.ttf', 36)
    f_small  = _font('DejaVuSans.ttf',      20)
    f_bold24 = _font('DejaVuSans-Bold.ttf', 25)
    f_bold20 = _font('DejaVuSans-Bold.ttf', 22)

    # ── ROW 1: Brand (y=62) ───────────────────────────────────────────────
    _cx(draw, 'S  K  I  L  L  V  E  R  S  E', 62, f_brand, GOLD_LIGHT)

    # Stars flanking
    _star(draw, W//2 - 390, 100, 16, GOLD)
    _star(draw, W//2 + 374, 100, 16, GOLD)

    # ── ROW 2: Title (y=95) ───────────────────────────────────────────────
    _cx(draw, 'CERTIFICATE OF COMPLETION', 95, f_title, WHITE)

    # Underline title
    tw = _tw(draw, 'CERTIFICATE OF COMPLETION', f_title)
    lx = (W - tw) // 2
    draw.line([(lx, 172), (lx+tw, 172)], fill=GOLD, width=2)

    # ── ROW 3: Subtitle (y=185) ───────────────────────────────────────────
    _cx(draw, 'This is to proudly certify that', 185, f_sub, SILVER)

    # ── DIVIDER (y=235) ───────────────────────────────────────────────────
    _divider(draw, 238)

    # ── ROW 4: Student Name (y=252) ───────────────────────────────────────
    # Shadow
    for ox, oy in [(-2,2),(2,2),(0,3)]:
        nx = (W - _tw(draw, student_name, f_name)) // 2
        draw.text((nx+ox, 252+oy), student_name, font=f_name, fill=GOLD_DIM)
    _cx(draw, student_name, 252, f_name, GOLD_LIGHT)

    # Dot underline
    nw = _tw(draw, student_name, f_name)
    nx = (W - nw) // 2
    draw.line([(nx, 350), (nx+nw, 350)], fill=GOLD, width=2)
    for dot_x in range(nx, nx+nw+1, 14):
        draw.ellipse([dot_x-2, 356, dot_x+2, 360], fill=GOLD_DIM)

    # ── DIVIDER (y=388) ───────────────────────────────────────────────────
    _divider(draw, 390)

    # ── ROW 5: "has successfully completed" (y=402) ───────────────────────
    _cx(draw, 'has successfully completed the course', 402, f_sub, SILVER)

    # ── ROW 6: Skill name box (y=440) ─────────────────────────────────────
    sw = _tw(draw, skill_name, f_skill)
    sx = (W - sw) // 2
    pad = 28
    draw.rounded_rectangle([sx-pad, 440, sx+sw+pad, 508],
                            radius=12, fill=(20,35,95), outline=GOLD, width=2)
    _cx(draw, skill_name, 448, f_skill, WHITE)
    mid_y = 474
    _star(draw, sx - pad - 28, mid_y, 13, GOLD)
    _star(draw, sx + sw + pad + 28, mid_y, 13, GOLD)

    # ── DIVIDER (y=528) ───────────────────────────────────────────────────
    _divider(draw, 530)

    # ── ROW 7: Provider (y=542) ───────────────────────────────────────────
    _cx(draw, 'Under the expert guidance of', 548, f_sub, SILVER)
    _cx(draw, provider_name, 584, f_prov, GOLD_LIGHT)

    # ── DIVIDER (y=632) ───────────────────────────────────────────────────
    _divider(draw, 634)

    # ── ROW 8: Info boxes + Seal (y=650) ──────────────────────────────────
    iy = 670

    # LEFT: Date box
    col1 = 195
    draw.rounded_rectangle([col1-12, iy-6, col1+250, iy+80],
                            radius=8, fill=(16,28,82), outline=GOLD_DIM, width=1)
    draw.text((col1, iy),    'DATE OF ISSUE',    font=f_small,  fill=SILVER)
    draw.text((col1, iy+24), completion_date,    font=f_bold24, fill=WHITE)
    draw.text((col1, iy+54), 'SkillVerse Platform', font=f_small, fill=GOLD_DIM)

    # CENTER: Gold seal
    sc_x, sc_y = W//2, iy + 42
    for r, col in [(72, (50,42,8)), (60, (80,65,12)), (48, GOLD)]:
        draw.ellipse([sc_x-r, sc_y-r, sc_x+r, sc_y+r], outline=col, width=2)
    draw.ellipse([sc_x-40, sc_y-40, sc_x+40, sc_y+40], fill=GOLD)
    draw.ellipse([sc_x-30, sc_y-30, sc_x+30, sc_y+30], fill=GOLD_DIM)
    _star(draw, sc_x, sc_y, 24, GOLD_LIGHT)
    for deg in range(0, 360, 25):
        a = math.radians(deg)
        draw.line([(sc_x+52*math.cos(a), sc_y+52*math.sin(a)),
                   (sc_x+65*math.cos(a), sc_y+65*math.sin(a))],
                  fill=GOLD_DIM, width=1)

    # RIGHT: Cert ID box
    cw = max(_tw(draw, 'CERTIFICATE ID', f_small), _tw(draw, cert_id, f_bold24))
    col3 = W - 195 - cw
    draw.rounded_rectangle([col3-12, iy-6, col3+cw+12, iy+80],
                            radius=8, fill=(16,28,82), outline=GOLD_DIM, width=1)
    draw.text((col3, iy),    'CERTIFICATE ID', font=f_small,  fill=SILVER)
    draw.text((col3, iy+24), cert_id,          font=f_bold24, fill=GOLD_LIGHT)
    draw.text((col3, iy+54), f'Order #{order_id}', font=f_small, fill=GOLD_DIM)

    # ── DIVIDER (y=752) ───────────────────────────────────────────────────
    _divider(draw, 780)

    # ── ROW 9: Signatures (y=770) ─────────────────────────────────────────
    sy = 800
    s1_cx = W // 4
    s2_cx = 3 * W // 4

    for scx in [s1_cx, s2_cx]:
        draw.line([(scx-120, sy+44), (scx+120, sy+44)], fill=GOLD_DIM, width=1)

    _squiggle(draw, s1_cx, sy+28, GOLD_LIGHT)
    _squiggle(draw, s2_cx, sy+28, GOLD_LIGHT)

    _cx_at(draw, provider_name,       sy+52, f_bold20, SILVER, s1_cx)
    _cx_at(draw, 'INSTRUCTOR / PROVIDER', sy+76, f_small, GOLD_DIM, s1_cx)

    _cx_at(draw, 'SkillVerse',            sy+52, f_bold20, SILVER, s2_cx)
    _cx_at(draw, 'AUTHORIZED SIGNATURE',  sy+76, f_small, GOLD_DIM, s2_cx)

    # ── DIVIDER (y=868) ───────────────────────────────────────────────────
    _divider(draw, 910)

    # ── ROW 10: Achievement badges row (y=886) ────────────────────────────
    badge_y = 960
    badges = ['* Verified Completion', '* SkillVerse Certified', '* Tamper-Proof Record']
    bx = W // 4 - 80
    bw = W // 3 - 20
    for i, badge in enumerate(badges):
        bx_start = 130 + i * (W - 260) // 3
        draw.rounded_rectangle([bx_start, badge_y-4, bx_start + (W-260)//3 - 20, badge_y+36],
                                radius=8, fill=(16,28,78), outline=GOLD_DIM, width=1)
        _cx_at(draw, badge, badge_y+4, f_small, SILVER, bx_start + ((W-260)//3 - 20)//2)

    # ── ROW 11: Verify URL (y=948) ────────────────────────────────────────
    _cx(draw, f'Verify at: skillverse-oh9z.onrender.com/verify/{cert_id}',
        1120, f_small, SILVER)

    return img


def generate_certificate(student_name, skill_name, provider_name,
                         order_id, cert_id=None, completion_date=None,
                         template_path=None):
    if not cert_id:
        cert_id = f"CERT-{uuid.uuid4().hex[:6].upper()}"
    if not completion_date:
        completion_date = datetime.now().strftime("%B %d, %Y")

    img = _draw_certificate(student_name, skill_name, provider_name,
                            order_id, cert_id, completion_date)

    tmp_png      = os.path.join(CERTS_FOLDER, f"_tmp_{cert_id}.png")
    pdf_filename = f"certificate_order{order_id}_{cert_id}.pdf"
    pdf_path     = os.path.join(CERTS_FOLDER, pdf_filename)

    img.save(tmp_png, format='PNG', dpi=(150, 150))

    pw, ph = landscape(A4)
    c = canvas.Canvas(pdf_path, pagesize=landscape(A4))
    c.setTitle(f"SkillVerse Certificate - {student_name}")
    c.setAuthor("SkillVerse Platform")
    c.setSubject(f"Certificate of Completion: {skill_name}")
    c.drawImage(tmp_png, 0, 0, width=pw, height=ph,
                preserveAspectRatio=True, anchor='c')
    c.save()

    try:
        os.remove(tmp_png)
    except OSError:
        pass

    return pdf_path


def generate_cert_id():
    return f"CERT-{uuid.uuid4().hex[:6].upper()}"


if __name__ == '__main__':
    img = _draw_certificate('Daksh Bhavsar', 'Tailwind CSS', 'Daksh Bhavsar',
                            16, 'CERT-3893EF', 'February 18, 2026')
    img.save('/home/claude/preview_final.png')
    print("Done!")