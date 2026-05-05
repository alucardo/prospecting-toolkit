import imaplib
import email
from email.header import decode_header
from datetime import datetime


def get_unread_emails(settings, limit=20):
    """
    Łączy się przez IMAP i pobiera nieprzeczytane wiadomości.
    Zwraca listę słowników z podstawowymi danymi.
    """
    if not settings.imap_host or not settings.imap_username or not settings.imap_password:
        raise ValueError('Brak konfiguracji IMAP — uzupełnij ustawienia.')

    # Połączenie
    if settings.imap_use_ssl:
        conn = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)
    else:
        conn = imaplib.IMAP4(settings.imap_host, settings.imap_port)

    try:
        conn.login(settings.imap_username, settings.imap_password)
        conn.select('INBOX')

        # Szukaj nieprzeczytanych
        status, data = conn.search(None, 'UNSEEN')
        if status != 'OK':
            return []

        uids = data[0].split()
        if not uids:
            return []

        # Ogranicz do ostatnich N
        uids = uids[-limit:]

        emails = []
        for uid in reversed(uids):
            status, msg_data = conn.fetch(uid, '(RFC822.HEADER)')
            if status != 'OK':
                continue

            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            # Dekoduj nadawcę
            from_raw = msg.get('From', '')
            sender = _decode_str(from_raw)

            # Dekoduj temat
            subject_raw = msg.get('Subject', '(brak tematu)')
            subject = _decode_str(subject_raw)

            # Data
            date_raw = msg.get('Date', '')
            date = _parse_date(date_raw)

            emails.append({
                'uid': uid.decode(),
                'sender': sender,
                'subject': subject,
                'date': date,
            })

        return emails

    finally:
        try:
            conn.logout()
        except Exception:
            pass


def get_unread_count(settings):
    """Szybki licznik nieprzeczytanych — bez pobierania treści."""
    if not settings.imap_host or not settings.imap_username or not settings.imap_password:
        return None

    try:
        if settings.imap_use_ssl:
            conn = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)
        else:
            conn = imaplib.IMAP4(settings.imap_host, settings.imap_port)

        conn.login(settings.imap_username, settings.imap_password)
        conn.select('INBOX')
        status, data = conn.search(None, 'UNSEEN')
        conn.logout()

        if status == 'OK':
            uids = data[0].split()
            return len(uids)
        return 0
    except Exception:
        return None


def _decode_str(value):
    """Dekoduje nagłówek email (może być base64/quoted-printable)."""
    if not value:
        return ''
    parts = decode_header(value)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            try:
                decoded.append(part.decode(charset or 'utf-8', errors='replace'))
            except (LookupError, TypeError):
                decoded.append(part.decode('utf-8', errors='replace'))
        else:
            decoded.append(part)
    return ''.join(decoded)


def _parse_date(date_str):
    """Parsuje datę z nagłówka email."""
    if not date_str:
        return None
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(date_str)
    except Exception:
        return None
