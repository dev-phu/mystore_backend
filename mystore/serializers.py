from rest_framework import serializers
from .models import Product
from django.contrib.auth import get_user_model

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'role')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            role=validated_data.get('role', 'BUYER')
        )
        return user

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ('seller',)

from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source='product.title', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ('order_item_id', 'product', 'product_title', 'quantity', 'unit_price')

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True) # ดึง OrderItem ที่ผูกกับบิลนี้มาแสดงด้วย

    class Meta:
        model = Order
        fields = ('order_id', 'total_amount', 'status', 'create_at', 'items')
