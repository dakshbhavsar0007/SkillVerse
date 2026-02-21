"""
Email Utility Module for SkillVerse

Sends transactional emails via SendGrid HTTP API (port 443, always open on Render).

Anti-spam measures implemented:
- Named sender: "SkillVerse Team <noreply@...>" instead of bare address
- Plain-text alternative for every email (HTML-only emails score badly with filters)
- List-Unsubscribe header so Gmail/Outlook don't flag bulk-style messages
- Descriptive subject lines (no ALL CAPS, no spam trigger words)
- All links use the production Render URL, not localhost
"""

import os
import re
from threading import Thread

import sendgrid
from sendgrid.helpers.mail import Mail, Content, MimeType
from flask import render_template, current_app

# ── Production base URL (used for all external links in emails) ───────────────
APP_BASE_URL = "https://skillverse-oh9z.onrender.com"


def _base_url():
    """Return the production base URL, falling back to env var if set."""
    return os.environ.get("APP_BASE_URL", APP_BASE_URL).rstrip("/")


def _get_sg_client():
    """Return a configured SendGrid client."""
    api_key = os.environ.get("SENDGRID_API_KEY") or current_app.config.get("SENDGRID_API_KEY")
    if not api_key:
        raise ValueError("SENDGRID_API_KEY environment variable is not set")
    return sendgrid.SendGridAPIClient(api_key=api_key)


def _get_named_sender():
    """
    Return sender as 'SkillVerse Team <address>'.
    A named sender dramatically reduces spam-filter scores.
    """
    raw = (
        os.environ.get("MAIL_DEFAULT_SENDER")
        or current_app.config.get("MAIL_DEFAULT_SENDER", "noreply@skillverse.com")
    )
    # If already a tuple/dict keep it; if format "Name <email>" keep it too.
    if "<" in str(raw):
        return raw
    return ("SkillVerse Team", raw)


def _html_to_text(html: str) -> str:
    """Very simple HTML → plain-text strip for the text/plain alternative."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&amp;",  "&",  text)
    text = re.sub(r"&lt;",   "<",  text)
    text = re.sub(r"&gt;",   ">",  text)
    text = re.sub(r"&nbsp;", " ",  text)
    text = re.sub(r"\s{2,}", " ",  text)
    return text.strip()


def send_async_email(app, subject, recipient, html_content, sender):
    """
    Send email in a background thread via SendGrid HTTP API.
    Includes plain-text alternative and anti-spam headers.
    """
    with app.app_context():
        try:
            sg = _get_sg_client()

            plain_text = _html_to_text(html_content)

            # Build message with both HTML and plain-text parts
            message = Mail()
            message.from_email = sender
            message.to = recipient
            message.subject = subject

            # text/plain first (recommended order for deliverability)
            message.content = [
                Content(MimeType.text, plain_text),
                Content(MimeType.html, html_content),
            ]

            # Anti-spam: List-Unsubscribe header
            unsubscribe_url = f"{_base_url()}/unsubscribe?email={recipient}"
            message.header = [
                sendgrid.helpers.mail.Header(
                    "List-Unsubscribe",
                    f"<{unsubscribe_url}>"
                ),
                sendgrid.helpers.mail.Header(
                    "List-Unsubscribe-Post",
                    "List-Unsubscribe=One-Click"
                ),
                sendgrid.helpers.mail.Header(
                    "X-Mailer",
                    "SkillVerse Mailer 1.0"
                ),
            ]

            response = sg.send(message)
            if response.status_code not in (200, 202):
                app.logger.error(
                    f"SendGrid {response.status_code}: {response.body}"
                )
            else:
                app.logger.info(f"Email sent to {recipient}: {subject}")
        except Exception as e:
            app.logger.error(f"Failed to send email via SendGrid: {e}")


def send_email(subject, recipient, template, **kwargs):
    """
    Render an HTML email template and queue it for delivery.

    All templates receive `base_url` in their context so they can build
    absolute links without relying on url_for(_external=True) which generates
    http://localhost on Render.

    Args:
        subject   : Email subject
        recipient : Recipient address
        template  : Template name (without .html), inside templates/emails/
        **kwargs  : Additional Jinja2 context variables
    """
    try:
        app = current_app._get_current_object()

        # Inject base_url so every template can build correct production links
        kwargs.setdefault("base_url", _base_url())

        html_content = render_template(f"emails/{template}.html", **kwargs)
        sender = _get_named_sender()

        Thread(
            target=send_async_email,
            args=(app, subject, recipient, html_content, sender),
            daemon=True,
        ).start()

        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        current_app.logger.error(f"Error queuing email '{subject}' to {recipient}: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Public helper functions
# ─────────────────────────────────────────────────────────────────────────────

def send_welcome_email(user):
    """Send welcome email to new user."""
    return send_email(
        subject="Welcome to SkillVerse!",
        recipient=user.email,
        template="welcome",
        user=user,
    )


def send_order_placed_emails(order):
    """Notify buyer and seller when an order is placed."""
    send_email(
        subject="Your order has been placed on SkillVerse",
        recipient=order.buyer.email,
        template="order_placed_customer",
        order=order,
        customer=order.buyer,
        provider=order.seller,
        service=order.service,
    )
    send_email(
        subject="You have a new order on SkillVerse",
        recipient=order.seller.email,
        template="order_placed_provider",
        order=order,
        customer=order.buyer,
        provider=order.seller,
        service=order.service,
    )


def send_order_accepted_emails(order):
    """Notify buyer and seller when an order is accepted."""
    send_email(
        subject="Your order has been accepted",
        recipient=order.buyer.email,
        template="order_accepted_customer",
        order=order,
        customer=order.buyer,
        provider=order.seller,
        service=order.service,
    )
    send_email(
        subject="Order accepted — let's get started!",
        recipient=order.seller.email,
        template="order_accepted_provider",
        order=order,
        customer=order.buyer,
        provider=order.seller,
        service=order.service,
    )


def send_order_completed_emails(order):
    """Notify buyer and seller when an order is completed."""
    send_email(
        subject="Your order is complete — download your certificate",
        recipient=order.buyer.email,
        template="order_completed_customer",
        order=order,
        customer=order.buyer,
        provider=order.seller,
        service=order.service,
    )
    send_email(
        subject="Order marked as complete",
        recipient=order.seller.email,
        template="order_completed_provider",
        order=order,
        customer=order.buyer,
        provider=order.seller,
        service=order.service,
    )


def send_booking_confirmation_email(booking):
    """Send booking confirmation to the student/client."""
    base = _base_url()
    start_time = booking.slot.start_time.strftime("%Y-%m-%d %H:%M UTC")
    service_title = booking.service.title if booking.service else "General Session"
    link = f"{base}/user/bookings"

    send_email(
        subject="Booking Confirmed on SkillVerse",
        recipient=booking.client.email,
        template="booking_confirmation",
        customer=booking.client,
        provider=booking.slot.provider,
        start_time=start_time,
        service_title=service_title,
        order_id=booking.order_id,
        link=link,
    )


def send_booking_rejection_email(booking):
    """Notify client that their booking was rejected."""
    base = _base_url()
    start_time = booking.slot.start_time.strftime("%Y-%m-%d %H:%M UTC")
    service_title = booking.service.title if booking.service else "General Session"

    if booking.order_id:
        link = f"{base}/user/order/{booking.order_id}"
    elif booking.service_id:
        link = f"{base}/service/{booking.service_id}"
    else:
        link = f"{base}/service/browse"

    send_email(
        subject="Your booking request was not accepted",
        recipient=booking.client.email,
        template="booking_rejection",
        customer=booking.client,
        provider=booking.slot.provider,
        start_time=start_time,
        service_title=service_title,
        link=link,
    )


def send_password_reset_email(user, token):
    """Send password reset link to user."""
    base = _base_url()
    link = f"{base}/auth/reset-password/{token}"

    return send_email(
        subject="Reset your SkillVerse password",
        recipient=user.email,
        template="reset_password",
        user=user,
        link=link,
    )