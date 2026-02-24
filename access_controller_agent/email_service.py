"""
Email Service for Access Controller Agent.
Handles Gmail IMAP (reading) and SMTP (sending) operations.
Uses app password for authentication.
"""
from __future__ import annotations
import os
import logging
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from email.utils import parseaddr, formataddr
from datetime import datetime, timedelta
from typing import Any, Optional, List
import re
import html

logger = logging.getLogger(__name__)


class EmailService:
    """Gmail email service using IMAP for reading and SMTP for sending."""
    
    def __init__(self) -> None:
        # Gmail settings
        self.email_address = os.getenv("GMAIL_ADDRESS")
        self.app_password = os.getenv("GMAIL_APP_PASSWORD")
        
        # IMAP settings (for reading)
        self.imap_host = os.getenv("GMAIL_IMAP_HOST", "imap.gmail.com")
        self.imap_port = int(os.getenv("GMAIL_IMAP_PORT", "993"))
        
        # SMTP settings (for sending)
        self.smtp_host = os.getenv("GMAIL_SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("GMAIL_SMTP_PORT", "587"))
        
        # Bot identity
        self.bot_name = os.getenv("EMAIL_BOT_NAME", "AccessAssist")
        
        if not self.email_address or not self.app_password:
            logger.warning(
                "Gmail credentials missing (GMAIL_ADDRESS, GMAIL_APP_PASSWORD). "
                "Email tools will return mock responses."
            )
    
    def _decode_header_value(self, value: str) -> str:
        """Decode email header value (handles encoded subjects/names)."""
        if not value:
            return ""
        decoded_parts = decode_header(value)
        result = []
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                result.append(part.decode(encoding or 'utf-8', errors='replace'))
            else:
                result.append(part)
        return ''.join(result)
    
    def _get_email_body(self, msg: email.message.Message) -> str:
        """Extract plain text body from email message."""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        body = payload.decode(charset, errors='replace')
                        break
                elif content_type == "text/html" and not body:
                    # Fallback to HTML if no plain text
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        html_body = payload.decode(charset, errors='replace')
                        # Simple HTML stripping
                        body = re.sub(r'<[^>]+>', '', html_body)
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or 'utf-8'
                body = payload.decode(charset, errors='replace')
        
        return body.strip()
    
    def _connect_imap(self) -> Optional[imaplib.IMAP4_SSL]:
        """Connect to Gmail IMAP server."""
        if not self.email_address or not self.app_password:
            return None
        try:
            imap = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            imap.login(self.email_address, self.app_password)
            return imap
        except Exception as e:
            logger.error(f"IMAP connection failed: {e}")
            return None
    
    def fetch_unread_emails(self, folder: str = "INBOX", limit: int = 10) -> dict[str, Any]:
        """
        Fetch unread emails from Gmail inbox.
        Returns list of emails with sender, subject, body, date, message_id.
        """
        if not self.email_address or not self.app_password:
            return {"status": "error", "error": "Gmail not configured (GMAIL_ADDRESS, GMAIL_APP_PASSWORD)"}
        
        imap = self._connect_imap()
        if not imap:
            return {"status": "error", "error": "Could not connect to Gmail IMAP"}
        
        try:
            imap.select(folder)
            
            # Search for unread emails
            status, messages = imap.search(None, 'UNSEEN')
            if status != 'OK':
                return {"status": "error", "error": "Failed to search emails"}
            
            email_ids = messages[0].split()
            if not email_ids:
                return {"status": "success", "emails": [], "message": "No unread emails"}
            
            # Get the most recent emails up to limit
            email_ids = email_ids[-limit:]
            
            emails = []
            for eid in email_ids:
                status, msg_data = imap.fetch(eid, '(RFC822)')
                if status != 'OK':
                    continue
                
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Extract email details
                from_header = msg.get("From", "")
                from_name, from_email = parseaddr(from_header)
                from_name = self._decode_header_value(from_name) or from_email
                
                subject = self._decode_header_value(msg.get("Subject", "(No Subject)"))
                date_str = msg.get("Date", "")
                message_id = msg.get("Message-ID", "")
                in_reply_to = msg.get("In-Reply-To", "")
                references = msg.get("References", "")
                
                body = self._get_email_body(msg)
                
                emails.append({
                    "id": eid.decode() if isinstance(eid, bytes) else str(eid),
                    "from_email": from_email,
                    "from_name": from_name,
                    "subject": subject,
                    "body": body,
                    "date": date_str,
                    "message_id": message_id,
                    "in_reply_to": in_reply_to,
                    "references": references,
                })
            
            imap.close()
            imap.logout()
            
            return {
                "status": "success",
                "emails": emails,
                "count": len(emails),
                "message": f"Found {len(emails)} unread email(s)"
            }
            
        except Exception as e:
            logger.exception(f"Error fetching emails: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            try:
                imap.logout()
            except:
                pass
    
    def fetch_email_by_id(self, email_id: str, folder: str = "INBOX") -> dict[str, Any]:
        """Fetch a specific email by its ID."""
        if not self.email_address or not self.app_password:
            return {"status": "error", "error": "Gmail not configured"}
        
        imap = self._connect_imap()
        if not imap:
            return {"status": "error", "error": "Could not connect to Gmail IMAP"}
        
        try:
            imap.select(folder)
            status, msg_data = imap.fetch(email_id.encode() if isinstance(email_id, str) else email_id, '(RFC822)')
            
            if status != 'OK' or not msg_data or not msg_data[0]:
                return {"status": "error", "error": f"Email {email_id} not found"}
            
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            from_header = msg.get("From", "")
            from_name, from_email = parseaddr(from_header)
            from_name = self._decode_header_value(from_name) or from_email
            
            return {
                "status": "success",
                "email": {
                    "id": email_id,
                    "from_email": from_email,
                    "from_name": from_name,
                    "subject": self._decode_header_value(msg.get("Subject", "")),
                    "body": self._get_email_body(msg),
                    "date": msg.get("Date", ""),
                    "message_id": msg.get("Message-ID", ""),
                    "in_reply_to": msg.get("In-Reply-To", ""),
                }
            }
        except Exception as e:
            logger.exception(f"Error fetching email {email_id}: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            try:
                imap.logout()
            except:
                pass
    
    def mark_as_read(self, email_id: str, folder: str = "INBOX") -> dict[str, Any]:
        """Mark an email as read."""
        if not self.email_address or not self.app_password:
            return {"status": "error", "error": "Gmail not configured"}
        
        imap = self._connect_imap()
        if not imap:
            return {"status": "error", "error": "Could not connect to Gmail IMAP"}
        
        try:
            imap.select(folder)
            imap.store(email_id.encode() if isinstance(email_id, str) else email_id, '+FLAGS', '\\Seen')
            imap.close()
            imap.logout()
            return {"status": "success", "message": f"Email {email_id} marked as read"}
        except Exception as e:
            logger.exception(f"Error marking email as read: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            try:
                imap.logout()
            except:
                pass
    
    def _create_html_template(self, body: str) -> str:
        """
        Create a professional HTML email template.
        """
        # Escape HTML in body and preserve line breaks
        body_html = html.escape(body).replace('\n', '<br>')
        
        # Check if body contains bullet points (•) and format them
        if '•' in body_html:
            lines = body_html.split('<br>')
            formatted_lines = []
            in_list = False
            
            for line in lines:
                if '•' in line:
                    if not in_list:
                        formatted_lines.append('<ul style="margin: 10px 0; padding-left: 20px;">')
                        in_list = True
                    # Extract bullet content
                    content = line.replace('•', '').strip()
                    formatted_lines.append(f'<li style="margin: 5px 0;">{content}</li>')
                else:
                    if in_list:
                        formatted_lines.append('</ul>')
                        in_list = False
                    if line.strip():
                        formatted_lines.append(f'<p style="margin: 10px 0;">{line}</p>')
            
            if in_list:
                formatted_lines.append('</ul>')
            
            body_html = ''.join(formatted_lines)
        else:
            # Simple paragraph formatting
            body_html = '<p style="margin: 10px 0;">' + body_html.replace('<br><br>', '</p><p style="margin: 10px 0;">') + '</p>'
        
        template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 20px 0;">
                <table role="presentation" style="width: 600px; max-width: 100%; border-collapse: collapse; background-color: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 600;">AccessAssist</h1>
                            <p style="margin: 5px 0 0 0; color: #e0e7ff; font-size: 14px;">Your Access Management Assistant</p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px; color: #333333; font-size: 15px; line-height: 1.6;">
                            {body_html}
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8f9fa; padding: 20px 30px; border-top: 1px solid #e9ecef;">
                            <p style="margin: 0; color: #6c757d; font-size: 13px; line-height: 1.5;">
                                Best regards,<br>
                                <strong style="color: #495057;">AccessAssist</strong>
                            </p>
                            <p style="margin: 15px 0 0 0; color: #adb5bd; font-size: 12px;">
                                This is an automated message from your access management system.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """.strip()
        
        return template
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        reply_to_message_id: Optional[str] = None,
        references: Optional[str] = None,
        use_html: bool = True
    ) -> dict[str, Any]:
        """
        Send an email via Gmail SMTP.
        Supports threading by providing reply_to_message_id and references.
        Sends both HTML and plain text versions for maximum compatibility.
        """
        if not self.email_address or not self.app_password:
            logger.info(f"[Mock] Email would send to={to} subject={subject}")
            return {"status": "success", "message": f"Email queued (mock) to {to}", "mock": True}
        
        try:
            msg = MIMEMultipart('alternative')
            msg["Subject"] = subject
            msg["From"] = formataddr((self.bot_name, self.email_address))
            msg["To"] = to
            
            # Add threading headers for replies
            if reply_to_message_id:
                msg["In-Reply-To"] = reply_to_message_id
                msg["References"] = references or reply_to_message_id
            
            # Create plain text version (fallback)
            plain_body = body + "\n\n---\nBest regards,\nAccessAssist"
            part1 = MIMEText(plain_body, 'plain')
            msg.attach(part1)
            
            # Create HTML version
            if use_html:
                html_body = self._create_html_template(body)
                part2 = MIMEText(html_body, 'html')
                msg.attach(part2)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.app_password)
                server.sendmail(self.email_address, [to], msg.as_string())
            
            logger.info(f"Email sent to {to}: {subject}")
            return {
                "status": "success",
                "message": f"Email sent to {to}",
                "to": to,
                "subject": subject
            }
            
        except Exception as e:
            logger.exception(f"Send email failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def send_reply(
        self,
        original_email: dict,
        body: str,
        include_original: bool = True
    ) -> dict[str, Any]:
        """
        Send a reply to an email, maintaining the thread.
        """
        to = original_email.get("from_email")
        original_subject = original_email.get("subject", "")
        
        # Add Re: if not already present
        if not original_subject.lower().startswith("re:"):
            subject = f"Re: {original_subject}"
        else:
            subject = original_subject
        
        # Build reply body (no need to add signature - template handles it)
        if include_original:
            original_body = original_email.get("body", "")
            original_from = original_email.get("from_name") or original_email.get("from_email")
            original_date = original_email.get("date", "")
            
            # For HTML, we'll quote the original nicely
            quoted_lines = original_body.split("\n")[:20]  # Limit quoted text
            quoted_text = "\n".join(f"> {line}" for line in quoted_lines)
            full_body = f"{body}\n\n---\nOn {original_date}, {original_from} wrote:\n{quoted_text}"
        else:
            full_body = body
        
        return self.send_email(
            to=to,
            subject=subject,
            body=full_body,
            reply_to_message_id=original_email.get("message_id"),
            references=original_email.get("references") or original_email.get("message_id")
        )
    
    def search_emails(
        self,
        query: str,
        folder: str = "INBOX",
        limit: int = 10
    ) -> dict[str, Any]:
        """
        Search emails using IMAP search criteria.
        query examples: 'FROM "user@example.com"', 'SUBJECT "access request"', 'SINCE 01-Jan-2026'
        """
        if not self.email_address or not self.app_password:
            return {"status": "error", "error": "Gmail not configured"}
        
        imap = self._connect_imap()
        if not imap:
            return {"status": "error", "error": "Could not connect to Gmail IMAP"}
        
        try:
            imap.select(folder)
            status, messages = imap.search(None, query)
            
            if status != 'OK':
                return {"status": "error", "error": f"Search failed: {query}"}
            
            email_ids = messages[0].split()[-limit:]  # Get last N matches
            
            emails = []
            for eid in email_ids:
                status, msg_data = imap.fetch(eid, '(RFC822)')
                if status != 'OK':
                    continue
                
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                from_header = msg.get("From", "")
                from_name, from_email_addr = parseaddr(from_header)
                
                emails.append({
                    "id": eid.decode() if isinstance(eid, bytes) else str(eid),
                    "from_email": from_email_addr,
                    "from_name": self._decode_header_value(from_name),
                    "subject": self._decode_header_value(msg.get("Subject", "")),
                    "date": msg.get("Date", ""),
                    "message_id": msg.get("Message-ID", ""),
                })
            
            imap.close()
            imap.logout()
            
            return {
                "status": "success",
                "emails": emails,
                "count": len(emails),
                "query": query
            }
            
        except Exception as e:
            logger.exception(f"Error searching emails: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            try:
                imap.logout()
            except:
                pass


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
