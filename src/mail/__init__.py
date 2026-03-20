"""
Mail Ingestion Package – Gmail-Zugriff und Label-Management.
"""

from .fetcher import GmailFetcher
from .labeler import GmailLabeler

__all__ = ["GmailFetcher", "GmailLabeler"]
