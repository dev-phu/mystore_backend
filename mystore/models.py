from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = (
        ("BUYER", "Buyer"),
        ("SELLER", "Seller"),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="BUYER")


# 2. ตาราง PRODUCTS
class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="products")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(
        upload_to="product_images/", blank=True, null=True
    )  # keep image
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2
    )  # เลข2หลักเพื่อจำนวนสินค้า
    available_quantity = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return self.title


# 3. ตาราง CARTS (ตะกร้าสินค้า)
class Cart(models.Model):
    cart_id = models.AutoField(primary_key=True)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"Cart: {self.buyer.username} - {self.product.title}"


# 4. ตาราง ORDERS (คำสั่งซื้อ)
class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=50, default="pending"
    )  # status pending, paid, shipped
    create_at = models.DateTimeField(
        auto_now_add=True
    )  # บันทึกเวลาปัจจุบันอัตโนมัติเมื่อสร้าง Order

    def __str__(self):
        return f"Order #{self.order_id} by {self.buyer.username}"


# 5. ตาราง ORDER_ITEMS (รายละเอียดสินค้าในคำสั่งซื้อนั้นๆ)
class OrderItem(models.Model):
    order_item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product, on_delete=models.RESTRICT
    )  # ป้องกันไม่ให้ลบสินค้าถ้ามีคนสั่งซื้อไปแล้ว
    quantity = models.IntegerField()
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2
    )  # เก็บราคา ณ วันที่ซื้อ (เผื่ออนาคตสินค้าปรับราคา)

    def __str__(self):
        return f"{self.quantity} x {self.product.title} (Order #{self.order.order_id})"
