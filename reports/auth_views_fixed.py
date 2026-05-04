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
    authentication_classes = []  # Disable authentication for this viewset
    
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


@method_decorator(csrf_exempt, name='dispatch')
class UserViewSet(viewsets.ModelViewSet):
    """Simple user management"""
    queryset = User.objects.all()
    permission_classes = [AllowAny]  # Temporarily allow all access
    authentication_classes = []  # Disable authentication for this viewset
    
    def create(self, request):
        """Create a new user"""
        try:
            username = request.data.get('username')
            password = request.data.get('password')
            email = request.data.get('email', '')
            first_name = request.data.get('first_name', '')
            last_name = request.data.get('last_name', '')
            is_active = request.data.get('is_active', True)
            role = request.data.get('role', 'VIEWER')
            
            # Create user
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=is_active
            )
            
            # Set is_staff and is_superuser based on role
            user.is_staff = role in ['ADMIN', 'MANAGER']
            user.is_superuser = role == 'ADMIN'
            user.save()
            
            # Create UserProfile
            from reports.models import UserProfile
            profile = UserProfile.objects.create(
                user=user,
                role=role,
                full_name=f"{first_name} {last_name}".strip() or username
            )
            
            logger.info(f"User created: {username} with role {role}")
            
            return Response({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'message': 'User created successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def list(self, request):
        """List users"""
        try:
            # Get all users without select_related to avoid issues
            users = User.objects.all().order_by('-date_joined')
            users_data = []
            
            for user in users:
                user_info = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email or '',
                    'first_name': user.first_name or '',
                    'last_name': user.last_name or '',
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                    'is_active': user.is_active,
                    'date_joined': user.date_joined.isoformat() if user.date_joined else None,
                }
                
                # Add profile info if available
                try:
                    profile = user.profile
                    user_info['profile'] = {
                        'role': profile.role,
                        'full_name': profile.full_name,
                        'department': profile.department,
                    }
                except:
                    # No profile exists, use default role
                    user_info['profile'] = {
                        'role': 'ADMIN' if user.is_staff else 'VIEWER',
                        'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
                        'department': '',
                    }
                
                users_data.append(user_info)
            
            logger.info(f"Returning {len(users_data)} users")
            return Response({'results': users_data})
        except Exception as e:
            logger.error(f"User list error: {str(e)}")
            return Response({
                'error': 'Could not retrieve users'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def update(self, request, pk=None):
        """Update a user (PUT)"""
        try:
            user = User.objects.get(pk=pk)
            
            # Update basic fields
            user.username = request.data.get('username', user.username)
            user.email = request.data.get('email', user.email)
            user.first_name = request.data.get('first_name', user.first_name)
            user.last_name = request.data.get('last_name', user.last_name)
            user.is_active = request.data.get('is_active', user.is_active)
            
            # Update password if provided
            password = request.data.get('password')
            if password:
                user.set_password(password)
            
            # Update role
            role = request.data.get('role')
            if role:
                # Set is_staff and is_superuser based on role
                user.is_staff = role in ['ADMIN', 'MANAGER']
                user.is_superuser = role == 'ADMIN'
                
                # Create or update UserProfile
                from reports.models import UserProfile
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.role = role
                profile.full_name = f"{user.first_name} {user.last_name}".strip() or user.username
                profile.save()
                
                logger.info(f"User profile {'created' if created else 'updated'} for {user.username} with role {role}")
            
            user.save()
            
            logger.info(f"User updated: {user.username}")
            return Response({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'message': 'User updated successfully'
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, pk=None):
        """Partially update a user (PATCH)"""
        try:
            user = User.objects.get(pk=pk)
            
            # Update only provided fields
            if 'username' in request.data:
                user.username = request.data['username']
            if 'email' in request.data:
                user.email = request.data['email']
            if 'first_name' in request.data:
                user.first_name = request.data['first_name']
            if 'last_name' in request.data:
                user.last_name = request.data['last_name']
            if 'is_active' in request.data:
                user.is_active = request.data['is_active']
            
            # Update password if provided
            if 'password' in request.data and request.data['password']:
                user.set_password(request.data['password'])
            
            # Update role
            if 'role' in request.data:
                role = request.data['role']
                user.is_staff = role in ['ADMIN', 'MANAGER']
                user.is_superuser = role == 'ADMIN'
                
                # Create or update UserProfile
                from reports.models import UserProfile
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.role = role
                profile.full_name = f"{user.first_name} {user.last_name}".strip() or user.username
                profile.save()
                
                logger.info(f"User profile {'created' if created else 'updated'} for {user.username} with role {role}")
            
            user.save()
            
            logger.info(f"User partially updated: {user.username}")
            return Response({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'message': 'User updated successfully'
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error partially updating user: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        """Delete a user"""
        try:
            user = User.objects.get(pk=pk)
            username = user.username
            user.delete()
            
            logger.info(f"User deleted: {username}")
            return Response({
                'message': f'User {username} deleted successfully'
            }, status=status.HTTP_204_NO_CONTENT)
            
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


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