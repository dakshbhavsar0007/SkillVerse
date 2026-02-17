"""
Email Utility Module for SkillVerse

This module handles all email sending functionality using SendGrid's HTTP Web API.
Switched from Flask-Mail SMTP to SendGrid HTTP API to fix Render.com port 587 blocking.

WHY THIS CHANGE:
- Render.com free/starter tier blocks outbound SMTP (port 587/465) → [Errno 110] Connection timed out
- SendGrid HTTP API uses port 443 (HTTPS) which is always open on Render
- More reliable delivery and better error reporting
"""

import os
import sendgrid
from sendgrid.helpers.mail import Mail, To
from flask import render_template, current_app
from threading import Thread


def _get_sg_client():
    """Get a configured SendGrid client using SENDGRID_API_KEY env var"""
    api_key = os.environ.get('SENDGRID_API_KEY') or current_app.config.get('SENDGRID_API_KEY')
    if not api_key:
        raise ValueError("SENDGRID_API_KEY environment variable is not set")
    return sendgrid.SendGridAPIClient(api_key=api_key)


def _get_default_sender():
    """Get the configured default sender email"""
    sender = os.environ.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@skillverse.com')
    # Flask-Mail format: "Name <email@example.com>" → extract just email for SendGrid
    # SendGrid accepts both plain "email@example.com" and tuple ("Name", "email")
    return sender


def send_async_email(app, subject, recipient, html_content, sender):
    """
    Send email in a background thread via SendGrid HTTP API.

    Args:
        app: Flask application instance
        subject (str): Email subject
        recipient (str): Recipient email address
        html_content (str): Rendered HTML body
        sender (str): Sender email/name string
    """
    with app.app_context():
        try:
            sg = _get_sg_client()
            message = Mail(
                from_email=sender,
                to_emails=recipient,
                subject=subject,
                html_content=html_content
            )
            response = sg.send(message)
            if response.status_code not in (200, 202):
                app.logger.error(
                    f"SendGrid returned unexpected status {response.status_code}: {response.body}"
                )
        except Exception as e:
            app.logger.error(f"Failed to send email via SendGrid HTTP API: {str(e)}")


def send_email(subject, recipient, template, **kwargs):
    """
    Send HTML email using template via SendGrid HTTP API.

    Args:
        subject (str): Email subject line
        recipient (str): Recipient email address
        template (str): Template file name (without .html extension)
        **kwargs: Additional context variables for the template

    Returns:
        bool: True if email queued successfully, False otherwise
    """
    try:
        app = current_app._get_current_object()

        # Render the HTML template
        html_content = render_template(f'emails/{template}.html', **kwargs)
        sender = _get_default_sender()

        # Send asynchronously to avoid blocking the request
        Thread(
            target=send_async_email,
            args=(app, subject, recipient, html_content, sender)
        ).start()

        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        current_app.logger.error(f"Error queuing email '{subject}' to {recipient}: {str(e)}")
        return False


# ─── All public helper functions below are unchanged ─────────────────────────

def send_welcome_email(user):
    """Send welcome email to new user"""
    return send_email(
        subject='Welcome to SkillVerse',
        recipient=user.email,
        template='welcome',
        user=user
    )


def send_order_placed_emails(order):
    """Send order placement confirmation emails to both customer and provider"""
    send_email(
        subject='Your order has been sent successfully',
        recipient=order.buyer.email,
        template='order_placed_customer',
        order=order,
        customer=order.buyer,
        provider=order.seller,
        service=order.service
    )
    send_email(
        subject='New order received',
        recipient=order.seller.email,
        template='order_placed_provider',
        order=order,
        customer=order.buyer,
        provider=order.seller,
        service=order.service
    )


def send_order_accepted_emails(order):
    """Send order acceptance confirmation emails to both customer and provider"""
    send_email(
        subject='Your order has been accepted',
        recipient=order.buyer.email,
        template='order_accepted_customer',
        order=order,
        customer=order.buyer,
        provider=order.seller,
        service=order.service
    )
    send_email(
        subject='Order accepted successfully',
        recipient=order.seller.email,
        template='order_accepted_provider',
        order=order,
        customer=order.buyer,
        provider=order.seller,
        service=order.service
    )


def send_order_completed_emails(order):
    """Send order completion emails to both customer and provider"""
    send_email(
        subject='Your order has been completed',
        recipient=order.buyer.email,
        template='order_completed_customer',
        order=order,
        customer=order.buyer,
        provider=order.seller,
        service=order.service
    )
    send_email(
        subject='Order marked as completed',
        recipient=order.seller.email,
        template='order_completed_provider',
        order=order,
        customer=order.buyer,
        provider=order.seller,
        service=order.service
    )


def send_booking_confirmation_email(booking):
    """Send booking confirmation email to customer"""
    from flask import url_for

    start_time = booking.slot.start_time.strftime('%Y-%m-%d %H:%M UTC')
    service_title = booking.service.title if booking.service else 'General Session'
    link = url_for('user.bookings_list', _external=True)

    send_email(
        subject='Booking Confirmed!',
        recipient=booking.client.email,
        template='booking_confirmation',
        customer=booking.client,
        provider=booking.slot.provider,
        start_time=start_time,
        service_title=service_title,
        order_id=booking.order_id,
        link=link
    )


def send_booking_rejection_email(booking):
    """Send booking rejection email to customer"""
    from flask import url_for

    start_time = booking.slot.start_time.strftime('%Y-%m-%d %H:%M UTC')
    service_title = booking.service.title if booking.service else 'General Session'

    if booking.order_id:
        link = url_for('user.order_detail', order_id=booking.order_id, _external=True)
    elif booking.service_id:
        link = url_for('service.detail', service_id=booking.service_id, _external=True)
    else:
        link = url_for('service.browse', _external=True)

    send_email(
        subject='Action Required: Booking Request Rejected',
        recipient=booking.client.email,
        template='booking_rejection',
        customer=booking.client,
        provider=booking.slot.provider,
        start_time=start_time,
        service_title=service_title,
        link=link
    )


def send_password_reset_email(user, token):
    """Send password reset email to user"""
    from flask import url_for

    link = url_for('auth.reset_password_token', token=token, _external=True)

    return send_email(
        subject='Reset Your Password - SkillVerse',
        recipient=user.email,
        template='reset_password',
        user=user,
        link=link
    )