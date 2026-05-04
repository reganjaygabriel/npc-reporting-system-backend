"""
Optimized Authentication Views
High-performance login with minimal database queries
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.cache import cache
from django.db import transaction
import time

class AuthViewSet(viewsets.ViewSet):
    """Optimized authentication endpoints"""
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        High-performance login with JWT tokens and caching
        """
        start_time = time.time()
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({
                'error': 'Username and password required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check rate limiting cache
        rate_limit_key = f"login_attempts:{request.META.get('REMOTE_ADDR', 'unknown')}"
        attempts = cache.get(rate_limit_key, 0)
        
        if attempts >= 5:  # Max 5 attempts per IP per hour
            return Response({
                'error': 'Too many login attempts. Please try again later.'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Attempt authentication with optimized query
        try:
            with transaction.atomic():
                user = authenticate(
                    request=request,
                    username=username, 
                    password=password
                )
                
                if user and user.is_active:
                    # Login user with session
                    login(request, user)
                    
                    # Generate JWT tokens
                    from rest_framework_simplejwt.tokens import RefreshToken
                    refresh = RefreshToken.for_user(user)
                    access_token = refresh.access_token
                    
                    # Clear rate limiting
                    cache.delete(rate_limit_key)
                    
                    # Cache user data for 15 minutes
                    user_data = {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'is_staff': user.is_staff,
                    }
                    cache.set(f"user_data:{user.id}", user_data, 900)  # 15 minutes
                    
                    response_time = round((time.time() - start_time) * 1000, 2)
                    
                    return Response({
                        'user': user_data,
                        'access': str(access_token),
                        'refresh': str(refresh),
                        'access_token': str(access_token),  # For compatibility
                        'refresh_token': str(refresh),     # For compatibility
                        'message': 'Login successful',
                        'response_time_ms': response_time
                    }, status=status.HTTP_200_OK)
                else:
                    # Increment rate limiting
                    cache.set(rate_limit_key, attempts + 1, 3600)  # 1 hour
                    
                    return Response({
                        'error': 'Invalid credentials'
                    }, status=status.HTTP_401_UNAUTHORIZED)
                    
        except Exception as e:
            return Response({
                'error': 'Authentication service temporarily unavailable'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Optimized logout"""
        try:
            # Clear user cache
            cache.delete(f"user_data:{request.user.id}")
            logout(request)
            
            return Response({
                'message': 'Successfully logged out'
            }, status=status.HTTP_200_OK)
        except Exception:
            return Response({
                'message': 'Logout completed'
            }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        """Get cached user profile"""
        # Try cache first
        user_data = cache.get(f"user_data:{request.user.id}")
        
        if not user_data:
            # Fallback to database
            user_data = {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'is_staff': request.user.is_staff,
            }
            cache.set(f"user_data:{request.user.id}", user_data, 900)
        
        return Response(user_data)


class UserViewSet(viewsets.ModelViewSet):
    """Optimized user management"""
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """List users with caching"""
        cache_key = "all_users_list"
        users_data = cache.get(cache_key)
        
        if not users_data:
            users = User.objects.select_related().only(
                'id', 'username', 'email', 'first_name', 'last_name', 'is_staff'
            )
            users_data = [{
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_staff': user.is_staff,
            } for user in users]
            cache.set(cache_key, users_data, 600)  # 10 minutes
        
        return Response(users_data)


class PasswordResetRequestViewSet(viewsets.ViewSet):
    """Simple password reset requests"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """List password reset requests"""
        return Response([])
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def pending_count(self, request):
        """Get count of pending password reset requests"""
        # For now, return 0 since we don't have a proper password reset system
        return Response({'count': 0})