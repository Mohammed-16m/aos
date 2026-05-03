from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated

from .tokens import CustomRefreshToken as RefreshToken

from .serializers import RegisterSerializer
from .models import User
from .permissions import IsAdmin
from django.contrib.auth import get_user_model

# Create your views here.


@api_view(['POST'])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "status": "success",
            "data": {
                "access":  str(refresh.access_token),
                "refresh": str(refresh),
                "user_id": user.id,
                "role":    user.role
            }
        }, status=201)
    return Response({"status": "error", "message": serializer.errors}, status=400)


User = get_user_model()

@api_view(['POST'])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    user = User.objects.filter(email=email).first()

    if user and user.check_password(password):
        refresh = RefreshToken.for_user(user)

        return Response({
            "status": "success",
            "data": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user_id": user.id,
                "role": user.role
            }
        })

    return Response({
        "status": "error",
        "message": "Invalid credentials"
    }, status=401)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_me(request):
    user = request.user

    return Response({
        "status": "success",
        "data": {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,   
            "last_name": user.last_name,
            "email": user.email,
            "role": user.role
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def validate_token(request):
    user = request.user
    return Response({
        "status": "success",
        "data": {
            "user_id": user.id,
            "email": user.email,      # ← added
            "role": user.role
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()

        return Response({"status": "success", "message": "Logged out"}, status=200)
    
    except Exception:
        return Response({
            "status": "error",
            "message": "Invalid token"
        }, status=400)
    


@api_view(['GET'])
@permission_classes([IsAdmin])
def admin_test(request):
    return Response({
        "status": "success",
        "message": "Hello Admin, you have access"
    })