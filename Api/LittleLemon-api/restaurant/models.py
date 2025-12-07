from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class Category(models.Model):
    """
    Model representing a menu category.
    """
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=255, db_index=True)

    class Meta:
        ordering = ['title']
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.title


class Menu(models.Model):
    """
    Model representing a menu item at Little Lemon Restaurant.
    """
    title = models.CharField(max_length=255, db_index=True)
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    featured = models.BooleanField(default=False, db_index=True, help_text="Item of the day")
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='menu_items',
        null=True,
        blank=True
    )
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        verbose_name = 'Menu Item'
        verbose_name_plural = 'Menu Items'

    def __str__(self):
        return f"{self.title} - ${self.price}"


class Cart(models.Model):
    """
    Model representing items in a customer's shopping cart.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    menuitem = models.ForeignKey(
        Menu,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    quantity = models.SmallIntegerField(
        validators=[MinValueValidator(1)],
        default=1
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    class Meta:
        unique_together = ['user', 'menuitem']
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'

    def __str__(self):
        return f"{self.user.username} - {self.menuitem.title} x{self.quantity}"


class Order(models.Model):
    """
    Model representing a customer order.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    delivery_crew = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='deliveries',
        null=True,
        blank=True
    )
    status = models.BooleanField(default=False, db_index=True, help_text="False=pending, True=delivered")
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    date = models.DateField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'

    def __str__(self):
        return f"Order #{self.id} - {self.user.username} - ${self.total}"


class OrderItem(models.Model):
    """
    Model representing individual items within an order.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    menuitem = models.ForeignKey(
        Menu,
        on_delete=models.CASCADE
    )
    quantity = models.SmallIntegerField(
        validators=[MinValueValidator(1)]
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    class Meta:
        unique_together = ['order', 'menuitem']
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'

    def __str__(self):
        return f"{self.menuitem.title} x{self.quantity} (Order #{self.order.id})"


class Reservation(models.Model):
    """
    Model representing a table reservation at Little Lemon Restaurant.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reservations',
        help_text="User who made the reservation"
    )
    name = models.CharField(
        max_length=255,
        help_text="Name for the reservation"
    )
    number_of_guests = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Number of guests for the reservation"
    )
    reservation_date = models.DateField(
        help_text="Date of the reservation"
    )
    reservation_time = models.TimeField(
        help_text="Time of the reservation"
    )
    special_requests = models.TextField(
        blank=True,
        default='',
        help_text="Any special requests or dietary restrictions"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-reservation_date', '-reservation_time']
        verbose_name = 'Reservation'
        verbose_name_plural = 'Reservations'
        # Ensure the same user cannot book the same date/time twice
        unique_together = ['user', 'reservation_date', 'reservation_time']

    def __str__(self):
        return f"{self.name} - {self.reservation_date} at {self.reservation_time} ({self.number_of_guests} guests)"
