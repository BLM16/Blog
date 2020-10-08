from flask import Flask, render_template
from flask_bootstrap import Bootstrap

app = Flask(__name__)
Bootstrap(app)

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