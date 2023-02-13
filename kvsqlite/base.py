class BaseClient:
    def get(self, key: str):
        """Get the value of ``key``

        Args:
            key (``str``):
                The key to get.
        """
        raise NotImplementedError

    def set(self, key: str, value):
        """Get the value of ``key``

        Args:
            key (``str``):
                The key.

            value (``Any``):
                The value to set for ``key``.
        """
        raise NotImplementedError

    def delete(self, key: str):
        """Delete ``key`` from database

        Args:
            key (``str``):
                The key to get.
        """
        raise NotImplementedError

    def commit(self):
        """Commit the current changes

        Returns:
            :py:class:`bool`: ``True`` on success.
        """
        raise NotImplementedError

    def exists(self, key: str):
        """Check if ``key`` already exists in database

        Args:
            key (``str``):
                The key to search for.

        Returns:
            :py:class:`bool`: ``True`` if found, otherwise ``False``.
        """
        raise NotImplementedError

    def keys(self, like: str = "%"):
        """Return list of keys in database with the given pattern

        Args:
            like (``str``, *optional*):
                SQLite LIKE operator. Defaults to ``%`` (all keys).

        """
        raise NotImplementedError

    def flush(self):
        """Flush the current database"""
        raise NotImplementedError

    def close(self, optimize_database: bool = True):
        """Close database

        Args:
            optimize_database (``bool``, **optional**):
                Whether optimize database before closing or not. Defaults to ``True``.
        """
        raise NotImplementedError
