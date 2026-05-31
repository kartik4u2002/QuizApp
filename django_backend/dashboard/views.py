from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import NewsArticle, Quiz, QuizAttempt
import uuid
import datetime

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Returns stats for the dashboard.
        """
        total_news = NewsArticle.objects.count()
        total_quizzes = Quiz.objects.count()
        user_attempts = QuizAttempt.objects.filter(user_id=request.user.id).count()

        return Response({
            "total_news_ingested": total_news,
            "total_quizzes_generated": total_quizzes,
            "your_quiz_attempts": user_attempts,
            "username": request.user.username
        })

class QuizAttemptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Submit a quiz attempt.
        Expected data: {"quiz_id": "uuid", "answers": [...], "score": 80}
        """
        quiz_id = request.data.get('quiz_id')
        score = request.data.get('score', 0)
        answers = request.data.get('answers', [])

        if not quiz_id:
            return Response({"error": "quiz_id is required"}, status=400)

        attempt = QuizAttempt(
            attempt_id=str(uuid.uuid4()),
            user_id=request.user.id,
            quiz_id=quiz_id,
            score=score,
            answers=answers,
            attempted_at=datetime.datetime.utcnow()
        )
        attempt.save()

        return Response({
            "message": "Quiz attempt recorded.",
            "attempt_id": attempt.attempt_id,
            "score": attempt.score
        })
