from django.contrib import admin
from .models import Category, Menu, Cart, Order, OrderItem, Reservation


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title']


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'category', 'featured', 'created_at']
    list_filter = ['category', 'featured', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['title']
    list_editable = ['featured']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'menuitem', 'quantity', 'unit_price', 'price']
    list_filter = ['user']
    search_fields = ['user__username', 'menuitem__title']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['menuitem', 'quantity', 'unit_price', 'price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total', 'status', 'delivery_crew', 'date']
    list_filter = ['status', 'date', 'delivery_crew']
    search_fields = ['user__username', 'delivery_crew__username']
    ordering = ['-date']
    inlines = [OrderItemInline]
    list_editable = ['status', 'delivery_crew']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'menuitem', 'quantity', 'unit_price', 'price']
    list_filter = ['order']
    search_fields = ['menuitem__title', 'order__user__username']


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'reservation_date', 'reservation_time', 'number_of_guests', 'created_at']
    list_filter = ['reservation_date', 'created_at']
    search_fields = ['name', 'user__username', 'special_requests']
    ordering = ['-reservation_date', '-reservation_time']
    date_hierarchy = 'reservation_date'
