class CrawlerError(Exception):
    """Base for all named crawler errors."""


class AuthMissing(CrawlerError):
    """`~/Documents/.udemy/` or its expected files are absent/unreadable."""


class AuthInvalid(CrawlerError):
    """API returned 401/403 — cookies are stale or user doesn't own the resource."""


class CloudflareChallenge(CrawlerError):
    """API returned an HTML challenge page instead of JSON; `cf_clearance` likely expired."""


class RateLimited(CrawlerError):
    """API returned 429 beyond the retry budget."""


class CourseIdUnresolved(CrawlerError):
    """Could not derive a numeric `course_id` from the supplied URL/slug."""
