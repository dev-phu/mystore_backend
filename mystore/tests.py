from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from mystore.models import User, Product, Cart, Order, OrderItem


class AuthTests(TestCase):
    """Tests for user registration and login."""

    def setUp(self):
        self.client = APIClient()

    def test_register_buyer(self):
        """Buyer registration should succeed and return 201."""
        res = self.client.post("/api/register/", {
            "username": "buyer1",
            "password": "testpass123",
            "email": "buyer1@test.com",
            "role": "BUYER",
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["role"], "BUYER")

    def test_register_seller(self):
        """Seller registration should succeed and return 201."""
        res = self.client.post("/api/register/", {
            "username": "seller1",
            "password": "testpass123",
            "email": "seller1@test.com",
            "role": "SELLER",
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["role"], "SELLER")

    def test_register_duplicate_username(self):
        """Registering with a duplicate username should fail."""
        self.client.post("/api/register/", {
            "username": "dup_user",
            "password": "testpass123",
            "role": "BUYER",
        })
        res = self.client.post("/api/register/", {
            "username": "dup_user",
            "password": "testpass456",
            "role": "BUYER",
        })
        self.assertEqual(res.status_code, 400)

    def test_login_success(self):
        """Login with valid credentials should return JWT tokens."""
        User.objects.create_user(username="loginuser", password="testpass123", role="BUYER")
        res = self.client.post("/api/login/", {
            "username": "loginuser",
            "password": "testpass123",
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)

    def test_login_wrong_password(self):
        """Login with wrong password should return 401."""
        User.objects.create_user(username="loginuser2", password="testpass123", role="BUYER")
        res = self.client.post("/api/login/", {
            "username": "loginuser2",
            "password": "wrongpassword",
        })
        self.assertEqual(res.status_code, 401)


class ProfileTests(TestCase):
    """Tests for profile view and update."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="profileuser", password="testpass123", role="BUYER",
            email="profile@test.com", first_name="Test", last_name="User",
        )

    def test_get_profile_unauthenticated(self):
        """Unauthenticated request should return 401."""
        res = self.client.get("/api/profile/")
        self.assertEqual(res.status_code, 401)

    def test_get_profile_authenticated(self):
        """Authenticated request should return user profile data."""
        self.client.force_authenticate(user=self.user)
        res = self.client.get("/api/profile/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["username"], "profileuser")
        self.assertEqual(res.data["role"], "BUYER")

    def test_update_profile(self):
        """PUT should update first_name and last_name."""
        self.client.force_authenticate(user=self.user)
        res = self.client.put("/api/profile/", {
            "first_name": "Updated",
            "last_name": "Name",
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["first_name"], "Updated")
        self.assertEqual(res.data["last_name"], "Name")


class ProductTests(TestCase):
    """Tests for product CRUD operations."""

    def setUp(self):
        self.client = APIClient()
        self.seller = User.objects.create_user(username="seller", password="testpass123", role="SELLER")
        self.buyer = User.objects.create_user(username="buyer", password="testpass123", role="BUYER")

    def test_seller_create_product(self):
        """Seller should be able to create a product."""
        self.client.force_authenticate(user=self.seller)
        res = self.client.post("/api/products/", {
            "title": "Test Product",
            "description": "A test product",
            "unit_price": "99.99",
            "available_quantity": 10,
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["title"], "Test Product")

    def test_buyer_cannot_create_product(self):
        """Buyer should NOT be able to create a product."""
        self.client.force_authenticate(user=self.buyer)
        res = self.client.post("/api/products/", {
            "title": "Hacked Product",
            "unit_price": "10.00",
            "available_quantity": 5,
        })
        self.assertEqual(res.status_code, 403)

    def test_negative_price_rejected(self):
        """Product with negative price should be rejected."""
        self.client.force_authenticate(user=self.seller)
        res = self.client.post("/api/products/", {
            "title": "Bad Product",
            "unit_price": "-50.00",
            "available_quantity": 10,
        })
        self.assertEqual(res.status_code, 400)

    def test_negative_quantity_rejected(self):
        """Product with negative quantity should be rejected."""
        self.client.force_authenticate(user=self.seller)
        res = self.client.post("/api/products/", {
            "title": "Bad Product",
            "unit_price": "50.00",
            "available_quantity": -5,
        })
        self.assertEqual(res.status_code, 400)

    def test_list_products(self):
        """Anyone can list active products."""
        Product.objects.create(seller=self.seller, title="Shirt", unit_price=100, available_quantity=5)
        res = self.client.get("/api/products/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)

    def test_inactive_product_hidden(self):
        """Inactive products should not appear in the public listing."""
        Product.objects.create(seller=self.seller, title="Hidden", unit_price=100, available_quantity=5, is_active=False)
        res = self.client.get("/api/products/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 0)

    def test_search_products(self):
        """Search should filter by keyword in title."""
        Product.objects.create(seller=self.seller, title="Blue Shirt", unit_price=100, available_quantity=5)
        Product.objects.create(seller=self.seller, title="Red Hat", unit_price=80, available_quantity=3)
        res = self.client.get("/api/products/?search=shirt")
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["title"], "Blue Shirt")

    def test_seller_delete_product(self):
        """Delete should soft-delete (set is_active=False)."""
        self.client.force_authenticate(user=self.seller)
        product = Product.objects.create(seller=self.seller, title="To Delete", unit_price=100, available_quantity=5)
        res = self.client.delete(f"/api/products/mysellerproduct/{product.product_id}/")
        self.assertEqual(res.status_code, 200)
        product.refresh_from_db()
        self.assertFalse(product.is_active)


class CartTests(TestCase):
    """Tests for cart operations."""

    def setUp(self):
        self.client = APIClient()
        self.seller = User.objects.create_user(username="seller", password="testpass123", role="SELLER")
        self.buyer = User.objects.create_user(username="buyer", password="testpass123", role="BUYER")
        self.product = Product.objects.create(
            seller=self.seller, title="Cart Product", unit_price=Decimal("50.00"), available_quantity=10,
        )

    def test_add_to_cart(self):
        """Buyer should be able to add items to cart."""
        self.client.force_authenticate(user=self.buyer)
        res = self.client.post("/api/cart/", {"product_id": self.product.product_id, "quantity": 2})
        self.assertEqual(res.status_code, 201)

    def test_add_to_cart_exceeds_stock(self):
        """Adding more than available stock should fail."""
        self.client.force_authenticate(user=self.buyer)
        res = self.client.post("/api/cart/", {"product_id": self.product.product_id, "quantity": 999})
        self.assertEqual(res.status_code, 400)

    def test_seller_cannot_add_to_cart(self):
        """Seller should NOT be able to add to cart."""
        self.client.force_authenticate(user=self.seller)
        res = self.client.post("/api/cart/", {"product_id": self.product.product_id, "quantity": 1})
        self.assertEqual(res.status_code, 403)

    def test_view_cart(self):
        """Buyer should see their cart items."""
        self.client.force_authenticate(user=self.buyer)
        Cart.objects.create(buyer=self.buyer, product=self.product, quantity=3)
        res = self.client.get("/api/cart/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)

    def test_delete_cart_item(self):
        """Buyer should be able to remove items from cart."""
        self.client.force_authenticate(user=self.buyer)
        cart_item = Cart.objects.create(buyer=self.buyer, product=self.product, quantity=1)
        res = self.client.delete("/api/cart/", {"cart_id": cart_item.cart_id}, format="json")
        self.assertEqual(res.status_code, 204)


class CheckoutTests(TestCase):
    """Tests for the checkout flow."""

    def setUp(self):
        self.client = APIClient()
        self.seller = User.objects.create_user(username="seller", password="testpass123", role="SELLER")
        self.buyer = User.objects.create_user(username="buyer", password="testpass123", role="BUYER")
        self.product = Product.objects.create(
            seller=self.seller, title="Checkout Product", unit_price=Decimal("100.00"), available_quantity=5,
        )

    def test_checkout_success(self):
        """Checkout should create an order and reduce stock."""
        self.client.force_authenticate(user=self.buyer)
        Cart.objects.create(buyer=self.buyer, product=self.product, quantity=2)
        res = self.client.post("/api/orders/checkout/")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["total_amount"], "200.00")
        # Stock should be reduced
        self.product.refresh_from_db()
        self.assertEqual(self.product.available_quantity, 3)
        # Cart should be cleared
        self.assertEqual(Cart.objects.filter(buyer=self.buyer).count(), 0)

    def test_checkout_empty_cart(self):
        """Checkout with empty cart should fail."""
        self.client.force_authenticate(user=self.buyer)
        res = self.client.post("/api/orders/checkout/")
        self.assertEqual(res.status_code, 400)

    def test_checkout_insufficient_stock(self):
        """Checkout should fail if stock is insufficient."""
        self.client.force_authenticate(user=self.buyer)
        Cart.objects.create(buyer=self.buyer, product=self.product, quantity=999)
        res = self.client.post("/api/orders/checkout/")
        self.assertEqual(res.status_code, 400)
        # Stock should NOT change
        self.product.refresh_from_db()
        self.assertEqual(self.product.available_quantity, 5)

    def test_checkout_inactive_product(self):
        """Checkout should fail if product was deactivated."""
        self.client.force_authenticate(user=self.buyer)
        Cart.objects.create(buyer=self.buyer, product=self.product, quantity=1)
        self.product.is_active = False
        self.product.save()
        res = self.client.post("/api/orders/checkout/")
        self.assertEqual(res.status_code, 400)
        self.assertIn("no longer available", res.data["detail"])


class OrderTests(TestCase):
    """Tests for order history and seller order management."""

    def setUp(self):
        self.client = APIClient()
        self.seller = User.objects.create_user(username="seller", password="testpass123", role="SELLER")
        self.buyer = User.objects.create_user(username="buyer", password="testpass123", role="BUYER")
        self.product = Product.objects.create(
            seller=self.seller, title="Order Product", unit_price=Decimal("100.00"), available_quantity=10,
        )
        # Create an order with one item
        self.order = Order.objects.create(buyer=self.buyer, total_amount=Decimal("200.00"), status="paid")
        self.order_item = OrderItem.objects.create(
            order=self.order, product=self.product, quantity=2, unit_price=Decimal("100.00"),
        )
        # Simulate stock deduction from checkout
        self.product.available_quantity -= 2
        self.product.save()

    def test_buyer_order_history(self):
        """Buyer should see their own order history."""
        self.client.force_authenticate(user=self.buyer)
        res = self.client.get("/api/orders/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(len(res.data[0]["items"]), 1)

    def test_seller_cannot_view_buyer_orders(self):
        """Seller should NOT be able to access buyer order history endpoint."""
        self.client.force_authenticate(user=self.seller)
        res = self.client.get("/api/orders/")
        self.assertEqual(res.status_code, 403)

    def test_seller_view_sold_items(self):
        """Seller should see items sold from their products."""
        self.client.force_authenticate(user=self.seller)
        res = self.client.get("/api/orders/mysellerorders/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["buyer_name"], "buyer")

    def test_seller_update_status(self):
        """Seller should be able to update order item status."""
        self.client.force_authenticate(user=self.seller)
        res = self.client.patch(
            f"/api/orders/mysellerorders/{self.order_item.order_item_id}/",
            {"status": "shipped"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.status, "shipped")

    def test_seller_invalid_status_rejected(self):
        """Invalid status value should be rejected."""
        self.client.force_authenticate(user=self.seller)
        res = self.client.patch(
            f"/api/orders/mysellerorders/{self.order_item.order_item_id}/",
            {"status": "HACKED_STATUS"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)

    def test_cancel_restores_stock(self):
        """Cancelling an order item should restore product stock."""
        self.client.force_authenticate(user=self.seller)
        res = self.client.patch(
            f"/api/orders/mysellerorders/{self.order_item.order_item_id}/",
            {"status": "cancelled"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        # Stock should be restored
        self.product.refresh_from_db()
        self.assertEqual(self.product.available_quantity, 10)
        # Order total should be reduced
        self.order.refresh_from_db()
        self.assertEqual(self.order.total_amount, Decimal("0.00"))

    def test_cancel_twice_fails(self):
        """Cannot cancel an already cancelled item."""
        self.client.force_authenticate(user=self.seller)
        self.order_item.status = "cancelled"
        self.order_item.save()
        res = self.client.patch(
            f"/api/orders/mysellerorders/{self.order_item.order_item_id}/",
            {"status": "cancelled"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)
