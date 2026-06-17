import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from Authentication.authentication import SessionJWTAuthentication
from Authentication.permissions import IsOwner, IsOwnerOrManager
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import User, EmployeeInvitation
from ..serializers import (
    EmployeeInviteSerializer,
    EmployeeSetupSerializer,
    EmployeeRoleChangeSerializer,
)
from ..utils import Util
from ..renderers import UserRenderer

from drf_spectacular.utils import extend_schema


@extend_schema(tags=["Employee Management"],description="Only Admin, Owner or Manager can invite an employee")
class EmployeeInviteView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, IsOwnerOrManager]
    authentication_classes = [SessionJWTAuthentication]
    serializer_class = EmployeeInviteSerializer

    @extend_schema(
        request=EmployeeInviteSerializer,
        responses={201: {'description': 'Invitation sent successfully'}}
    )
    def post(self, request):
        dt = request.data
        serializer = EmployeeInviteSerializer(data=dt)

        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data.get('email')
            role = serializer.validated_data.get('role')
            invited_by = request.user

            # Role-based permission check:
            # Only owner or admin can invite another owner
            if role == 'owner' and invited_by.role != 'owner' and not invited_by.is_superuser:
                return Response(
                    {'error': 'Only owners or admin can invite other owners'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Generate secure token
            token = secrets.token_urlsafe(48)

            # Set expiration (e.g., 7 days from now)
            expires_at = timezone.now() + timedelta(days=7)

            # Create invitation record
            invitation = EmployeeInvitation.objects.create(
                email=email,
                role=role,
                invited_by=invited_by,
                token=token,
                expires_at=expires_at,
            )

            # Send invitation email
            setup_link = f"{settings.FRONTEND_URL}/employee/setup/{token}/"

            email_data = {
                'email_subject': f'You are invited as {role.capitalize()}',
                'email_body': (
                    f'You have been invited to join as a {role.capitalize()}.\n\n'
                    f'Click the link below to set up your account:\n{setup_link}\n\n'
                    f'This invitation will expire in 7 days.'
                ),
                'to_email': email,
                'context': {
                    'subject': f'Invitation to join as {role.capitalize()}',
                    'body': (
                        f'You have been invited to join as a {role.capitalize()}. '
                        f'Click the button below to set up your account.'
                    ),
                    'cta_url': setup_link,
                    'cta_text': 'Accept Invitation',
                }
            }
            Util.send_email(email_data)

            return Response(
                {
                    'message': f'Invitation sent successfully to {email}',
                    'role': role,
                    'email': email,
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Employee Management"])
class EmployeeSetupView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [AllowAny]
    serializer_class = EmployeeSetupSerializer

    @extend_schema(
        request=EmployeeSetupSerializer,
        responses={201: {'description': 'Account created successfully'}}
    )
    def post(self, request, token):
        # Validate token and find invitation
        try:
            invitation = EmployeeInvitation.objects.get(
                token=token,
                is_used=False
            )
        except EmployeeInvitation.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired invitation token'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if invitation is expired
        if invitation.is_expired():
            return Response(
                {'error': 'Invitation has expired. Please request a new invitation.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = EmployeeSetupSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            name = serializer.validated_data.get('name')
            password = serializer.validated_data.get('password')

            # Check if user already exists (e.g., existing customer)
            existing_user = User.objects.filter(email=invitation.email).first()

            if existing_user:
                # Upgrade existing customer to employee role
                existing_user.role = invitation.role
                existing_user.is_active = True  # Ensure active
                existing_user.name = name
                existing_user.set_password(password)
                existing_user.save()
                user = existing_user

                # Logout all existing sessions for security
                from ..utils import logout_all_user_sessions
                logout_all_user_sessions(user)

                message = 'Your account has been upgraded to employee. You can now log in with your new password.'
                status_code = status.HTTP_200_OK
            else:
                # Create new user with the invitation's email and role
                user = User.objects.create_user(
                    name=name,
                    email=invitation.email,
                    password=password
                )
                user.role = invitation.role
                user.is_active = True  # No email verification needed
                user.save()
                message = 'Account created successfully. You can now log in.'
                status_code = status.HTTP_201_CREATED

            # Mark invitation as used
            invitation.is_used = True
            invitation.save()

            return Response(
                {
                    'message': message,
                    'email': user.email,
                    'role': user.role,
                    'name': user.name,
                },
                status=status_code
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Employee Management"], description="Only Admin, Owner and Manager can change employee roles. Only Admin can promote or change owner role.")
class EmployeeRoleChangeView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, IsOwnerOrManager]
    authentication_classes = [SessionJWTAuthentication]
    serializer_class = EmployeeRoleChangeSerializer

    @extend_schema(
        request=EmployeeRoleChangeSerializer,
        responses={200: {'description': 'Role updated successfully'}}
    )
    def patch(self, request, user_id):
        """Change an employee's role"""
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EmployeeRoleChangeSerializer(
            data=request.data,
            context={
                'request': request,
                'target_user': target_user,
            }
        )

        if serializer.is_valid(raise_exception=True):
            new_role = serializer.validated_data.get('role')

            # Save new role
            old_role = target_user.role
            target_user.role = new_role
            target_user.save()

            # Logout all sessions for security when role changes
            from ..utils import logout_all_user_sessions
            logout_all_user_sessions(target_user)

            return Response(
                {
                    'message': f'Role changed from {old_role} to {new_role} successfully',
                    'user_id': target_user.id,
                    'email': target_user.email,
                    'name': target_user.name,
                    'old_role': old_role,
                    'new_role': new_role,
                },
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Employee Management"], description="Only Admin, Owner and Manager can list employees.")
class EmployeeListView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, IsOwnerOrManager]
    authentication_classes = [SessionJWTAuthentication]

    def get(self, request):
        """List all employees (non-customer users)"""
        employees = User.objects.exclude(
            role__in=['customer']
        ).exclude(
            is_superuser=True
        ).order_by('role', 'name')

        data = [
            {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'role': user.role,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat(),
            }
            for user in employees
        ]

        return Response(data, status=status.HTTP_200_OK)