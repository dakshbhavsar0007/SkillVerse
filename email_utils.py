"""
Email Utility Module for SkillVerse

Sends transactional emails via SendGrid HTTP API (port 443, always open on Render).

Anti-spam measures implemented:
- Named sender: "SkillVerse Team <noreply@...>" instead of bare address
- Reply-To set to a monitored address so replies don't bounce
- Plain-text alternative for every email (HTML-only emails score badly with filters)
- List-Unsubscribe header ONLY on marketing/notification emails (not on transactional)
  (Adding it to password resets / order confirmations is a spam signal)
- Descriptive subject lines (no ALL CAPS, no spam trigger words)
- All links use the production Render URL, not localhost
- Improved plain-text stripping: preserves line breaks and collapses whitespace cleanly

Checklist for good deliverability (things you must do outside this code):
1. SPF  — add a TXT record: v=spf1 include:sendgrid.net ~all
2. DKIM — enable & verify your domain in SendGrid dashboard
3. DMARC — add: v=DMARC1; p=none; rua=mailto:dmarc@yourdomain.com
4. Verify your sender domain in SendGrid (not just the email address)
5. Keep spam complaint rate below 0.1% (monitor in SendGrid dashboard)
"""

import os
import re
from threading import Thread

import sendgrid
from sendgrid.helpers.mail import Mail, Content, MimeType, ReplyTo
from flask import render_template, current_app

# ── Production base URL (used for all external links in emails) ───────────────
APP_BASE_URL = "https://skillverse-oh9z.onrender.com"

# ── Email types: only these get a List-Unsubscribe header ────────────────────
# Transactional emails (order confirmations, password resets, booking alerts)
# must NOT have List-Unsubscribe — it confuses spam filters.
# Only add it to digest / newsletter style emails.
MARKETING_TEMPLATES = {"welcome"}  # extend if you add newsletters


def _base_url():
    """Return the production base URL, falling back to env var if set."""
    return os.environ.get("APP_BASE_URL", APP_BASE_URL).rstrip("/")


def _get_reply_to():
    """
    Return a monitored Reply-To address.
    noreply senders with no Reply-To are a spam signal because ISPs can't
    verify there's a human behind the domain.  Point to a real inbox.
    """
    return os.environ.get("MAIL_REPLY_TO", "support@skillverse.com")


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
    """
    HTML → plain-text for the text/plain alternative.

    A well-formed plain-text part is critical: spam filters penalise emails
    where the HTML and plain-text say wildly different things, and they also
    penalise plain-text parts that are just a wall of whitespace.
    """
    # Block-level tags → newlines so paragraphs survive the strip
    text = re.sub(r"<(?:br\s*/?|/p|/div|/tr|/li|/h[1-6])>", "\n", html, flags=re.I)
    # Remove all remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Decode common HTML entities
    text = re.sub(r"&amp;",   "&",  text)
    text = re.sub(r"&lt;",    "<",  text)
    text = re.sub(r"&gt;",    ">",  text)
    text = re.sub(r"&nbsp;",  " ",  text)
    text = re.sub(r"&#39;",   "'",  text)
    text = re.sub(r"&quot;",  '"',  text)
    # Collapse runs of spaces/tabs (but keep newlines)
    text = re.sub(r"[^\S\n]+", " ", text)
    # Collapse more than two consecutive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip leading/trailing whitespace from each line
    text = "\n".join(line.strip() for line in text.splitlines())
    return text.strip()


def send_async_email(app, subject, recipient, html_content, sender, template_name=""):
    """
    Send email in a background thread via SendGrid HTTP API.
    Includes plain-text alternative, Reply-To, and conditional anti-spam headers.
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

            # Reply-To: a monitored inbox — improves sender reputation
            message.reply_to = ReplyTo(_get_reply_to(), "SkillVerse Support")

            # text/plain first (recommended order for deliverability)
            message.content = [
                Content(MimeType.text, plain_text),
                Content(MimeType.html, html_content),
            ]

            headers = [
                sendgrid.helpers.mail.Header("X-Mailer", "SkillVerse Mailer 1.0"),
            ]

            # List-Unsubscribe ONLY for marketing/welcome emails.
            # Adding it to transactional emails (order confirmations, password
            # resets) confuses ISPs and increases spam scores.
            if template_name in MARKETING_TEMPLATES:
                unsubscribe_url = f"{_base_url()}/unsubscribe?email={recipient}"
                headers += [
                    sendgrid.helpers.mail.Header(
                        "List-Unsubscribe",
                        f"<{unsubscribe_url}>"
                    ),
                    sendgrid.helpers.mail.Header(
                        "List-Unsubscribe-Post",
                        "List-Unsubscribe=One-Click"
                    ),
                ]

            message.header = headers

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
            args=(app, subject, recipient, html_content, sender, template),
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


def send_skill_rejected_email(provider, service_title, reason, service_id):
    """Notify a provider that their skill submission was rejected."""
    base = _base_url()
    resubmit_link = f"{base}/service/edit/{service_id}"

    return send_email(
        subject="Your skill submission needs a revision",
        recipient=provider.email,
        template="skill_rejected",
        provider=provider,
        service_title=service_title,
        reason=reason,
        resubmit_link=resubmit_link,
    )