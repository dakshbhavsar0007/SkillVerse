"""
Certificate Routes for SkillVerse

Add these routes to your routes.py (inside user_bp or service_bp blueprint).

Two endpoints:
  1. POST /order/<id>/complete  — marks order complete, generates certificate
  2. GET  /certificate/<cert_id>/download — serves the PDF to the user
"""

import os
from flask import send_file, abort, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models import db, Order, Certificate, User
from certificate_generator import generate_certificate, generate_cert_id


# ─────────────────────────────────────────────────────────────────────────────
# 1.  Mark order complete  +  issue certificate
# ─────────────────────────────────────────────────────────────────────────────

@user_bp.route('/order/<int:order_id>/complete', methods=['POST'])
@login_required
def complete_order(order_id):
    """
    Called when the PROVIDER clicks 'Mark as Complete'.

    - Updates order status to 'completed'
    - Generates a PDF certificate for the buyer
    - Saves certificate record to DB
    - (Optional) sends email to buyer with download link
    """
    order = Order.query.get_or_404(order_id)

    # Only the seller (provider) can mark complete
    if current_user.id != order.seller_id:
        abort(403)

    if order.status == 'completed':
        flash('Order is already marked as complete.', 'info')
        return redirect(url_for('user.order_detail', order_id=order_id))

    # ── 1. Update order status ────────────────────────────────────────────
    order.update_status('completed')
    db.session.commit()

    # ── 2. Generate certificate ───────────────────────────────────────────
    try:
        student  = User.query.get(order.buyer_id)
        provider = User.query.get(order.seller_id)
        service  = order.service

        cert_id  = generate_cert_id()

        pdf_path = generate_certificate(
            student_name    = student.full_name or student.username,
            skill_name      = service.title,
            provider_name   = provider.full_name or provider.username,
            order_id        = order.id,
            cert_id         = cert_id,
        )

        # ── 3. Save cert record to DB ─────────────────────────────────────
        cert = Certificate(
            cert_id      = cert_id,
            order_id     = order.id,
            student_id   = order.buyer_id,
            provider_id  = order.seller_id,
            skill_name   = service.title,
            pdf_filename = os.path.basename(pdf_path),
        )
        db.session.add(cert)
        db.session.commit()

        # ── 4. Notify the buyer ───────────────────────────────────────────
        from models import Notification
        notification = Notification(
            user_id = order.buyer_id,
            title   = '🎓 Your Certificate is Ready!',
            message = (f'Congratulations! You have completed "{service.title}". '
                       f'Your certificate ({cert_id}) is ready to download.'),
            link    = url_for('user.download_certificate', cert_id=cert_id),
        )
        db.session.add(notification)
        db.session.commit()

        # ── 5. (Optional) send email ──────────────────────────────────────
        try:
            _send_certificate_email(student, cert, pdf_path)
        except Exception as mail_err:
            print(f"[Certificate] Email failed (non-fatal): {mail_err}")

        flash(f'Order marked complete! Certificate {cert_id} issued to {student.username}.', 'success')

    except Exception as e:
        print(f"[Certificate] Generation failed: {e}")
        flash('Order marked complete, but certificate generation failed. '
              'Please contact support.', 'warning')

    return redirect(url_for('user.order_detail', order_id=order_id))


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Download certificate PDF
# ─────────────────────────────────────────────────────────────────────────────

@user_bp.route('/certificate/<cert_id>/download')
@login_required
def download_certificate(cert_id):
    """
    Serves the certificate PDF.
    Only the student (buyer) or the provider or admin can download it.
    """
    cert = Certificate.query.filter_by(cert_id=cert_id).first_or_404()

    # Access control
    allowed = (
        current_user.id == cert.student_id or
        current_user.id == cert.provider_id or
        current_user.is_admin()
    )
    if not allowed:
        abort(403)

    BASE_DIR   = os.path.abspath(os.path.dirname(__file__))
    certs_dir  = os.path.join(BASE_DIR, 'static', 'certificates')
    pdf_path   = os.path.join(certs_dir, cert.pdf_filename)

    if not os.path.exists(pdf_path):
        abort(404)

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"SkillVerse_Certificate_{cert.cert_id}.pdf",
        mimetype='application/pdf'
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3.  API endpoint — check if a certificate exists for an order
# ─────────────────────────────────────────────────────────────────────────────

@user_bp.route('/api/certificate/order/<int:order_id>')
@login_required
def get_order_certificate(order_id):
    """Returns certificate info for an order as JSON (for frontend use)."""
    cert = Certificate.query.filter_by(order_id=order_id).first()
    if not cert:
        return jsonify({'exists': False})
    return jsonify({
        'exists'      : True,
        'cert_id'     : cert.cert_id,
        'issued_at'   : cert.issued_at.strftime('%B %d, %Y'),
        'download_url': url_for('user.download_certificate', cert_id=cert.cert_id),
    })


# ─────────────────────────────────────────────────────────────────────────────
# Helper: send certificate email via SendGrid
# ─────────────────────────────────────────────────────────────────────────────

def _send_certificate_email(student, cert, pdf_path):
    """Send certificate download link to the student via email."""
    from flask import current_app
    from flask_mail import Mail, Message as MailMessage

    mail = Mail(current_app)
    download_url = url_for('user.download_certificate',
                           cert_id=cert.cert_id, _external=True)

    msg = MailMessage(
        subject  = f'🎓 Your SkillVerse Certificate - {cert.skill_name}',
        sender   = current_app.config['MAIL_DEFAULT_SENDER'],
        recipients = [student.email],
        html     = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto">
            <h2 style="color:#1a1a4e">Congratulations, {student.full_name or student.username}! 🎉</h2>
            <p>You have successfully completed <strong>{cert.skill_name}</strong>.</p>
            <p>Your Certificate ID is: <strong>{cert.cert_id}</strong></p>
            <p style="margin:30px 0">
                <a href="{download_url}"
                   style="background:#B8860B;color:white;padding:14px 28px;
                          border-radius:6px;text-decoration:none;font-weight:bold">
                    Download Your Certificate
                </a>
            </p>
            <p style="color:#666;font-size:12px">
                This certificate was issued on {cert.issued_at.strftime('%B %d, %Y')} 
                by SkillVerse Platform.
            </p>
        </div>
        """
    )
    mail.send(msg)
