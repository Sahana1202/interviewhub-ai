from app.core.config import settings


class PlacementResourceProvider:
    """External placement-folder boundary. It never crawls or copies folder contents."""

    def status(self) -> dict:
        configured = bool(settings.placement_resources_url and settings.placement_resources_url.strip())
        return {
            "configured": configured,
            "import_configured": False,
            "source_url": settings.placement_resources_url if configured else None,
            "message": (
                "Placement resources are available through the configured placement resource source. "
                "Folder import is not currently configured."
                if configured else "Placement resource import is not currently configured."
            ),
        }


def placement_resource_status() -> dict:
    return PlacementResourceProvider().status()
