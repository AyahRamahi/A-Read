from flask import Flask,request,url_for,redirect,render_template,session,jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests
import os
import json

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

app.config['SESSION_TYPE'] = 'filesystem'
app.config["SESSION_PERMANENT"] = False
Session(app)
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


from database import create_users, signin_user,signup_user,create_reviews



@app.route("/")
def index ():
    return render_template("index.html")

@app.route("/main",methods=["GET","POST"])
def main():
    # you can search for a book with a part of its isbn,title,author name or year of production
    try:
        session['logged_in']
    except KeyError:
        session['logged_in'] = False
    if not session['logged_in'] :
        return redirect(url_for("index"))
    else :
        if request.method == "GET":
            return render_template("main.html")
        elif request.method == "POST":
            search = request.form['search']
            search = search.capitalize()
            # concatenate the %% to the string to be able to use placeholders
            instr = """
                SELECT * FROM books WHERE (title LIKE '%' || :search || '%') 
                OR (author LIKE '%' || :search || '%') OR
                (ISBN LIKE '%' || :search || '%') OR 
                (year LIKE '%' || :search || '%')
            """
            result = db.execute(f"({instr})",{'search':search}).fetchall()
            return render_template("result.html",result=result)


@app.route("/signin",methods=["POST","GET"])
def signin():
    try :
        session['logged_in']
    except KeyError:
        session['logged_in']=False
    if session['logged_in']:
        return redirect(url_for("main"))
    else :
        if request.method == "GET":
            return render_template("signin.html",error=False)
        elif request.method == "POST" :
            usr=request.form['username']
            pas=request.form['password']
            check = signin_user(usr,pas)
            if check == False:
                return render_template("signin.html",error=True)
            else :
                session['logged_in'] = True
                session['user_id'] = check[0]
                return redirect(url_for("main"))
    
@app.route("/signup",methods=["POST","GET"])
def signup ():
    try :
        session['logged_in']
    except KeyError:
        session['logged_in'] = False
    if session['logged_in'] :
        return redirect(url_for("main"))
    else :
        if request.method == "GET":
            return render_template("signup.html",error=False)
        elif request.method == "POST" :
            usr=request.form['username']
            pas=request.form['password']
            check = signup_user(usr,pas)
            if check == False :
                return render_template("signup.html",error=True)
            else :
                return redirect(url_for("index"))

@app.route("/signout")
def signout():
    session['logged_in'] = False
    del session['user_id']
    return redirect(url_for("index"))

@app.route("/<string:isbn>",methods=["GET","POST"])
def book(isbn):
    # shows data about this book and shows reviews and rates submitted by users and avg rates
    try:
        session['logged_in']
    except KeyError:
        session['logged_in'] = False
    b = db.execute("SELECT * FROM books WHERE ISBN = :isbn",{'isbn':isbn}).fetchone()
    if request.method == "GET":
        reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id",{'book_id':b[0]}).fetchall()
        reviewd = False
        if session['logged_in'] :
            for r in reviews :
                if r[2] == session['user_id']:
                    reviewd=True
                    break
        avg_rate= db.execute("SELECT AVG(rate) FROM reviews WHERE book_id = :id",{'id':b['id']})
        if avg_rate is None:
            avg_rate = 0
        avg_rate = avg_rate.scalar()
        if avg_rate is not None:
            avg_rate = round(avg_rate,2)
        return render_template("book.html",avg_rate=avg_rate,book=b,reviewd=reviewd,reviews=reviews,user_id=session['user_id'])
    elif request.method == "POST" :
        # add a review
        review = request.form['review']
        rate = request.form['rate']
        db.execute("INSERT INTO reviews (book_id,user_id,review,rate) VALUES (:book_id,:user_id,:review,:rate)"
        ,{'book_id':b[0],'user_id':session['user_id'],'review':review,'rate':rate})
        db.commit()
        return redirect(url_for('book',isbn=isbn))

@app.route("/<string:isbn>/delete/<int:review_id>")
def del_review (isbn,review_id):
    # delets a review
    try :
        session['logged_in']
    except KeyError:
        session['logged_in'] = False
    if not session['logged_in']:
        return redirect(url_for('main'))
    else :
        db.execute("DELETE FROM reviews WHERE id = :id",{'id':review_id})
        db.commit()
        return redirect(url_for('book',isbn=isbn))

@app.route("/api/<string:isbn>")
def api_access (isbn) :
    # takes dictionary from goodreads API about the book with isbn and return json file
    key = "VUmCmbZNT73oLCo0rRriTg"
    check = db.execute("SELECT * FROM books WHERE ISBN = :isbn",{'isbn':isbn}).fetchone()
    if check is not None :
        # .json() converts the result to dictionary
        res = requests.get("https://www.goodreads.com/book/review_counts.json",
        params={"key": key, "isbns":isbn}).json()
        ret = {
            "title" : check[2],
            "author" : check[3],
            "year" : check[4],
            "isbn" : isbn,
            "review_count": str(res['books'][0]['reviews_count']),
            "average_score": str(res['books'][0]['average_rating']) }
        return jsonify (ret)
    else :
        return render_template("404.html")
    
if __name__ == '__main__':
	app.debug = True
	create_users()
    	create_reviews()
	app.secret_key = os.urandom(24)
	app.run()
