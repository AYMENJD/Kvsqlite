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

        Returns:
            :py:class:`bool`: ``True`` on success.
        """
        raise NotImplementedError

    def delete(self, key: str):
        """Delete ``key`` from database

        Args:
            key (``str``):
                The key to delete.
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

    def rename(self, key: str, new_key: str):
        """Rename ``key`` with ``new_key``

        Args:
            key (``str``):
                The key to rename.

            new_key (``str``):
                The key to rename with.

        Returns:
            :py:class:`bool`: ``True`` if renamed, otherwise ``False``.
        """
        raise NotImplementedError

    def keys(self, like: str = "%"):
        """Return list of keys in database with the given pattern

        Args:
            like (``str``, *optional*):
                SQLite LIKE operator. Defaults to ``%`` (all keys).

        Returns:
            :py:class:`list`:
                A list of :py:class:`Tuple` contains keys.

            :py:class:`None`:
                If there is no keys to return.
        """
        raise NotImplementedError

    def flush(self):
        """Flush and remove everything from the current database

        Returns:
            :py:class:`bool`: ``True`` on success.
        """
        raise NotImplementedError

    def close(self, optimize_database: bool = True):
        """Close database connection

        Args:
            optimize_database (``bool``, **optional**):
                Whether optimize database before closing or not. Defaults to ``True``.

        Returns:
            :py:class:`bool`: ``True`` on success.
        """
        raise NotImplementedError
