from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer that includes essential user permissions"""

    @classmethod
    def get_token(cls, user):
        """Add custom claims to the token"""
        token = super().get_token(user)

        # Add only essential user info
        token["username"] = user.username
        token["is_staff"] = user.is_staff
        token["is_superuser"] = user.is_superuser

        # Import here to avoid circular imports
        from permissions.models import UserRole

        # Add user role (essential for frontend authorization)
        try:
            user_role = UserRole.objects.get(user=user, is_active=True)
            token["role"] = user_role.role
        except UserRole.DoesNotExist:
            token["role"] = "user"  # Default role

        # Add accessible property IDs only (not all data)
        from permissions.models import PropertyAccess

        accessible_properties = list(
            PropertyAccess.objects.filter(user=user, is_active=True).values_list(
                "property_id", flat=True
            )
        )
        token["accessible_properties"] = accessible_properties

        # Add resource permissions (for clients, guards, etc.)
        from permissions.models import ResourcePermission

        resource_permissions = {}
        permissions_qs = ResourcePermission.objects.filter(
            user=user, is_active=True
        ).values("resource_type", "action")

        for perm in permissions_qs:
            resource_type = perm["resource_type"]
            action = perm["action"]
            if resource_type not in resource_permissions:
                resource_permissions[resource_type] = []
            if action not in resource_permissions[resource_type]:
                resource_permissions[resource_type].append(action)

        token["resource_permissions"] = resource_permissions

        # Add admin status for quick frontend checks
        token["is_admin"] = user.is_superuser or (
            user_role.role == "admin" if "user_role" in locals() else False
        )

        return token

    def validate(self, attrs):
        """Validate credentials and return tokens"""
        return super().validate(attrs)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token obtain view"""

    serializer_class = CustomTokenObtainPairSerializer
