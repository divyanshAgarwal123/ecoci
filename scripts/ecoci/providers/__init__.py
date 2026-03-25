"""Provider abstractions for CI platforms (GitHub, GitLab, etc.)."""

from .base import CIProvider
from .github import GitHubProvider
from .gitlab import GitLabProvider

__all__ = ["CIProvider", "GitHubProvider", "GitLabProvider"]
