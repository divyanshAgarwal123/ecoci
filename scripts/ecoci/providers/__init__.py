"""Provider abstractions for CI platforms (GitHub, GitLab, etc.)."""

from .base import CIProvider
from .github import GitHubProvider

__all__ = ["CIProvider", "GitHubProvider"]
