# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
import json
import os

# Base class demonstrating inheritance
class Person:
    def __init__(self, person_id, name, email):
        self._person_id = person_id
        self._name = name
        self._email = email
        self._created_at = datetime.now()
    
    # Encapsulation - getter methods
    @property
    def person_id(self):
        return self._person_id
    
    @property
    def name(self):
        return self._name
    
    @property
    def email(self):
        return self._email
    
    def get_info(self):
        return {
            'id': self._person_id,
            'name': self._name,
            'email': self._email,
            'created_at': self._created_at.isoformat()
        }

# Inheritance - Member inherits from Person
class Member(Person):
    def __init__(self, member_id, name, email):
        super().__init__(member_id, name, email)
        self._borrowed_books = []
        self._max_books = 3
    
    def can_borrow(self):
        return len(self._borrowed_books) < self._max_books
    
    def borrow_book(self, book_id):
        if self.can_borrow():
            self._borrowed_books.append({
                'book_id': book_id,
                'borrowed_date': datetime.now().isoformat(),
                'due_date': (datetime.now() + timedelta(days=14)).isoformat()
            })
            return True
        return False
    
    def return_book(self, book_id):
        self._borrowed_books = [b for b in self._borrowed_books if b['book_id'] != book_id]
    
    def get_borrowed_books(self):
        return self._borrowed_books
    
    def to_dict(self):
        data = self.get_info()
        data.update({
            'borrowed_books': self._borrowed_books,
            'can_borrow_more': self.can_borrow()
        })
        return data

class Book:
    def __init__(self, book_id, title, author, isbn, category="General"):
        self._book_id = book_id
        self._title = title
        self._author = author
        self._isbn = isbn
        self._category = category
        self._is_available = True
        self._borrowed_by = None
        self._added_date = datetime.now()
    
    # Encapsulation
    @property
    def book_id(self):
        return self._book_id
    
    @property
    def title(self):
        return self._title
    
    @property
    def author(self):
        return self._author
    
    @property
    def is_available(self):
        return self._is_available
    
    def borrow(self, member_id):
        if self._is_available:
            self._is_available = False
            self._borrowed_by = member_id
            return True
        return False
    
    def return_book(self):
        self._is_available = True
        self._borrowed_by = None
    
    def to_dict(self):
        return {
            'id': self._book_id,
            'title': self._title,
            'author': self._author,
            'isbn': self._isbn,
            'category': self._category,
            'is_available': self._is_available,
            'borrowed_by': self._borrowed_by,
            'added_date': self._added_date.isoformat()
        }

# Data Access Layer - demonstrating abstraction
class DataManager:
    def __init__(self, data_file='library_data.json'):
        self.data_file = data_file
        self.data = self._load_data()
    
    def _load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return {'books': {}, 'members': {}, 'transactions': []}
    
    def _save_data(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def add_book(self, book):
        self.data['books'][str(book.book_id)] = book.to_dict()
        self._save_data()
    
    def add_member(self, member):
        self.data['members'][str(member.person_id)] = member.to_dict()
        self._save_data()
    
    def get_all_books(self):
        return self.data['books']
    
    def get_all_members(self):
        return self.data['members']
    
    def get_book(self, book_id):
        return self.data['books'].get(str(book_id))
    
    def get_member(self, member_id):
        return self.data['members'].get(str(member_id))
    
    def update_book(self, book_id, book_data):
        self.data['books'][str(book_id)] = book_data
        self._save_data()
    
    def update_member(self, member_id, member_data):
        self.data['members'][str(member_id)] = member_data
        self._save_data()
    
    def add_transaction(self, transaction):
        self.data['transactions'].append(transaction)
        self._save_data()

# Main Library System - demonstrates composition and polymorphism
class LibrarySystem:
    def __init__(self):
        self.data_manager = DataManager()
        self._next_book_id = self._get_next_id('books')
        self._next_member_id = self._get_next_id('members')
    
    def _get_next_id(self, entity_type):
        existing_ids = [int(k) for k in self.data_manager.data[entity_type].keys()]
        return max(existing_ids) + 1 if existing_ids else 1
    
    def add_book(self, title, author, isbn, category="General"):
        book = Book(self._next_book_id, title, author, isbn, category)
        self.data_manager.add_book(book)
        self._next_book_id += 1
        return book
    
    def add_member(self, name, email):
        member = Member(self._next_member_id, name, email)
        self.data_manager.add_member(member)
        self._next_member_id += 1
        return member
    
    def borrow_book(self, member_id, book_id):
        member_data = self.data_manager.get_member(member_id)
        book_data = self.data_manager.get_book(book_id)
        
        if not member_data or not book_data:
            return False, "Member or book not found"
        
        if not book_data['is_available']:
            return False, "Book is not available"
        
        # Recreate member object to check borrowing limit
        member = Member(member_data['id'], member_data['name'], member_data['email'])
        member._borrowed_books = member_data.get('borrowed_books', [])
        
        if not member.can_borrow():
            return False, "Member has reached borrowing limit"
        
        # Update book status
        book_data['is_available'] = False
        book_data['borrowed_by'] = member_id
        self.data_manager.update_book(book_id, book_data)
        
        # Update member's borrowed books
        member.borrow_book(book_id)
        self.data_manager.update_member(member_id, member.to_dict())
        
        # Add transaction
        transaction = {
            'type': 'borrow',
            'member_id': member_id,
            'book_id': book_id,
            'date': datetime.now().isoformat()
        }
        self.data_manager.add_transaction(transaction)
        
        return True, "Book borrowed successfully"
    
    def return_book(self, member_id, book_id):
        member_data = self.data_manager.get_member(member_id)
        book_data = self.data_manager.get_book(book_id)
        
        if not member_data or not book_data:
            return False, "Member or book not found"
        
        # Update book status
        book_data['is_available'] = True
        book_data['borrowed_by'] = None
        self.data_manager.update_book(book_id, book_data)
        
        # Update member's borrowed books
        member = Member(member_data['id'], member_data['name'], member_data['email'])
        member._borrowed_books = member_data.get('borrowed_books', [])
        member.return_book(book_id)
        self.data_manager.update_member(member_id, member.to_dict())
        
        # Add transaction
        transaction = {
            'type': 'return',
            'member_id': member_id,
            'book_id': book_id,
            'date': datetime.now().isoformat()
        }
        self.data_manager.add_transaction(transaction)
        
        return True, "Book returned successfully"

# Flask Application
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
library_system = LibrarySystem()

@app.route('/')
def index():
    books = library_system.data_manager.get_all_books()
    members = library_system.data_manager.get_all_members()
    
    # Calculate stats
    total_books = len(books)
    available_books = len([b for b in books.values() if b['is_available']])
    total_members = len(members)
    
    return render_template('index.html', 
                         total_books=total_books,
                         available_books=available_books,
                         total_members=total_members)

@app.route('/books')
def books():
    all_books = library_system.data_manager.get_all_books()
    return render_template('books.html', books=all_books)

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        category = request.form['category']
        
        book = library_system.add_book(title, author, isbn, category)
        flash(f'Book "{title}" added successfully!', 'success')
        return redirect(url_for('books'))
    
    return render_template('add_book.html')

@app.route('/members')
def members():
    all_members = library_system.data_manager.get_all_members()
    return render_template('members.html', members=all_members)

@app.route('/add_member', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        
        member = library_system.add_member(name, email)
        flash(f'Member "{name}" added successfully!', 'success')
        return redirect(url_for('members'))
    
    return render_template('add_member.html')

@app.route('/borrow', methods=['GET', 'POST'])
def borrow_book():
    if request.method == 'POST':
        member_id = request.form['member_id']
        book_id = request.form['book_id']
        
        success, message = library_system.borrow_book(member_id, book_id)
        flash(message, 'success' if success else 'error')
        return redirect(url_for('borrow_book'))
    
    books = library_system.data_manager.get_all_books()
    members = library_system.data_manager.get_all_members()
    available_books = {k: v for k, v in books.items() if v['is_available']}
    
    return render_template('borrow.html', books=available_books, members=members)

@app.route('/return', methods=['GET', 'POST'])
def return_book():
    if request.method == 'POST':
        member_id = request.form['member_id']
        book_id = request.form['book_id']
        
        success, message = library_system.return_book(member_id, book_id)
        flash(message, 'success' if success else 'error')
        return redirect(url_for('return_book'))
    
    books = library_system.data_manager.get_all_books()
    members = library_system.data_manager.get_all_members()
    borrowed_books = {k: v for k, v in books.items() if not v['is_available']}
    
    return render_template('return.html', books=borrowed_books, members=members)

@app.route('/api/member/<int:member_id>/books')
def get_member_books(member_id):
    member_data = library_system.data_manager.get_member(member_id)
    if member_data:
        borrowed_books = member_data.get('borrowed_books', [])
        return jsonify(borrowed_books)
    return jsonify([])

if __name__ == '__main__':
    app.run(debug=True)