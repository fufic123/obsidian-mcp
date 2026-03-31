"""Vault-related exceptions."""


class VaultNotFoundError(Exception):
    """Vault directory does not exist."""


class VaultReadError(Exception):
    """Failed to read from vault."""


class VaultWriteError(Exception):
    """Failed to write to vault."""


class PathSecurityError(Exception):
    """Path traversal or symlink attack detected."""
