class BaseClient:
    def get(self, key: str, one_time=False):
        """Get the value of ``key``

        Args:
            key (``str``):
                The key to get

            one_time (``bool``, *optional*):
                If True, mark the key for one-time retrieval and delete it after retrieval.
                Defaults to False.

        Returns:
            ``Any``: The value of the key, or None if key doesn't exist
        """
        raise NotImplementedError

    def set(self, key: str, value, one_time=False):
        """Set the value of ``key``

        Args:
            key (``str``):
                The key

            value (``Any``):
                The value to set for ``key``

            one_time (``bool``, *optional*):
                If True, mark the key for one-time retrieval and delete it after retrieval.
                Defaults to False.

        Returns:
            :py:class:`bool`: ``True`` on success
        """
        raise NotImplementedError

    def setex(self, key: str, ttl: int, value, one_time=False):
        """Set the value of ``key`` with a timeout specified by ``ttl``

        Args:
            key (``str``):
                The key

            ttl (``int``):
                The number of seconds for ``key`` timeout (a.k.a ``key`` lifetime)

            value (``Any``):
                The value to set for ``key``

            one_time (``bool``, *optional*):
                If True, mark the key for one-time retrieval and delete it after retrieval.
                Defaults to False.

        Returns:
            :py:class:`bool`: ``True`` on success
        """
        raise NotImplementedError

    def delete(self, key: str):
        """Delete ``key`` from database

        Args:
            key (``str``):
                The key to delete
        """
        raise NotImplementedError

    def commit(self):
        """Commit the current changes

        Returns:
            :py:class:`bool`: ``True`` on success
        """
        raise NotImplementedError

    def exists(self, key: str):
        """Check if ``key`` already exists in database

        Args:
            key (``str``):
                The key to search for

        Returns:
            :py:class:`bool`: ``True`` if found, otherwise ``False``
        """
        raise NotImplementedError

    def ttl(self, key: str):
        """Returns the remaining time to live of a ``key`` that has a timeout

        Args:
            key (``str``):
                The key

        Returns:
            :py:class:`float`: The remaining time, otherwise ``0``
        """
        raise NotImplementedError

    def expire(self, key: str, ttl: int):
        """Set a timeout on ``key``

        Args:
            key (``str``):
                The key

            ttl (``int``):
                The number of seconds for ``key`` timeout (a.k.a ``key`` lifetime)

        Returns:
            :py:class:`bool`: ``True`` on success
        """
        raise NotImplementedError

    def rename(self, key: str, new_key: str):
        """Rename ``key`` with ``new_key``

        Args:
            key (``str``):
                The key to rename

            new_key (``str``):
                The key to rename with

        Returns:
            :py:class:`bool`: ``True`` if renamed, otherwise ``False``
        """
        raise NotImplementedError

    def keys(self, like: str = "%"):
        """Return list of keys in database with the given pattern

        Args:
            like (``str``, *optional*):
                SQLite LIKE operator. Defaults to ``%`` (all keys)

        Returns:
            :py:class:`list`:
                A list of :py:class:`Tuple` contains keys

            :py:class:`None`:
                If there is no keys to return
        """
        raise NotImplementedError

    def cleanex(self):
        """Removes all expired keys from database. This reduces disk usage

        Returns:
            :py:class:`int`: Number of deleted keys
        """
        raise NotImplementedError

    def flush(self):
        """Flush and remove everything from the current database

        Returns:
            :py:class:`bool`: ``True`` on success
        """
        raise NotImplementedError

    def close(self, optimize_database: bool = True):
        """Close database connection

        Args:
            optimize_database (``bool``, **optional**):
                Whether optimize database before closing or not. Defaults to ``True``

        Returns:
            :py:class:`bool`: ``True`` on success
        """
        raise NotImplementedError
