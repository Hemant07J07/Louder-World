from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.conf import settings
from django.utils import timezone
from bson.objectid import ObjectId
from pymongo.errors import PyMongoError
from .mongo import events_coll, subscriptions_coll, serialize_event
from .serializers import SubscriptionSerializer
from datetime import datetime


def mongo_unavailable(detail: str = "MongoDB unavailable"):
    return Response({"detail": detail}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

def require_admin_token(request):
    token = request.headers.get("X-Admin-Token") or request.GET.get("admin_token")
    return token == settings.ADMIN_API_TOKEN

class EventListView(APIView):
    """
    GET /api/events/?q=music&city=sydney&status=new&page=1
    """
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        q = request.GET.get("q")
        city = request.GET.get("city")
        status_filter = request.GET.get("status")
        start_from = request.GET.get("from")  # ISO date
        start_to = request.GET.get("to")

        query = {}
        if q:
            # simple text search on title + description
            query["$or"] = [
                {"title": {"$regex": q, "$options": "i"}},
                {"description": {"$regex": q, "$options": "i"}},
            ]
        if city:
            city_or = [
                {"city": {"$regex": city, "$options": "i"}},
                {"venue": {"$regex": city, "$options": "i"}},
            ]
            if "$or" in query:
                q_or = query.pop("$or")
                query.setdefault("$and", []).extend([{"$or": q_or}, {"$or": city_or}])
            else:
                query["$or"] = city_or
        if status_filter:
            query["status"] = status_filter
        if start_from or start_to:
            time_q = {}
            if start_from:
                time_q["$gte"] = start_from
            if start_to:
                time_q["$lte"] = start_to
            if time_q:
                query["start_time"] = time_q

        # pagination via DRF paginator
        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        paginator.page_size = request.GET.get("page_size") or 12

        try:
            cursor = events_coll.find(query).sort("start_time", 1)
            # convert cursor to list then paginate
            items = [serialize_event(d) for d in cursor]
        except PyMongoError:
            return mongo_unavailable()
        page = paginator.paginate_queryset(items, request)
        return paginator.get_paginated_response(page)


class EventDetailView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request, event_id):
        try:
            doc = events_coll.find_one({"_id": ObjectId(event_id)})
        except PyMongoError:
            return mongo_unavailable()
        except Exception:
            return Response({"detail":"Invalid id"}, status=status.HTTP_400_BAD_REQUEST)
        if not doc:
            return Response({"detail":"Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(serialize_event(doc))

class SubscriptionView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = SubscriptionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        event_id = data["event_id"]
        # optional: verify event exists
        try:
            _ = events_coll.find_one({"_id": ObjectId(event_id)})
        except PyMongoError:
            return mongo_unavailable()
        except Exception:
            return Response({"detail":"Invalid event id"}, status=status.HTTP_400_BAD_REQUEST)

        doc = {
            "event_id": event_id,
            "email": data["email"],
            "consent": data["consent"],
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        try:
            subscriptions_coll.insert_one(doc)
        except PyMongoError:
            return mongo_unavailable()
        return Response({"status":"ok"}, status=status.HTTP_201_CREATED)


class AdminImportView(APIView):
    """
    POST /api/admin/import/<id>  (requires X-Admin-Token header)
    body: optional { notes: "..." }
    """
    def post(self, request, event_id):
        if not require_admin_token(request):
            return Response({"detail":"Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            obj_id = ObjectId(event_id)
        except Exception:
            return Response({"detail":"Invalid id"}, status=status.HTTP_400_BAD_REQUEST)

        user = request.headers.get("X-User-Email", "admin")  # optional header indicating who did import
        now = datetime.utcnow().isoformat() + "Z"

        notes = None
        try:
            notes = request.data.get("notes")
        except Exception:
            notes = None
        if isinstance(notes, str):
            notes = notes.strip() or None

        try:
            update_fields = {"status": "imported", "importedBy": user, "importedAt": now}
            if notes is not None:
                update_fields["importNotes"] = notes
            res = events_coll.update_one(
                {"_id": obj_id},
                {"$set": update_fields},
            )
        except PyMongoError:
            return mongo_unavailable()
        if res.matched_count == 0:
            return Response({"detail":"Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"status":"imported"})
