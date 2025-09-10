# tests/test_app.py
import pytest
import json
import os
from app import app, LibrarySystem, Book, Member, DataManager

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    with app.test_client() as client:
        yield client

@pytest.fixture
def library_system():
    # Use a test data file
    test_data_file = 'test_library_data.json'
    if os.path.exists(test_data_file):
        os.remove(test_data_file)
    
    data_manager = DataManager(test_data_file)
    system = LibrarySystem()
    system.data_manager = data_manager
    yield system
    
    # Cleanup
    if os.path.exists(test_data_file):
        os.remove(test_data_file)

class TestBook:
    def test_book_creation(self):
        book = Book(1, "Test Book", "Test Author", "123456789", "Fiction")
        assert book.book_id == 1
        assert book.title == "Test Book"
        assert book.author == "Test Author"
        assert book.is_available == True
    
    def test_book_borrow(self):
        book = Book(1, "Test Book", "Test Author", "123456789")
        assert book.borrow(1) == True
        assert book.is_available == False
        assert book.borrow(2) == False  # Already borrowed
    
    def test_book_return(self):
        book = Book(1, "Test Book", "Test Author", "123456789")
        book.borrow(1)
        book.return_book()
        assert book.is_available == True

class TestMember:
    def test_member_creation(self):
        member = Member(1, "John Doe", "john@example.com")
        assert member.person_id == 1
        assert member.name == "John Doe"
        assert member.email == "john@example.com"
        assert member.can_borrow() == True
    
    def test_member_borrowing_limit(self):
        member = Member(1, "John Doe", "john@example.com")
        
        # Borrow 3 books (max limit)
        for i in range(3):
            assert member.borrow_book(i+1) == True
        
        # Try to borrow 4th book
        assert member.borrow_book(4) == False
        assert member.can_borrow() == False
    
    def test_member_return_book(self):
        member = Member(1, "John Doe", "john@example.com")
        member.borrow_book(1)
        member.return_book(1)
        
        borrowed_books = member.get_borrowed_books()
        assert len(borrowed_books) == 0

class TestLibrarySystem:
    def test_add_book(self, library_system):
        book = library_system.add_book("Test Book", "Test Author", "123456789", "Fiction")
        assert book.title == "Test Book"
        
        # Check if book is saved in data manager
        saved_book = library_system.data_manager.get_book(book.book_id)
        assert saved_book is not None
        assert saved_book['title'] == "Test Book"
    
    def test_add_member(self, library_system):
        member = library_system.add_member("John Doe", "john@example.com")
        assert member.name == "John Doe"
        
        # Check if member is saved in data manager
        saved_member = library_system.data_manager.get_member(member.person_id)
        assert saved_member is not None
        assert saved_member['name'] == "John Doe"
    
    def test_borrow_book_success(self, library_system):
        # Add book and member
        book = library_system.add_book("Test Book", "Test Author", "123456789")
        member = library_system.add_member("John Doe", "john@example.com")
        
        # Borrow book
        success, message = library_system.borrow_book(member.person_id, book.book_id)
        assert success == True
        assert "successfully" in message.lower()
        
        # Check book status
        book_data = library_system.data_manager.get_book(book.book_id)
        assert book_data['is_available'] == False
    
    def test_borrow_unavailable_book(self, library_system):
        # Add book and members
        book = library_system.add_book("Test Book", "Test Author", "123456789")
        member1 = library_system.add_member("John Doe", "john@example.com")
        member2 = library_system.add_member("Jane Doe", "jane@example.com")
        
        # First member borrows the book
        library_system.borrow_book(member1.person_id, book.book_id)
        
        # Second member tries to borrow the same book
        success, message = library_system.borrow_book(member2.person_id, book.book_id)
        assert success == False
        assert "not available" in message.lower()

class TestFlaskApp:
    def test_index_route(self, client):
        response = client.get('/')
        assert response.status_code == 200
        assert b'Library Management System' in response.data
    
    def test_books_route(self, client):
        response = client.get('/books')
        assert response.status_code == 200
        assert b'Books Collection' in response.data
    
    def test_add_book_get(self, client):
        response = client.get('/add_book')
        assert response.status_code == 200
        assert b'Add New Book' in response.data
    
    def test_add_book_post(self, client):
        response = client.post('/add_book', data={
            'title': 'Test Book',
            'author': 'Test Author',
            'isbn': '123456789',
            'category': 'Fiction'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Test Book' in response.data
    
    def test_members_route(self, client):
        response = client.get('/members')
        assert response.status_code == 200
        assert b'Library Members' in response.data
    
    def test_add_member_post(self, client):
        response = client.post('/add_member', data={
            'name': 'John Doe',
            'email': 'john@example.com'
        }, follow_redirects=True)
        assert response.status_code == 200

if __name__ == '__main__':
    pytest.main(['-v'])