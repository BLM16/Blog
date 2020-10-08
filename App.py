from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'

db = SQLAlchemy(app)

Bootstrap(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), nullable = False)
    email = db.Column(db.String(50), nullable = False, unique = True)
    password = db.Column(db.String, nullable = False)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

    def __repr__(self):
        return 'User({}, {})'.format(self.username, self.email)

@app.route('/')
def Main():
    return render_template("index.html")

@app.route('/login')
def Login():
    return render_template("login.html")

@app.route('/register')
def Register():
    return render_template("register.html")

if __name__ == '__main__':
    app.debug = True
    app.run()
    app.run(debug = True)