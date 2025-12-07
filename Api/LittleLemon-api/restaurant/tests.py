from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from decimal import Decimal
from datetime import date, time, timedelta
from .models import Menu, Reservation


class MenuModelTest(TestCase):
    """Test cases for Menu model"""
    
    def setUp(self):
        self.menu_item = Menu.objects.create(
            title="Greek Salad",
            price=Decimal('12.99'),
            inventory=50,
            description="Fresh salad with feta cheese",
            category="Appetizer"
        )

    def test_menu_creation(self):
        """Test menu item creation"""
        self.assertEqual(self.menu_item.title, "Greek Salad")
        self.assertEqual(self.menu_item.price, Decimal('12.99'))
        self.assertEqual(self.menu_item.inventory, 50)

    def test_menu_string_representation(self):
        """Test string representation of menu item"""
        self.assertEqual(str(self.menu_item), "Greek Salad - $12.99")


class ReservationModelTest(TestCase):
    """Test cases for Reservation model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.reservation = Reservation.objects.create(
            user=self.user,
            name="John Doe",
            number_of_guests=4,
            reservation_date=date.today() + timedelta(days=1),
            reservation_time=time(18, 30),
            special_requests="Window seat please"
        )

    def test_reservation_creation(self):
        """Test reservation creation"""
        self.assertEqual(self.reservation.name, "John Doe")
        self.assertEqual(self.reservation.number_of_guests, 4)
        self.assertEqual(self.reservation.user, self.user)

    def test_reservation_string_representation(self):
        """Test string representation of reservation"""
        expected = f"John Doe - {self.reservation.reservation_date} at 18:30:00 (4 guests)"
        self.assertEqual(str(self.reservation), expected)


class MenuAPITest(APITestCase):
    """Test cases for Menu API endpoints"""
    
    def setUp(self):
        # Create regular user
        self.user = User.objects.create_user(
            username='regularuser',
            password='testpass123'
        )
        self.user_token = Token.objects.create(user=self.user)
        
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True
        )
        self.admin_token = Token.objects.create(user=self.admin)
        
        # Create menu items
        self.menu1 = Menu.objects.create(
            title="Bruschetta",
            price=Decimal('8.99'),
            inventory=30,
            description="Grilled bread with tomatoes",
            category="Appetizer"
        )
        self.menu2 = Menu.objects.create(
            title="Lemon Dessert",
            price=Decimal('6.99'),
            inventory=25,
            description="Our signature lemon dessert",
            category="Dessert"
        )
        
        self.client = APIClient()

    def test_get_menu_list_unauthenticated(self):
        """Test that unauthenticated users can view menu"""
        response = self.client.get('/api/menu/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_get_menu_item_detail(self):
        """Test retrieving a single menu item"""
        response = self.client.get(f'/api/menu/{self.menu1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Bruschetta')

    def test_create_menu_item_as_admin(self):
        """Test that admin can create menu items"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        data = {
            'title': 'Pasta Carbonara',
            'price': '15.99',
            'inventory': 20,
            'description': 'Classic Italian pasta',
            'category': 'Main Course'
        }
        response = self.client.post('/api/menu/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Menu.objects.count(), 3)

    def test_create_menu_item_as_regular_user_fails(self):
        """Test that regular users cannot create menu items"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user_token.key)
        data = {
            'title': 'New Item',
            'price': '10.99',
            'inventory': 10
        }
        response = self.client.post('/api/menu/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_menu_item_as_admin(self):
        """Test that admin can update menu items"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        data = {
            'title': 'Bruschetta',
            'price': '9.99',
            'inventory': 35,
            'description': 'Updated description',
            'category': 'Appetizer'
        }
        response = self.client.put(f'/api/menu/{self.menu1.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.menu1.refresh_from_db()
        self.assertEqual(self.menu1.price, Decimal('9.99'))

    def test_delete_menu_item_as_admin(self):
        """Test that admin can delete menu items"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        response = self.client.delete(f'/api/menu/{self.menu1.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Menu.objects.count(), 1)

    def test_delete_menu_item_as_regular_user_fails(self):
        """Test that regular users cannot delete menu items"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user_token.key)
        response = self.client.delete(f'/api/menu/{self.menu1.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ReservationAPITest(APITestCase):
    """Test cases for Reservation API endpoints"""
    
    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(
            username='user1',
            password='pass123'
        )
        self.user1_token = Token.objects.create(user=self.user1)
        
        self.user2 = User.objects.create_user(
            username='user2',
            password='pass123'
        )
        self.user2_token = Token.objects.create(user=self.user2)
        
        self.admin = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True
        )
        self.admin_token = Token.objects.create(user=self.admin)
        
        # Create reservations
        self.reservation1 = Reservation.objects.create(
            user=self.user1,
            name="Alice Smith",
            number_of_guests=2,
            reservation_date=date.today() + timedelta(days=1),
            reservation_time=time(19, 0)
        )
        
        self.client = APIClient()

    def test_get_reservations_authenticated(self):
        """Test that authenticated users can view their reservations"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user1_token.key)
        response = self.client.get('/api/reservations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_get_reservations_unauthenticated_fails(self):
        """Test that unauthenticated users cannot view reservations"""
        response = self.client.get('/api/reservations/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_reservation(self):
        """Test creating a new reservation"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user1_token.key)
        data = {
            'name': 'Bob Johnson',
            'number_of_guests': 4,
            'reservation_date': str(date.today() + timedelta(days=2)),
            'reservation_time': '20:00:00',
            'special_requests': 'Vegetarian menu'
        }
        response = self.client.post('/api/reservations/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.count(), 2)

    def test_user_cannot_see_other_user_reservations(self):
        """Test that users can only see their own reservations"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user2_token.key)
        response = self.client.get('/api/reservations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_admin_can_see_all_reservations(self):
        """Test that admin users can see all reservations"""
        # Create reservation for user2
        Reservation.objects.create(
            user=self.user2,
            name="User2 Reservation",
            number_of_guests=3,
            reservation_date=date.today() + timedelta(days=3),
            reservation_time=time(18, 0)
        )
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        response = self.client.get('/api/reservations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_user_can_update_own_reservation(self):
        """Test that users can update their own reservations"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user1_token.key)
        data = {
            'name': 'Alice Smith Updated',
            'number_of_guests': 3,
            'reservation_date': str(date.today() + timedelta(days=1)),
            'reservation_time': '19:30:00'
        }
        response = self.client.patch(f'/api/reservations/{self.reservation1.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.reservation1.refresh_from_db()
        self.assertEqual(self.reservation1.number_of_guests, 3)

    def test_user_cannot_update_other_user_reservation(self):
        """Test that users cannot update other users' reservations"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user2_token.key)
        data = {'number_of_guests': 5}
        response = self.client.patch(f'/api/reservations/{self.reservation1.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_reservation_with_past_date_fails(self):
        """Test that creating a reservation with a past date fails"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user1_token.key)
        data = {
            'name': 'Test',
            'number_of_guests': 2,
            'reservation_date': str(date.today() - timedelta(days=1)),
            'reservation_time': '19:00:00'
        }
        response = self.client.post('/api/reservations/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AuthenticationTest(APITestCase):
    """Test cases for authentication"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )

    def test_user_registration(self):
        """Test user registration via Djoser"""
        data = {
            'username': 'newuser',
            'password': 'newpass123',
            'email': 'newuser@example.com'
        }
        response = self.client.post('/auth/users/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_token_authentication(self):
        """Test token generation"""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post('/auth/token/login/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('auth_token', response.data)

    def test_access_protected_endpoint_with_token(self):
        """Test accessing protected endpoint with valid token"""
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.get('/api/reservations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_access_protected_endpoint_without_token_fails(self):
        """Test that accessing protected endpoint without token fails"""
        response = self.client.get('/api/reservations/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
