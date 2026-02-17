import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class UsageStorage:
    """Handles data storage and retrieval of usage data"""

    def __init__(self, storage_path: str = 'storage/usage_data.json'):
        """
        Initialize storage

        Args:
            storage_path: Path to storage file
        """
        self.storage_path = storage_path
        self.data = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        """
        Load data from storage file

        Returns:
            Dictionary with stored data
        """
        try:
            if not os.path.exists(self.storage_path):
                logger.info(f"Storage file not found: {self.storage_path}")
                return {
                    'last_updated': None,
                    'providers': {},
                    'history': []
                }

            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading storage: {e}")
            return {
                'last_updated': None,
                'providers': {},
                'history': []
            }

    def _save_data(self) -> None:
        """Save current data to storage file"""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving storage: {e}")

    def store_usage_data(self, provider_name: str, period: str, usage_data: Dict[str, Any]) -> None:
        """
        Store usage data for a provider

        Args:
            provider_name: Name of the provider
            period: Time period
            usage_data: Usage data to store
        """
        try:
            if provider_name not in self.data['providers']:
                self.data['providers'][provider_name] = {}

            self.data['providers'][provider_name][period] = {
                'data': usage_data,
                'stored_at': datetime.now().isoformat()
            }

            self._save_data()
        except Exception as e:
            logger.error(f"Error storing usage data: {e}")

    def get_usage_data(self, provider_name: str, period: str = 'daily') -> Optional[Dict[str, Any]]:
        """
        Retrieve usage data for a provider

        Args:
            provider_name: Name of the provider
            period: Time period

        Returns:
            Stored usage data or None
        """
        try:
            return self.data.get('providers', {}).get(provider_name, {}).get(period)
        except Exception as e:
            logger.error(f"Error retrieving usage data: {e}")
            return None

    def add_history_entry(self, entry: Dict[str, Any]) -> None:
        """
        Add an entry to usage history

        Args:
            entry: Entry to add to history
        """
        try:
            history = self.data.get('history', [])

            entry['timestamp'] = datetime.now().isoformat()
            history.append(entry)

            # Keep only last 1000 entries
            if len(history) > 1000:
                history = history[-1000:]

            self.data['history'] = history
            self.data['last_updated'] = datetime.now().isoformat()

            self._save_data()
        except Exception as e:
            logger.error(f"Error adding history entry: {e}")

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve usage history

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of history entries
        """
        try:
            history = self.data.get('history', [])

            if limit and len(history) > limit:
                return history[-limit:]

            return history
        except Exception as e:
            logger.error(f"Error retrieving history: {e}")
            return []

    def get_provider_history(self, provider_name: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve history for a specific provider

        Args:
            provider_name: Name of the provider
            limit: Maximum number of entries to return

        Returns:
            List of provider history entries
        """
        try:
            history = self.data.get('history', [])
            provider_history = [
                entry for entry in history
                if entry.get('provider') == provider_name
            ]

            if limit and len(provider_history) > limit:
                return provider_history[-limit:]

            return provider_history
        except Exception as e:
            logger.error(f"Error retrieving provider history: {e}")
            return []

    def update_provider_limits(self, provider_name: str, limits: Dict[str, Any]) -> None:
        """
        Update provider limits

        Args:
            provider_name: Name of the provider
            limits: New limits to apply
        """
        try:
            if provider_name not in self.data['providers']:
                self.data['providers'][provider_name] = {}

            self.data['providers'][provider_name]['limits'] = limits
            self._save_data()
        except Exception as e:
            logger.error(f"Error updating provider limits: {e}")

    def get_all_providers(self) -> List[str]:
        """
        Get list of all stored providers

        Returns:
            List of provider names
        """
        try:
            return list(self.data.get('providers', {}).keys())
        except Exception as e:
            logger.error(f"Error getting all providers: {e}")
            return []

    def clear_history(self) -> None:
        """Clear all history entries"""
        try:
            self.data['history'] = []
            self._save_data()
        except Exception as e:
            logger.error(f"Error clearing history: {e}")

    def clear_provider_data(self, provider_name: str) -> None:
        """
        Clear all data for a specific provider

        Args:
            provider_name: Name of the provider
        """
        try:
            if provider_name in self.data['providers']:
                del self.data['providers'][provider_name]
                self._save_data()
        except Exception as e:
            logger.error(f"Error clearing provider data: {e}")
