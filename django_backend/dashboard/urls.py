from django.urls import path
from .views import DashboardStatsView, QuizAttemptView

urlpatterns = [
    path('api/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('api/quiz/submit/', QuizAttemptView.as_view(), name='quiz-submit'),
]
