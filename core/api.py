from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import UserSerializer, UserCreateSerializer, UserUpdateSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer that includes user information"""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        # Add user information to the response
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
        }
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token obtain view with Swagger documentation"""
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing User model with full CRUD operations.
    
    list: Returns a list of all users
    create: Creates a new user
    retrieve: Returns user details by ID
    update: Updates user information (PUT)
    partial_update: Partially updates user information (PATCH)
    destroy: Deletes a user
    """
    queryset = User.objects.all().order_by('-date_joined')
    
    def get_serializer_class(self):
        """Return the appropriate serializer class based on action"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_permissions(self):
        """Return the appropriate permissions based on action"""
        if self.action == 'create':
            # Allow anyone to register
            permission_classes = [permissions.AllowAny]
        else:
            # Require authentication for other actions
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @swagger_auto_schema(
        operation_description="Get list of all users",
        responses={200: UserSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """Get list of all users"""
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Register a new user",
        request_body=UserCreateSerializer,
        responses={
            201: UserSerializer,
            400: 'Bad Request'
        }
    )
    def create(self, request, *args, **kwargs):
        """Register a new user"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            response_serializer = UserSerializer(user)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Get user details by ID",
        responses={
            200: UserSerializer,
            404: 'User not found'
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """Get user details by ID"""
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Update user information",
        request_body=UserUpdateSerializer,
        responses={
            200: UserSerializer,
            400: 'Bad Request',
            404: 'User not found'
        }
    )
    def update(self, request, *args, **kwargs):
        """Update user information (PUT)"""
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Partially update user information",
        request_body=UserUpdateSerializer,
        responses={
            200: UserSerializer,
            400: 'Bad Request',
            404: 'User not found'
        }
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially update user information (PATCH)"""
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Delete a user",
        responses={
            204: 'User deleted successfully',
            404: 'User not found'
        }
    )
    def destroy(self, request, *args, **kwargs):
        """Delete a user"""
        return super().destroy(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Get current user profile",
        responses={200: UserSerializer}
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Get current user profile"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
