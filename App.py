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
    about = db.Column(db.Text)

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
    # Log current user out (if any)
    if 'user_id' in session:
        session.pop('user_id')

    message = request.args.get('message')
    return render_template("login.html", message = message)

@app.route('/register')
def Register():
    # Log current user out (if any)
    if 'user_id' in session:
        session.pop('user_id')

    message = request.args.get('message')
    return render_template("register.html", message = message)

@app.route('/profile')
def Own_Profile():
    """Route for viewing own profile"""

    # Display profile if user is logged in, else prompt them to login
    if not 'user_id' in session:
        return redirect(url_for('Login', message = "You must be logged in to view your profile."))
    else:
        # Connect to DB
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

            # Check if the user is editing their about
            to_edit = request.args.get('edit')

        return render_template("profile.html", user = user, posts = posts, editable = True, to_edit = to_edit)

@app.route('/profile/<username>')
def User_Profile(username):
    """Route for viewing other's profiles"""

    # Connect to db
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

@app.route('/post/new')
def New_Post():
    message = request.args.get('message')

    if not 'user_id' in session:
        return redirect(url_for('Login', message = "You must be logged in to make a post"))

    return render_template("new.html", message = message)

@app.route('/post/<int:post_id>')
def View_Post(post_id):
    # Connect to DB
    with engine.connect() as con:
        # Select the post data
        try:
            statement = text("SELECT p.id AS post_id, p.title, p.content, p.author_id, p.date_created AS date, user.username AS author FROM post AS p INNER JOIN user ON (p.author_id = user.id) WHERE (p.id = :id)")
            post = con.execute(statement, id = post_id).fetchall()[0]
        except SQLAlchemyError as e:
            return redirect(url_for('Error', title = "Error: Fetching post", msg = type(e), back = "Recent"))
        except:
            return redirect(url_for('Error', title = "Error", msg = "<class 'blog.UnhandledError'>", back = "Recent"))

        if session['user_id'] == post.author_id:
            edit = request.args.get('edit')
        else:
            edit = 'false'

    return render_template('post.html', post = post, edit = edit)

@app.route('/recent')
def Recent():
    # Connect to DB
    with engine.connect() as con:
        # Select the 25 most recent posts
        try:
            statement = text("SELECT p.id, p.title, p.content, p.date_created AS date, user.username AS author FROM post AS p INNER JOIN user ON (p.author_id = user.id) ORDER BY p.id DESC LIMIT 25")
            posts = con.execute(statement).fetchall()
        except SQLAlchemyError as e:
            return redirect(url_for('Error', title = "Error: Fetching recent posts", msg = type(e), back = "Recent"))
        except:
            return redirect(url_for('Error', title = "Error", msg = "<class 'blog.UnhandledError'>", back = "Recent"))

    return render_template('recent.html', posts = posts)

@app.route('/post/<int:post_id>/del')
def Delete_Post_Form(post_id):
    return render_template("delete.html")

@app.route('/password')
def Change_Password_Form():
    # Send the user to login if they aren't logged in
    if not 'user_id' in session:
        return redirect(url_for('Login', message = "You must be logged in to change your password"))

    message = request.args.get('message')

    return render_template("changePwd.html", message = message)

@app.route('/logout')
def Logout():
    # Delete the user's session
    session.pop('user_id')

    return redirect(url_for('Login'))

@app.route('/error')
def Error():
    # Get the error parameters
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

            # If user exists, log them in
            # Else alert them to the wrong credentials
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
            try:
                new_user = User(request.form['username'], request.form['email'], request.form['password'])
                db.session.add(new_user)
                db.session.commit()
            except:
                return redirect(url_for('Error', title = "Error", msg = "<class 'blog.UnhandledError'>", back = "Register_User"))

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

@app.route('/profile', methods = ['POST'])
def Update_About():
    """Updates user's about in the DB"""

    # If the user is updating their about
    if request.form['about']:
        # Limit length to 500 characters including whitespace
        # Textarea in profile.html restricts too, this is verification
        if len(str(request.form['about'])) - str(request.form['about']).count("\n") > 500:
            return redirect(url_for('Error', title = "Error: About too long", msg = "Your about can not be more than 500 characters!", back = "Own_Profile"))

        # Connect to DB
        with engine.connect() as con:
            # Update user's status in DB
            try:
                statement = text("UPDATE user SET about = :about WHERE id = :id")
                result = con.execute(statement, about = request.form['about'], id = session['user_id']).rowcount
            except SQLAlchemyError as e:
                return redirect(url_for('Error', title = "Error: Updating user about", msg = type(e), back = "Own_Profile"))
            except:
                return redirect(url_for('Error', title = "Error", msg = "<class 'blog.UnhandledError'>", back = "Own_Profile"))

            # If update was successful, return to profile
            # Else throw error
            if result == 1:
                return redirect(url_for('Own_Profile'))
            else:
                return redirect(url_for('Error', title = "Error: Updating user about", msg = "<class 'blog.UnhandledError'>", back = "Own_Profile"))

@app.route('/post/new', methods = ['POST'])
def Post_New_Post():
    """Posts new posts"""

    # Check if the fields are filled out
    if not (request.form['title'] and request.form['content']):
        return redirect(url_for('New_Post', message = "Please fill out all the fields"))
    else:
        # Limit length including whitespace
        # Inputs in new.html restrict too, this is verification
        if len(str(request.form['title'])) > 100:
            return redirect(url_for('New_Post', message = "Title can only be 100 characters long"))
        if len(str(request.form['content'])) - str(request.form['content']).count("\n") > 5000:
            return redirect(url_for('New_post', message = "Content can only be 5000 characters long"))

        # Connect to DB
        with engine.connect() as con:
            # Create post
            try:
                post = Post(session['user_id'], request.form['title'], request.form['content'])
                db.session.add(post)
                db.session.commit()

                # Get post id and redirect to the new post
                try:
                    statement = text("SELECT id FROM post WHERE (author_id = :author AND title = :title AND content = :content)")
                    result = con.execute(statement, author = session['user_id'], title = request.form['title'], content = request.form['content']).scalar()

                    return redirect(url_for('View_Post', post_id = result))
                except SQLAlchemyError as e:
                    return redirect(url_for('Error', title = "Error: Handling post", msg = type(e), back = "Own_Profile"))
                except:
                    return redirect(url_for('Error', title = "Error", msg = "<class 'blog.UnhandledError'>", back = "New_Post"))
            except:
                return redirect(url_for('Error', title = "Error: Creating post", msg = "<class 'blog.UnhandledError'>", back = "New_Post"))

@app.route('/post/<int:post_id>', methods = ['POST'])
def Edit_Post(post_id):
    # Verify that the fields have content
    if not (request.form['title'] and request.form['content']):
        return redirect(url_for('View_Post', post_id = post_id))

    # Limit length including whitespace
    # Inputs in new.html restrict too, this is verification
    if len(str(request.form['title'])) > 100:
        return redirect(url_for('View_Post', post_id = post_id, message = "Title can only be 100 characters long"))
    if len(str(request.form['content'])) - str(request.form['content']).count("\n") > 5000:
        return redirect(url_for('View_Post', post_id = post_id, message = "Content can only be 5000 characters long"))

    # Connect to DB
    with engine.connect() as con:
        # Select the post's author's id
        try:
            statement = text("SELECT author_id FROM post WHERE (id = :id)")
            author_id = con.execute(statement, id = post_id).scalar()
        except SQLAlchemyError as e:
            return redirect(url_for('Error', title = "Error: Editing post", msg = type(e), back = "Recent"))
        except:
            return redirect(url_for('Error', title = "Error", msg = "<class 'blog.UnhandledError'>", back = "Recent"))

        # Verify that the editor is the author
        if session['user_id'] == author_id:
            # Update the post
            try:
                statement = text("UPDATE post SET title = :title, content = :content, date_created = :date WHERE id = :id")
                result = con.execute(statement, title = request.form['title'], content = request.form['content'], date = str(date.today()), id = post_id).rowcount
            except SQLAlchemyError as e:
                return redirect(url_for('Error', title = "Error: Updating post", msg = type(e), back = "Recent"))
            except:
                return redirect(url_for('Error', title = "Error", msg = "<class 'blog.UnhandledError'>", back = "Recent"))

            # If there was an error updating, show that
            if result < 1:
                return  redirect(url_for('Error', title = "Error: Updating post", msg = "<class 'blog.UnhandledError'>", back = "Recent"))
        else:
            return  redirect(url_for('Error', title = "Error: Can't edit other's posts", msg = "<class 'blog.PostSecurityError'>", back = "Recent"))

    return redirect(url_for("View_Post", post_id = post_id))

@app.route('/post/<int:post_id>/del', methods = ['POST'])
def Delete_Post(post_id):
    """Deletes a post by id if user is the post's author"""

    if str(request.form['confirm']).lower() == 'confirm':
        # Connect to DB
        with engine.connect() as con:
            try:
                statement = text("SELECT author_id from post WHERE (id = :id)")
                author_id = con.execute(statement, id = post_id).scalar()
            except SQLAlchemyError as e:
                return redirect(url_for('Error', title = "Error: Deleting post", msg = type(e), back = "Recent"))
            except:
                return redirect(url_for('Error', title = "Error", msg = "<class 'blog.UnhandledError'>", back = "Recent"))

            if not (session['user_id'] == author_id):
                return redirect(url_for('Error', title = "Error: Can't delete others' posts", msg = "You can't delete others' posts!!!", back = "Recent"))

            # Delete post
            try:
                statement = text("DELETE FROM post WHERE id = :id")
                result = con.execute(statement, id = post_id).rowcount
            except SQLAlchemyError as e:
                return redirect(url_for('Error', title = "Error: Deleting post", msg = type(e), back = "Recent"))
            except:
                return redirect(url_for('Error', title = "Error", msg = "<class 'blog.UnhandledError'>", back = "Recent"))

            # If update was successful, return to profile
            # Else throw error
            if result == 1:
                return redirect(url_for('Own_Profile'))
            else:
                return redirect(url_for('Error', title = "Error: Deleting post", msg = "<class 'blog.UnhandledError'>", back = "Recent"))
    else:
        return redirect(url_for('Delete_Post', post_id = post_id))

@app.route('/password', methods = ['POST'])
def Change_Password():
    """Changes the current user's password"""

    # Verify the fields have content
    if not (request.form['passwordOld'] and request.form['passwordNew'] and request.form['passwordConf']):
        return redirect(url_for('Change_Password_Form', message = "All the fields must be filled in"))

    # Ensure passwords match
    if request.form['passwordNew'] != request.form['passwordConf']:
        return redirect(url_for('Change_Password_Form', message = "Passwords do not match"))

    # Connect to DB
    with engine.connect() as con:
        # Check if password matches passwordOld
        try:
            statement = text("SELECT password FROM user WHERE id = :id")
            passwordOld = con.execute(statement, id = session['user_id']).scalar()
        except SQLAlchemyError as e:
            return redirect(url_for('Error', title = "Error: Deleting password", msg = type(e), back = "Change_Password_Form"))
        except:
            return redirect(url_for('Error', title = "Error", msg = "<class 'blog.UnhandledError'>", back = "Change_Password_Form"))

        if passwordOld == request.form['passwordOld']:
            # Change password
            try:
                statement = text("UPDATE user SET password = :password WHERE id = :id")
                result = con.execute(statement, password = request.form['passwordNew'], id = session['user_id']).rowcount
            except SQLAlchemyError as e:
                return redirect(url_for('Error', title = "Error: Deleting password", msg = type(e), back = "Change_Password_Form"))
            except:
                return redirect(url_for('Error', title = "Error", msg = "<class 'blog.UnhandledError'>", back = "Change_Password_Form"))
        else:
            return redirect(url_for('Change_Password_Form', message = "Incorrect old password"))

    # If update was successful, return to profile
    # Else throw error
    if result == 1:
        return redirect(url_for('Own_Profile'))
    else:
        return redirect(url_for('Error', title = "Error: Changing password", msg = "<class 'blog.UnhandledError'>", back = "Change_Password_Form"))

# Run the code in debug mode
# Remove debug in production
if __name__ == '__main__':
    app.debug = True
    app.run()
    app.run(debug = True)