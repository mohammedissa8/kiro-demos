"""Probe module used to verify the PostFileSave compile hook fires."""
__audit_id__ = "task-manager-cli"


def probe():
    """Return a constant marker string; exists only to exercise the save hook."""
    return "ok"
