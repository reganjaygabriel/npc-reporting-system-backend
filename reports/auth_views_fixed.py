"""
Fixed Authentication Views - Simple Session-based Auth
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.cache import cache
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import time
import logging

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class AuthViewSet(viewsets.ViewSet):
    """Simple session-based authentication"""
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        Simple login with session authentication
        """
        start_time = time.time()
        username = request.data.get('username')
        password = request.data.get('password')
        
        logger.info(f"Login attempt for username: {username}")
        
        if not username or not password:
            return Response({
                'error': 'Username and password required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Attempt authentication
            user = authenticate(request=request, username=username, password=password)
            
            if user and user.is_active:
                # Login user with session
                login(request, user)
                
                # Get user profile data
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                }
                
                # Add profile information if available
                try:
                    profile = user.profile
                    user_data.update({
                        'role': profile.role,
                        'full_name': profile.full_name,
                        'department': profile.department,
                        'phone': profile.phone,
                        'position': profile.position,
                    })
                except:
                    user_data['role'] = 'ADMIN' if user.is_staff else 'VIEWER'
                
                response_time = round((time.time() - start_time) * 1000, 2)
                
                logger.info(f"Login successful for user: {username}")
                
                return Response({
                    'user': user_data,
                    'message': 'Login successful',
                    'response_time_ms': response_time,
                    'session_id': request.session.session_key
                }, status=status.HTTP_200_OK)
            else:
                logger.warning(f"Login failed for username: {username}")
                return Response({
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
                    
        except Exception as e:
            logger.error(f"Login error for username {username}: {str(e)}")
            return Response({
                'error': f'Authentication error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Simple logout"""
        try:
            username = request.user.username
            logout(request)
            logger.info(f"Logout successful for user: {username}")
            
            return Response({
                'message': 'Successfully logged out'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response({
                'message': 'Logout completed'
            }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        """Get user profile"""
        try:
            user_data = {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'is_staff': request.user.is_staff,
                'is_superuser': request.user.is_superuser,
            }
            
            # Add profile information if available
            try:
                profile = request.user.profile
                user_data.update({
                    'role': profile.role,
                    'full_name': profile.full_name,
                    'department': profile.department,
                    'phone': profile.phone,
                    'position': profile.position,
                })
            except:
                user_data['role'] = 'ADMIN' if request.user.is_staff else 'VIEWER'
            
            return Response(user_data)
        except Exception as e:
            logger.error(f"Profile error: {str(e)}")
            return Response({
                'error': 'Could not retrieve profile'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserViewSet(viewsets.ModelViewSet):
    """Simple user management"""
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """List users"""
        try:
            users = User.objects.select_related().only(
                'id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser'
            )
            users_data = []
            
            for user in users:
                user_info = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                }
                
                # Add profile info if available
                try:
                    profile = user.profile
                    user_info.update({
                        'role': profile.role,
                        'full_name': profile.full_name,
                        'department': profile.department,
                    })
                except:
                    user_info['role'] = 'ADMIN' if user.is_staff else 'VIEWER'
                
                users_data.append(user_info)
            
            return Response({'results': users_data})
        except Exception as e:
            logger.error(f"User list error: {str(e)}")
            return Response({
                'error': 'Could not retrieve users'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PasswordResetRequestViewSet(viewsets.ViewSet):
    """Simple password reset requests"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """List password reset requests"""
        return Response({'results': []})
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def pending_count(self, request):
        """Get count of pending password reset requests"""
        return Response({'count': 0})