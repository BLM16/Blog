from flask import Flask, render_template, redirect, url_for, request, session
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text, select
from sqlalchemy.exc import SQLAlchemyError
from datetime import date
import re

# Configure app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SECRET_KEY'] = '77916e7166d54cf2bdc184058c4bf3d6'

# Configure database
db = SQLAlchemy(app)
engine = db.engine

# Configure bootstrap
Bootstrap(app)

class User(db.Model):
    """User model for DB"""

    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), nullable = False, unique = True)
    email = db.Column(db.String(50), nullable = False, unique = True)
    password = db.Column(db.String, nullable = False)
    #about = db.Colum(db.Text)

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

    def __init__(self, author_id, title, content):
        self.date_created = str(date.today())
        self.title = title
        self.content = content
        self.author_id = author_id

    def __repr__(self):
        return f'Post({self.author}, {self.date_created}, {self.title})'

# Handle 404 errors
@app.errorhandler(404)
def Page_Not_Found(e):
    return redirect(url_for('Error', title = "Error: 404", msg = e))

# Configure App routes
# Render the matching HTML file
@app.route('/')
def Main():
    return render_template("index.html")

@app.route('/login')
def Login():
    message = request.args.get('message')
    return render_template("login.html", message = message)

@app.route('/register')
def Register():
    message = request.args.get('message')
    return render_template("register.html", message = message)

@app.route('/profile')
def Own_Profile():
    """Route for viewing own profile"""

    # Display profile if user is logged in, else prompt them to login
    if not 'user_id' in session:
        return redirect(url_for('Login', message = "You must be logged in to view your profile."))
    else:
        with engine.connect() as con:
            # Get user from DB
            try:
                statement = text("SELECT * FROM user WHERE (id = :id)")
                user = con.execute(statement, id = session['user_id']).fetchall()[0]
            except SQLAlchemyError as e:
                return redirect(url_for('Error', title = "Error: Fetching user", msg = type(e), back = "Own_Profile"))
            except:
                return redirect(url_for('Error', title = "Error", msg = "<class 'blog.UnhandledError'>", back = "Own_Profile"))

            # Get user posts from DB
            try:
                statement = text("SELECT * FROM post WHERE (author_id = :id) ORDER BY id DESC")
                posts = con.execute(statement, id = session['user_id']).fetchall()
            except SQLAlchemyError as e:
                return redirect(url_for('Error', title = "Error: Fetching user posts", msg = type(e), back = "Own_Profile"))
            except:
                return redirect(url_for('Error', title = "Error", msg = "<class 'blog.UnhandledError'>", back = "Own_Profile"))

        return render_template("profile.html", user = user, posts = posts, editable = True)

@app.route('/profile/<username>')
def User_Profile(username):
    """Route for viewing other's profiles"""

    with engine.connect() as con:
        # Get user from DB
        try:
            statement = text("SELECT * FROM user WHERE (username = :username)")
            user = con.execute(statement, username = username).fetchall()[0]
        except SQLAlchemyError as e:
            return redirect(url_for('Error', title = "Error: Fetching user", msg = type(e)))
        except:
            return redirect(url_for('Error', title = "Error", msg = "<class 'blog.UnhandledError'>"))

        # Get user posts from DB
        try:
            statement = text("SELECT * FROM post WHERE (author_id = :id) ORDER BY id DESC")
            posts = con.execute(statement, id = user.id).fetchall()
        except SQLAlchemyError as e:
            return redirect(url_for('Error', title = "Error: Fetching user posts", msg = type(e)))
        except:
            return redirect(url_for('Error', title = "Error", msg = "<class 'blog.UnhandledError'>"))

        # Redirect user to profile not profile/<username> if <username> is theirs (shows editing buttons and stuff)
        if 'user_id' in session:
            if user.id == session['user_id']:
                return redirect(url_for('Own_Profile'))

    return render_template("profile.html", user = user, posts = posts, editable = False)

@app.route('/post/<int:post_id>')
def View_Post(post_id):
    pass

@app.route('/recent')
def Recent():
    # Connect to DB
    with engine.connect() as con:
        try:
            statement = text("SELECT p.id, p.title, p.content, p.date_created AS date, user.username AS author FROM post AS p INNER JOIN user ON (p.author_id = user.id) ORDER BY p.id DESC LIMIT 25")
            posts = con.execute(statement).fetchall()
        except SQLAlchemyError as e:
            return redirect(url_for('Error', title = "Error: Fetching recent posts", msg = type(e), back = "Recent"))
        except:
            return redirect(url_for('Error', title = "Error", msg = "<class 'blog.UnhandledError'>", back = "Recent"))

    return render_template('recent.html', posts = posts)

@app.route('/logout')
def Logout():
    # Delete the user's session
    session.pop('user_id')

    return redirect(url_for('Login'))

@app.route('/error')
def Error():
    title = request.args.get('title')
    msg = request.args.get('msg')
    back = request.args.get('back')

    return render_template("error.html", title = title, msg = msg, back = back)

# Configure App routes with HTTP methods
@app.route('/login', methods = ['POST'])
def Login_User():
    """Checks credentials and logs user in"""

    # Check if both fields are filled out
    if not (request.form['email'] and request.form['password']):
        return redirect(url_for('Login', message = "Invalid email or password"))
    else:
        # Connect to DB
        with engine.connect() as con:
            # Check if user exists with given credentials
            try:
                statement = text("SELECT user.id FROM user WHERE (email = :email AND password = :password)")
                user_id = con.execute(statement, email = request.form['email'], password = request.form['password']).scalar()
            except SQLAlchemyError as e:
                return redirect(url_for('Error', title = "Error: Validating user", msg = type(e), back = "Login_User"))
            except:
                return redirect(url_for('Error', title = "Error", msg = "<class 'blog.UnhandledError'>", back = "Login_User"))

            if user_id:
                session['user_id'] = user_id # Create a user_id session to store login
                return redirect(url_for('Own_Profile')) # Redirect to user's profile
            else:
                return redirect(url_for('Login', message = "Invalid email or password"))

@app.route('/register', methods = ['POST'])
def Register_User():
    """Validates register form data and saves it to the database"""

    # Check if the fields are filled out
    if not (request.form['username'] and request.form['email'] and request.form['password'] and request.form['passwordConf']):
        return redirect(url_for('Register', message = "Please fill out all the fields"))
    else:
        # Ensure passwords match
        if request.form['password'] != request.form['passwordConf']:
            return redirect(url_for('Register', message = "Passwords do not match"))

        # Ensure name is only _, a-z, A-Z, 0-9, and space
        if not re.search(r'^[\w_ ]+$', request.form['username']):
            return redirect(url_for('Register', message = "Username can only contain _, a-z, A-Z, 0-9 and spaces."))
        
        # Ensure a valid email
        if not re.search(r'^[a-zA-Z0-9]+[\._]?[a-zA-Z0-9]+[@]\w+[.]\w+$', request.form['email']):
            return redirect(url_for('Register', message = "Invalid email"))

        # Connect to DB
        with engine.connect() as con:
            # Check if username is taken
            try:
                statement = text("SELECT COUNT(1) FROM user WHERE (username = :username)")
                result = con.execute(statement, username = request.form['username']).scalar()
            except SQLAlchemyError as e:
                return redirect(url_for('Error', title = "Error: Validating user availability", msg = type(e), back = "Register_User"))
            except:
                return redirect(url_for('Error', title = "Error", msg = "<class 'blog.UnhandledError'>", back = "Register_User"))

            if result > 0:
                return redirect(url_for('Register', message = "Username is already taken"))

            # Check if email is taken
            try:
                statement = text("SELECT COUNT(1) FROM user WHERE (email = :email)")
                result = con.execute(statement, email = request.form['email']).scalar()
            except SQLAlchemyError as e:
                return redirect(url_for('Error', title = "Error: Validating user availability", msg = type(e), back = "Register_User"))
            except:
                return redirect(url_for('Error', title = "Error", msg = "<class 'blog.UnhandledError'>", back = "Register_User"))

            if result > 0:
                return redirect(url_for('Register', message = "Email is already taken"))

            # Create new user and add to the database
            new_user = User(request.form['username'], request.form['email'], request.form['password'])
            db.session.add(new_user)
            db.session.commit()

            # Get the new user's ID to log them in
            try:
                statement = text("SELECT id FROM user WHERE (username = :username)")
                result = con.execute(statement, username = request.form['username']).scalar()
            except:
                return redirect(url_for('Error', title = "Error: Login failed", msg = "REGISTRATION WAS SUCCESSFUL. Something went wrong loging you in. Please login."))

            # Log the new user in with a session
            session['user_id'] = result

            # Redirect to the new user's profile
            return redirect(url_for('Own_Profile'))

# Run the code in debug mode
# Remove debug in production
if __name__ == '__main__':
    app.debug = True
    app.run()
    app.run(debug = True)