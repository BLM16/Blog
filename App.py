from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from datetime import date

# Configure app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'

# Configure database
db = SQLAlchemy(app)

# Configure bootstrap
Bootstrap(app)

class User(db.Model):
    """User model for DB"""

    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), nullable = False, unique = True)
    email = db.Column(db.String(50), nullable = False, unique = True)
    password = db.Column(db.String, nullable = False)

    # References the Post class
    # Allows posts to access the User that created it
    posts = db.relationship('Post', backref = 'author', lazy = True)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

    def __repr__(self):
        return f'User({self.username}, {self.email})'

class Post(db.Model):
    """Post model for DB"""

    id = db.Column(db.Integer, primary_key = True)
    date_created = db.Column(db.String(10), nullable = False)
    title = db.Column(db.String(100), nullable = False)
    content = db.Column(db.Text, nullable = False)

    # Foreign key references the author's User's id
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)

    def __init__(self, author, title, content):
        self.author = author
        self.date_created = str(date.today())
        self.title = title
        self.content = content

    def __repr__(self):
        return f'Post({self.author}, {self.date_created}, {self.title})'

# Configure App routes
# Render the matching HTML file
@app.route('/')
def Main():
    return render_template("index.html")

@app.route('/login')
def Login():
    return render_template("login.html")

@app.route('/register')
def Register():
    return render_template("register.html")

# Run the code in debug mode
# Remove debug in production
if __name__ == '__main__':
    app.debug = True
    app.run()
    app.run(debug = True)