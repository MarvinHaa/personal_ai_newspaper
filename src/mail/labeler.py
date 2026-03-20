"""
Gmail Labeler – markiert verarbeitete Mails mit dem 'processed'-Label.
"""

import logging
from typing import Optional

from googleapiclient.discovery import Resource

from config import load_settings

logger = logging.getLogger(__name__)


class GmailLabeler:
    """Verwaltet Labels in Gmail – erstellt und setzt das 'processed'-Label."""

    def __init__(self, service: Resource, settings: Optional[dict] = None):
        """
        Args:
            service: Authentifizierter Gmail API Service (von GmailFetcher.service)
            settings: Pipeline-Settings (optional, wird sonst geladen)
        """
        self.service = service
        self.settings = settings or load_settings()
        self.processed_label_name = self.settings["mail"]["processed_label"]
        self._label_id: Optional[str] = None

    # ── Label Management ────────────────────────────────────

    def _get_or_create_label(self) -> str:
        """Gibt die Label-ID zurück. Erstellt das Label falls nötig."""
        if self._label_id:
            return self._label_id

        # Bestehendes Label suchen
        results = self.service.users().labels().list(userId="me").execute()
        for label in results.get("labels", []):
            if label["name"] == self.processed_label_name:
                self._label_id = label["id"]
                logger.info(f"Label '{self.processed_label_name}' gefunden: {self._label_id}")
                return self._label_id

        # Label erstellen
        label_body = {
            "name": self.processed_label_name,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show",
        }
        created = (
            self.service.users()
            .labels()
            .create(userId="me", body=label_body)
            .execute()
        )
        self._label_id = created["id"]
        logger.info(f"Label '{self.processed_label_name}' erstellt: {self._label_id}")
        return self._label_id

    # ── Marking ─────────────────────────────────────────────

    def mark_as_processed(self, message_ids: list[str]) -> int:
        """
        Fügt das 'processed'-Label zu den angegebenen Mails hinzu.

        Args:
            message_ids: Liste von Gmail Message-IDs

        Returns:
            Anzahl erfolgreich gelabelter Mails
        """
        if not message_ids:
            logger.info("Keine Mails zum Markieren.")
            return 0

        label_id = self._get_or_create_label()
        success_count = 0

        # Batch-Modify für Effizienz (max. 1000 pro Batch)
        for i in range(0, len(message_ids), 1000):
            batch = message_ids[i : i + 1000]
            try:
                self.service.users().messages().batchModify(
                    userId="me",
                    body={
                        "ids": batch,
                        "addLabelIds": [label_id],
                    },
                ).execute()
                success_count += len(batch)
                logger.info(f"Batch {i // 1000 + 1}: {len(batch)} Mails als '{self.processed_label_name}' markiert.")
            except Exception as e:
                logger.error(f"Fehler beim Batch-Labeling: {e}")

        logger.info(f"Insgesamt {success_count}/{len(message_ids)} Mails als verarbeitet markiert.")
        return success_count
