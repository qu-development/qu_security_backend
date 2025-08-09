from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Guard, Client, Property, Shift, Expense

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with all fields"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login']
        read_only_fields = ['id', 'date_joined', 'last_login']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new user"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 
                 'password', 'password_confirm', 'is_active', 'is_staff']
        
    def validate(self, attrs):
        """Validate that passwords match"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        """Create a new user with encrypted password"""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user information"""
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'is_active', 'is_staff']


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include username and password')
        
        return attrs

class GuardSerializer(serializers.ModelSerializer):
    """Serializer for Guard model"""
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = Guard
        fields = ['id', 'user', 'user_details', 'phone']
        read_only_fields = ['id']


class GuardDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Guard model with user information"""
    user_details = UserSerializer(source='user', read_only=True)
    shifts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Guard
        fields = ['id', 'user', 'user_details', 'phone', 'shifts_count']
        read_only_fields = ['id']
    
    def get_shifts_count(self, obj):
        return obj.shifts.count()


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for Client model"""
    user_details = UserSerializer(source='user', read_only=True)

    class Meta:
        model = Client
        fields = ['id', 'user', 'user_details', 'phone', 'balance']
        read_only_fields = ['id', 'balance']


class ClientDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Client model with user information"""
    user_details = UserSerializer(source='user', read_only=True)
    properties_count = serializers.SerializerMethodField()
    total_expenses = serializers.SerializerMethodField()
    
    class Meta:
        model = Client
        fields = ['id', 'user', 'user_details', 'phone', 'balance', 'properties_count', 'total_expenses']
        read_only_fields = ['id', 'balance']
    
    def get_properties_count(self, obj):
        return obj.properties.count()
    
    def get_total_expenses(self, obj):
        from decimal import Decimal
        total = Decimal('0.00')
        for property_obj in obj.properties.all():
            for expense in property_obj.expenses.all():
                total += expense.amount
        return total


class PropertySerializer(serializers.ModelSerializer):
    """Serializer for Property model"""
    owner_details = ClientSerializer(source='owner', read_only=True)

    class Meta:
        model = Property
        fields = ['id', 'owner', 'owner_details', 'address', 'total_hours']
        read_only_fields = ['id', 'owner']


class PropertyDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Property model with owner information"""
    owner_details = ClientSerializer(source='owner', read_only=True)
    shifts_count = serializers.SerializerMethodField()
    expenses_count = serializers.SerializerMethodField()
    total_expenses_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = ['id', 'owner', 'owner_details', 'address', 'total_hours', 
                 'shifts_count', 'expenses_count', 'total_expenses_amount']
        read_only_fields = ['id', 'owner']
    
    def get_shifts_count(self, obj):
        return obj.shifts.count()
    
    def get_expenses_count(self, obj):
        return obj.expenses.count()
    
    def get_total_expenses_amount(self, obj):
        from decimal import Decimal
        total = Decimal('0.00')
        for expense in obj.expenses.all():
            total += expense.amount
        return total


class ShiftSerializer(serializers.ModelSerializer):
    """Serializer for Shift model"""
    guard_details = GuardSerializer(source='guard', read_only=True)
    property_details = PropertySerializer(source='property', read_only=True)

    class Meta:
        model = Shift
        fields = ['id', 'guard', 'guard_details', 'property', 'property_details', 
                 'start_time', 'end_time', 'hours_worked']
        read_only_fields = ['id']


class ExpenseSerializer(serializers.ModelSerializer):
    """Serializer for Expense model"""
    property_details = PropertySerializer(source='property', read_only=True)

    class Meta:
        model = Expense
        fields = ['id', 'property', 'property_details', 'description', 'amount']
        read_only_fields = ['id']