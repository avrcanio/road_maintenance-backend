from django.urls import path

from .views_public import CustomerReviewPublicView

app_name = 'customer_review'

urlpatterns = [
    path('public/review/item/<str:jti>/', CustomerReviewPublicView.as_view(), name='review-public'),
]
