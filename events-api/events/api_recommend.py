from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions


class RecommendationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        POST /api/recommendations/
        body:
        {
          "type": "by_event" | "by_user",
          "event_id": "<mongo_id>",           # required for by_event
          "preferences": "music, free shows", # required for by_user
          "k": 8
        }
        """
        data = request.data or {}
        typ = data.get("type")
        k = int(data.get("k", 8))

        try:
            from .recommender import (
                recommend_by_event,
                recommend_by_preferences,
                fetch_events_with_scores,
                load_index,
            )
        except Exception as e:
            return Response(
                {"detail": "Recommendation dependencies not installed", "error": str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # ensure index exists
        idx, mapping = load_index()
        if idx is None:
            return Response({"detail": "Index not built"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if typ == "by_event":
            event_id = data.get("event_id")
            if not event_id:
                return Response({"detail":"event_id required"}, status=status.HTTP_400_BAD_REQUEST)
            pairs = recommend_by_event(event_id, k=k)
        elif typ == "by_user":
            prefs = data.get("preferences")
            if not prefs:
                return Response({"detail":"preferences required"}, status=status.HTTP_400_BAD_REQUEST)
            pairs = recommend_by_preferences(prefs, k=k)
        else:
            return Response({"detail":"type must be 'by_event' or 'by_user'"}, status=status.HTTP_400_BAD_REQUEST)

        results = fetch_events_with_scores(pairs)
        return Response({"results": results})
