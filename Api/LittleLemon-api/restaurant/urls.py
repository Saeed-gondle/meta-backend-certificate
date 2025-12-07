from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, MenuViewSet, CartViewSet, OrderViewSet,
    ManagerGroupViewSet, DeliveryCrewGroupViewSet, ReservationViewSet
)

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'menu-items', MenuViewSet, basename='menu')
router.register(r'cart/menu-items', CartViewSet, basename='cart')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'reservations', ReservationViewSet, basename='reservation')

# The API URLs are determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    
    # Group management endpoints
    path('groups/manager/users/', ManagerGroupViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='manager-group-list'),
    path('groups/manager/users/<int:pk>/', ManagerGroupViewSet.as_view({
        'delete': 'destroy'
    }), name='manager-group-detail'),
    
    path('groups/delivery-crew/users/', DeliveryCrewGroupViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='delivery-crew-list'),
    path('groups/delivery-crew/users/<int:pk>/', DeliveryCrewGroupViewSet.as_view({
        'delete': 'destroy'
    }), name='delivery-crew-detail'),
]
