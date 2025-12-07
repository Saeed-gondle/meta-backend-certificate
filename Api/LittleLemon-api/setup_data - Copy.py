# Setup script for Little Lemon API
# Run this after migrations to set up initial data

from django.contrib.auth.models import Group, User
from restaurant.models import Category, Menu

# Create user groups
print("Creating user groups...")
manager_group, created = Group.objects.get_or_create(name='Manager')
if created:
    print("✓ Manager group created")
else:
    print("✓ Manager group already exists")

delivery_group, created = Group.objects.get_or_create(name='Delivery crew')
if created:
    print("✓ Delivery crew group created")
else:
    print("✓ Delivery crew group already exists")

# Create sample categories
print("\nCreating sample categories...")
categories_data = [
    {'slug': 'appetizers', 'title': 'Appetizers'},
    {'slug': 'main-courses', 'title': 'Main Courses'},
    {'slug': 'desserts', 'title': 'Desserts'},
    {'slug': 'beverages', 'title': 'Beverages'},
]

for cat_data in categories_data:
    category, created = Category.objects.get_or_create(
        slug=cat_data['slug'],
        defaults={'title': cat_data['title']}
    )
    if created:
        print(f"✓ Created category: {category.title}")
    else:
        print(f"✓ Category already exists: {category.title}")

# Create sample menu items
print("\nCreating sample menu items...")
menu_items_data = [
    {
        'title': 'Greek Salad',
        'price': '12.99',
        'category_slug': 'appetizers',
        'description': 'Fresh mixed greens with feta cheese, olives, and Mediterranean dressing',
        'featured': False
    },
    {
        'title': 'Bruschetta',
        'price': '8.99',
        'category_slug': 'appetizers',
        'description': 'Grilled bread with fresh tomatoes, garlic, and basil',
        'featured': False
    },
    {
        'title': 'Grilled Salmon',
        'price': '24.99',
        'category_slug': 'main-courses',
        'description': 'Atlantic salmon with lemon butter sauce and seasonal vegetables',
        'featured': True
    },
    {
        'title': 'Pasta Carbonara',
        'price': '18.99',
        'category_slug': 'main-courses',
        'description': 'Classic Italian pasta with bacon, eggs, and Parmesan cheese',
        'featured': False
    },
    {
        'title': 'Lemon Dessert',
        'price': '7.99',
        'category_slug': 'desserts',
        'description': 'Our signature lemon cake with mascarpone cream',
        'featured': True
    },
    {
        'title': 'Tiramisu',
        'price': '8.99',
        'category_slug': 'desserts',
        'description': 'Traditional Italian coffee-flavored dessert',
        'featured': False
    },
    {
        'title': 'Fresh Lemonade',
        'price': '4.99',
        'category_slug': 'beverages',
        'description': 'House-made lemonade with fresh lemons',
        'featured': False
    },
    {
        'title': 'Italian Coffee',
        'price': '3.99',
        'category_slug': 'beverages',
        'description': 'Premium espresso or cappuccino',
        'featured': False
    },
]

for item_data in menu_items_data:
    category = Category.objects.get(slug=item_data['category_slug'])
    menu_item, created = Menu.objects.get_or_create(
        title=item_data['title'],
        defaults={
            'price': item_data['price'],
            'category': category,
            'description': item_data['description'],
            'featured': item_data['featured']
        }
    )
    if created:
        print(f"✓ Created menu item: {menu_item.title}")
    else:
        print(f"✓ Menu item already exists: {menu_item.title}")

print("\n✅ Setup complete!")
print("\nYou can now:")
print("1. Create test users via: python manage.py createsuperuser")
print("2. Run the server: python manage.py runserver")
print("3. Access the API at: http://127.0.0.1:8000/api/")
print("4. View API docs at: http://127.0.0.1:8000/api/docs/")
print("5. Access admin panel at: http://127.0.0.1:8000/admin/")
