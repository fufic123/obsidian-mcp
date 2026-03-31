"""Configuration-related exceptions."""


class ConfigError(Exception):
    """General configuration error."""


class NamespaceNotFoundError(Exception):
    """No vault mapping found for the given working directory."""
