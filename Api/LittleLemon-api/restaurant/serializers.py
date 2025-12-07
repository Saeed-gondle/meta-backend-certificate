from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Category, Menu, Cart, Order, OrderItem, Reservation
from datetime import date, time


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model.
    """
    class Meta:
        model = Category
        fields = ['id', 'slug', 'title']


class MenuSerializer(serializers.ModelSerializer):
    """
    Serializer for Menu model.
    Handles serialization and deserialization of menu items.
    """
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Menu
        fields = ['id', 'title', 'price', 'featured', 'category', 'category_id', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_price(self, value):
        """Ensure price is positive"""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value


class CartSerializer(serializers.ModelSerializer):
    """
    Serializer for Cart model.
    """
    user = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    menuitem = serializers.PrimaryKeyRelatedField(
        queryset=Menu.objects.all()
    )
    menuitem_title = serializers.CharField(source='menuitem.title', read_only=True)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'menuitem', 'menuitem_title', 'quantity', 'unit_price', 'price']
        read_only_fields = ['id', 'user', 'unit_price', 'price']

    def validate_quantity(self, value):
        """Ensure quantity is at least 1"""
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1")
        return value

    def create(self, validated_data):
        """Automatically calculate unit_price and price"""
        menuitem = validated_data['menuitem']
        quantity = validated_data['quantity']
        validated_data['unit_price'] = menuitem.price
        validated_data['price'] = menuitem.price * quantity
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Recalculate price when quantity changes"""
        if 'quantity' in validated_data:
            instance.quantity = validated_data['quantity']
            instance.price = instance.unit_price * instance.quantity
        if 'menuitem' in validated_data:
            instance.menuitem = validated_data['menuitem']
            instance.unit_price = instance.menuitem.price
            instance.price = instance.unit_price * instance.quantity
        instance.save()
        return instance


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for OrderItem model.
    """
    menuitem_title = serializers.CharField(source='menuitem.title', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'menuitem', 'menuitem_title', 'quantity', 'unit_price', 'price']
        read_only_fields = ['id', 'unit_price', 'price']


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for Order model.
    """
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    order_items = OrderItemSerializer(many=True, read_only=True)
    delivery_crew = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(groups__name='Delivery crew'),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Order
        fields = ['id', 'user', 'username', 'delivery_crew', 'status', 'total', 'date', 'order_items']
        read_only_fields = ['id', 'user', 'username', 'total', 'date', 'order_items']


class ReservationSerializer(serializers.ModelSerializer):
    """
    Serializer for Reservation model.
    Handles serialization and deserialization of table reservations.
    """
    user = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Reservation
        fields = [
            'id', 
            'user', 
            'username',
            'name', 
            'number_of_guests', 
            'reservation_date', 
            'reservation_time', 
            'special_requests',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'username', 'created_at', 'updated_at']

    def validate_number_of_guests(self, value):
        """Ensure number of guests is at least 1 and reasonable"""
        if value < 1:
            raise serializers.ValidationError("Number of guests must be at least 1")
        if value > 20:
            raise serializers.ValidationError("Number of guests cannot exceed 20. Please contact us for larger parties.")
        return value

    def validate_reservation_date(self, value):
        """Ensure reservation is not in the past"""
        if value < date.today():
            raise serializers.ValidationError("Reservation date cannot be in the past")
        return value

    def validate(self, attrs):
        """
        Additional validation for reservation date and time combination
        """
        reservation_date = attrs.get('reservation_date')
        reservation_time = attrs.get('reservation_time')

        # Check if reservation is for today and time has passed
        if reservation_date == date.today():
            from datetime import datetime
            current_time = datetime.now().time()
            if reservation_time < current_time:
                raise serializers.ValidationError({
                    'reservation_time': 'Reservation time cannot be in the past'
                })

        # Check business hours (example: 11:00 AM to 10:00 PM)
        opening_time = time(11, 0)
        closing_time = time(22, 0)
        if reservation_time < opening_time or reservation_time > closing_time:
            raise serializers.ValidationError({
                'reservation_time': 'Reservations are only available between 11:00 AM and 10:00 PM'
            })

        return attrs


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    Used for user registration and profile information.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']
