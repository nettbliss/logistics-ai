
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class TestAPIView(APIView):
    """Тестовый API для проверки авторизации"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({
            'status': 'ok',
            'message': 'Вы успешно авторизованы!',
            'user': request.user.username
        })