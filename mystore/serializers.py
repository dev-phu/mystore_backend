from rest_framework import serializers
from .models import Product, Cart, Order, OrderItem
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "password", "email", "role")

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
            role=validated_data.get("role", "BUYER"),
        )
        return user


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ("seller",)

    def validate_unit_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value

    def validate_available_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative.")
        return value


class CartSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Cart
        fields = ("cart_id", "product", "quantity")


class OrderItemSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source="product.title", read_only=True)

    class Meta:
        model = OrderItem
        fields = ("order_item_id", "product", "product_title", "quantity", "unit_price", "status")


class SellerOrderItemSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source="product.title", read_only=True)
    buyer_name = serializers.CharField(source="order.buyer.username", read_only=True)
    order_date = serializers.DateTimeField(source="order.create_at", read_only=True)
    order_id = serializers.IntegerField(source="order.order_id", read_only=True)

    class Meta:
        model = OrderItem
        fields = ("order_item_id", "order_id", "product", "product_title", "quantity", "unit_price", "status", "buyer_name", "order_date")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(
        many=True, read_only=True
    )  # ดึง OrderItem ที่ผูกกับบิลนี้มาแสดงด้วย

    class Meta:
        model = Order
        fields = ("order_id", "total_amount", "status", "create_at", "items")
