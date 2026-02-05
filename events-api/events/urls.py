from django.urls import path
from .views import EventListView, EventDetailView, SubscriptionView, AdminImportView
from .api_recommend import RecommendationView

urlpatterns = [
    path("events/", EventListView.as_view(), name="events-list"),
    path("events/<str:event_id>/", EventDetailView.as_view(), name="events-detail"),
    path("subscriptions/", SubscriptionView.as_view(), name="subscriptions"),
    path("admin/import/<str:event_id>/", AdminImportView.as_view(), name="admin-import"),
    path("recommendations/", RecommendationView.as_view(), name="recommendations"),
]
