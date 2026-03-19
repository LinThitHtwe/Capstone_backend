"""Placeholder API views — replace with real endpoints later."""

from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def health(request):
    """Simple JSON placeholder to verify the API is running."""
    return Response(
        {
            "status": "ok",
            "message": "Capstone REST API placeholder",
            "version": "0.0.0",
        }
    )
