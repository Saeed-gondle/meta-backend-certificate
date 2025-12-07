from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404
from decimal import Decimal
from .models import Category, Menu, Cart, Order, OrderItem, Reservation
from .serializers import (
    CategorySerializer, MenuSerializer, CartSerializer, 
    OrderSerializer, OrderItemSerializer, ReservationSerializer, UserSerializer
)
from .permissions import IsManager, IsDeliveryCrew, IsCustomer


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing categories.
    
    List: GET /api/categories/
    Retrieve: GET /api/categories/{id}/
    Create: POST /api/categories/ (Admin only)
    Update: PUT /api/categories/{id}/ (Admin only)
    Delete: DELETE /api/categories/{id}/ (Admin only)
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]


class MenuViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing menu items.
    
    Customers can:
    - Browse all menu items
    - Browse by category
    - Sort by price
    - Paginate results
    
    Admin can:
    - Create, update, delete menu items
    
    Managers can:
    - Update featured status (item of the day)
    """
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    filterset_fields = ['category', 'featured']
    search_fields = ['title', 'description']
    ordering_fields = ['price', 'title']
    ordering = ['title']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action == 'update_featured':
            return [IsManager()]
        return [IsAdminUser()]

    @action(detail=True, methods=['patch'], permission_classes=[IsManager])
    def update_featured(self, request, pk=None):
        """
        Managers can update the item of the day (featured status).
        PATCH /api/menu/{id}/update_featured/
        """
        menu_item = self.get_object()
        featured = request.data.get('featured', None)
        
        if featured is None:
            return Response(
                {'error': 'featured field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        menu_item.featured = bool(featured)
        menu_item.save()
        
        serializer = self.get_serializer(menu_item)
        return Response(serializer.data)


class CartViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing shopping cart.
    
    Customers can:
    - Add items to cart
    - View cart items
    - Update cart item quantity
    - Delete cart items
    """
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Users see only their own cart items"""
        return Cart.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Automatically set user when adding to cart"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """
        Clear all items from cart.
        DELETE /api/cart/clear/
        """
        Cart.objects.filter(user=request.user).delete()
        return Response(
            {'message': 'Cart cleared successfully'},
            status=status.HTTP_204_NO_CONTENT
        )


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing orders.
    
    Customers can:
    - Place orders (create from cart)
    - View their own orders
    
    Managers can:
    - View all orders
    - Assign orders to delivery crew
    
    Delivery crew can:
    - View orders assigned to them
    - Update order status to delivered
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'date']
    ordering_fields = ['date', 'total']
    ordering = ['-date']
    
    def get_queryset(self):
        """
        Filter orders based on user role:
        - Customers see only their orders
        - Delivery crew see orders assigned to them
        - Managers see all orders
        """
        user = self.request.user
        
        if user.is_staff or user.groups.filter(name='Manager').exists():
            return Order.objects.all()
        elif user.groups.filter(name='Delivery crew').exists():
            return Order.objects.filter(delivery_crew=user)
        else:
            return Order.objects.filter(user=user)
    
    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update']:
            return [IsManager() | IsDeliveryCrew()]
        elif self.action == 'assign_delivery_crew':
            return [IsManager()]
        return [IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        """
        Create order from cart items.
        POST /api/orders/
        """
        # Get user's cart items
        cart_items = Cart.objects.filter(user=request.user)
        
        if not cart_items.exists():
            return Response(
                {'error': 'Cart is empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate total
        total = sum(item.price for item in cart_items)
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            total=total
        )
        
        # Create order items from cart
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                menuitem=cart_item.menuitem,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                price=cart_item.price
            )
        
        # Clear cart
        cart_items.delete()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """
        Update order.
        Managers can update delivery_crew and status.
        Delivery crew can only update status.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        user = request.user
        
        # Delivery crew can only update status
        if user.groups.filter(name='Delivery crew').exists() and not user.is_staff:
            if 'delivery_crew' in request.data:
                return Response(
                    {'error': 'Delivery crew cannot assign orders'},
                    status=status.HTTP_403_FORBIDDEN
                )
            # Only allow status update
            allowed_data = {'status': request.data.get('status')}
            serializer = self.get_serializer(instance, data=allowed_data, partial=True)
        else:
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsManager])
    def assign_delivery_crew(self, request, pk=None):
        """
        Managers assign delivery crew to an order.
        PATCH /api/orders/{id}/assign_delivery_crew/
        Body: {"delivery_crew_id": <user_id>}
        """
        order = self.get_object()
        delivery_crew_id = request.data.get('delivery_crew_id')
        
        if not delivery_crew_id:
            return Response(
                {'error': 'delivery_crew_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            delivery_user = User.objects.get(
                id=delivery_crew_id,
                groups__name='Delivery crew'
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found or not in delivery crew'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        order.delivery_crew = delivery_user
        order.save()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)


class ManagerGroupViewSet(viewsets.ViewSet):
    """
    ViewSet for managing the Manager group.
    Only admin can access.
    
    List managers: GET /api/groups/manager/users/
    Add to managers: POST /api/groups/manager/users/
    Remove from managers: DELETE /api/groups/manager/users/{userId}/
    """
    permission_classes = [IsAdminUser]
    
    def list(self, request):
        """List all users in Manager group"""
        manager_group, created = Group.objects.get_or_create(name='Manager')
        users = manager_group.user_set.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        """Add user to Manager group"""
        username = request.data.get('username')
        
        if not username:
            return Response(
                {'error': 'username is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        manager_group, created = Group.objects.get_or_create(name='Manager')
        manager_group.user_set.add(user)
        
        return Response(
            {'message': f'User {username} added to Manager group'},
            status=status.HTTP_201_CREATED
        )
    
    def destroy(self, request, pk=None):
        """Remove user from Manager group"""
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        manager_group, created = Group.objects.get_or_create(name='Manager')
        manager_group.user_set.remove(user)
        
        return Response(
            {'message': f'User {user.username} removed from Manager group'},
            status=status.HTTP_200_OK
        )


class DeliveryCrewGroupViewSet(viewsets.ViewSet):
    """
    ViewSet for managing the Delivery crew group.
    Only managers and admin can access.
    
    List delivery crew: GET /api/groups/delivery-crew/users/
    Add to delivery crew: POST /api/groups/delivery-crew/users/
    Remove from delivery crew: DELETE /api/groups/delivery-crew/users/{userId}/
    """
    permission_classes = [IsManager]
    
    def list(self, request):
        """List all users in Delivery crew group"""
        delivery_group, created = Group.objects.get_or_create(name='Delivery crew')
        users = delivery_group.user_set.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        """Add user to Delivery crew group"""
        username = request.data.get('username')
        
        if not username:
            return Response(
                {'error': 'username is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        delivery_group, created = Group.objects.get_or_create(name='Delivery crew')
        delivery_group.user_set.add(user)
        
        return Response(
            {'message': f'User {username} added to Delivery crew group'},
            status=status.HTTP_201_CREATED
        )
    
    def destroy(self, request, pk=None):
        """Remove user from Delivery crew group"""
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        delivery_group, created = Group.objects.get_or_create(name='Delivery crew')
        delivery_group.user_set.remove(user)
        
        return Response(
            {'message': f'User {user.username} removed from Delivery crew group'},
            status=status.HTTP_200_OK
        )


class ReservationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing reservations.
    """
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Users see only their own reservations, admin sees all"""
        user = self.request.user
        if user.is_staff:
            return Reservation.objects.all()
        return Reservation.objects.filter(user=user)

    def perform_create(self, serializer):
        """Automatically set user when creating reservation"""
        serializer.save(user=self.request.user)
