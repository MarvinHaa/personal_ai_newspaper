"""
Gmail Fetcher – holt Newsletter-Mails via Gmail API (OAuth2).
"""

import base64
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import load_settings, get_credentials_path

logger = logging.getLogger(__name__)

# Gmail API – nur Lese- und Label-Rechte
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.modify",
]

# Token wird im data/-Verzeichnis gecacht
TOKEN_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "token.json"


class GmailFetcher:
    """Holt Mails mit einem bestimmten Label aus Gmail."""

    def __init__(self, settings: Optional[dict] = None):
        self.settings = settings or load_settings()
        self.mail_config = self.settings["mail"]
        self.service = self._authenticate()

    # ── Auth ────────────────────────────────────────────────

    def _authenticate(self):
        """OAuth2-Flow: beim ersten Mal Browser-Login, danach gecachter Token."""
        creds = None

        if TOKEN_PATH.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Token abgelaufen – wird automatisch erneuert.")
                creds.refresh(Request())
            else:
                logger.info("Erster Login – Browser öffnet sich für OAuth2...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(get_credentials_path()), SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Token speichern
            TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(TOKEN_PATH, "w") as token_file:
                token_file.write(creds.to_json())
            logger.info(f"Token gespeichert: {TOKEN_PATH}")

        return build("gmail", "v1", credentials=creds)

    # ── Label-Lookup ────────────────────────────────────────

    def _get_label_id(self, label_name: str) -> Optional[str]:
        """Gibt die ID eines Gmail-Labels zurück (oder None)."""
        results = self.service.users().labels().list(userId="me").execute()
        for label in results.get("labels", []):
            if label["name"] == label_name:
                return label["id"]
        return None

    # ── Fetch ───────────────────────────────────────────────

    def fetch_newsletters(self) -> list[dict]:
        """
        Holt alle Mails mit Label `source_label` (ohne `processed_label`)
        aus dem konfigurierten Zeitfenster.

        Returns:
            Liste von Dicts mit: id, subject, sender, date, body
        """
        source_label = self.mail_config["source_label"]
        processed_label = self.mail_config["processed_label"]
        time_window = self.mail_config["time_window_hours"]
        max_results = self.mail_config.get("max_results", 100) or 500

        # Label-IDs auflösen
        source_label_id = self._get_label_id(source_label)
        if not source_label_id:
            logger.warning(f"Label '{source_label}' nicht gefunden in Gmail.")
            return []

        processed_label_id = self._get_label_id(processed_label)

        # Zeitfenster berechnen
        cutoff = datetime.now(timezone.utc) - timedelta(hours=time_window)
        after_epoch = int(cutoff.timestamp())

        # Query bauen
        query = f"after:{after_epoch}"
        if processed_label_id:
            query += f" -label:{processed_label}"

        logger.info(
            f"Suche Mails: label='{source_label}', query='{query}', max={max_results}"
        )

        # Mails auflisten
        results = (
            self.service.users()
            .messages()
            .list(
                userId="me",
                labelIds=[source_label_id],
                q=query,
                maxResults=max_results,
            )
            .execute()
        )

        message_ids = results.get("messages", [])
        logger.info(f"{len(message_ids)} Mails gefunden.")

        # Volldaten pro Mail laden
        emails = []
        for msg_ref in message_ids:
            email = self._fetch_message_detail(msg_ref["id"])
            if email:
                emails.append(email)

        logger.info(f"{len(emails)} Mails erfolgreich geladen.")
        return emails

    def _fetch_message_detail(self, message_id: str) -> Optional[dict]:
        """Lädt die Volldetails einer einzelnen Mail."""
        try:
            msg = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )

            headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
            body = self._extract_body(msg["payload"])

            return {
                "id": message_id,
                "subject": headers.get("Subject", "(kein Betreff)"),
                "sender": headers.get("From", "(unbekannt)"),
                "date": headers.get("Date", ""),
                "body": body,
            }
        except Exception as e:
            logger.error(f"Fehler beim Laden von Mail {message_id}: {e}")
            return None

    # ── Body extrahieren ────────────────────────────────────

    def _extract_body(self, payload: dict) -> str:
        """Extrahiert den Body als Plain-Text (bevorzugt) oder HTML."""
        # Direkt im Payload
        if "body" in payload and payload["body"].get("data"):
            return self._decode_base64(payload["body"]["data"])

        # In Parts suchen (multipart)
        parts = payload.get("parts", [])

        # Zuerst nach text/plain suchen
        for part in parts:
            if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                return self._decode_base64(part["body"]["data"])

        # Fallback: text/html
        for part in parts:
            if part.get("mimeType") == "text/html" and part.get("body", {}).get("data"):
                return self._decode_base64(part["body"]["data"])

        # Rekursiv in verschachtelten Parts suchen
        for part in parts:
            if "parts" in part:
                result = self._extract_body(part)
                if result:
                    return result

        return ""

    @staticmethod
    def _decode_base64(data: str) -> str:
        """Dekodiert Base64url-encodierten Gmail-Body."""
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
