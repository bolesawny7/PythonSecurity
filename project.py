from flask import Flask, render_template, request, redirect, url_for, session, flash, render_template_string
import db
import utils
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import validators
import os

project = Flask(__name__)
connection = db.connect_to_database()
project.secret_key = "zs9XYCbTPKvux46UJckflw"
limiter = Limiter(app=project, key_func=get_remote_address, default_limits=["5 per minute"])

@project.route('/')
def index():
	if 'username' in session:
		if session['username'] == 'admin':
			return render_template("index.html", gadgets=db.getAllBooks(connection)) 
			return list(db.get_all_users(connection))
		else:
			return render_template("index.html", gadgets=db.getAllBooks(connection))
	return "You are not logged in."

@project.route('/signIn', methods=['GET', 'POST'])
@limiter.limit("5 per minute") 
def signIn():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']

		user = db.getUser(connection, username)
		
		if user:
			if utils.passwordMatch(password, user[2]):
				session['username'] = user[1]
				session['user_id'] = user[0]
				return redirect(url_for('index'))
			else:
				flash("Password doesn't match", "danger")
				return render_template('signIn.html')
			
		else:
			flash("Wrong User Name", "danger")
			return render_template('signIn.html')

	return render_template('signIn.html')

@project.route('/registeration', methods=['GET', 'POST'])
@limiter.limit("5 per minute") 
def registeration():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		if not utils.strongPassword(password):
			flash("You have Entered a weak Password.Choose a stronger one", "danger")
			return render_template('registeration.html')
		
		user = db.getUser(connection, username)
		if user:
			flash("User Name already exists.Choose a different one.", "danger")
			return render_template('registeration.html')
		else:
			db.addUser(connection, username, password)
			return redirect(url_for('signIn'))

	return render_template('registeration.html')

@project.route('/logout')
def logout():
	session.pop('username', None)
	return redirect(url_for('index'))

@project.route('/uploadBook', methods = ['GET','POST'])
def uploadBook():
	if request.method == 'POST':
		if not 'user_id' in session:
			flash("You Are Not Logged In", "danger")
			return redirect(url_for('signIn'))

		bookImage = request.files['image']
		if not bookImage or bookImage.filename == '':
			flash("Image Is Required", "danger")
			return render_template("uploadBook.html")

		if  not (validators.allowed_file(bookImage.filename)) or not validators.allowed_file_size(bookImage):
			flash("Invalid File is Uploaded", "danger")
			return render_template("uploadBook.html")

		title = request.form['title']
		description = request.form['description']
		price = request.form['price']

		image_url = f"uploads/{bookImage.filename}"
		bookImage.save(os.path.join("static",image_url))
		user_id = session['user_id']

		db.addBook(connection, user_id, title, description, price, image_url)
		return redirect(url_for('index'))

	return render_template("uploadBook.html")


@project.route('/book/<gadget_id>',methods=['GET','POST'])
def getBook(gadget_id):
	gadget = db.get_book(connection, gadget_id)
	comments = db.get_comments_for_book(connection, gadget[0])

	return render_template('book.html', gadget=gadget, comments=comments)

@project.route('/add-comment/<gadget_id>', methods=['POST'])
def addComment(gadget_id):
	text = request.form['comment']
	user_id = session['user_id']
	db.add_comment(connection, gadget_id, user_id, text)
	return redirect(url_for("getBook", gadget_id=gadget_id))

@project.route('/buy-gadget/<gadget_id>',methods=['POST'])
def buyBook(gadget_id):
    gadget = db.get_book(connection, gadget_id)
    is_sold = db.bookSoldCheck(connection,gadget_id)
    if is_sold == 0:
       if gadget:
            db.bookSold(connection, gadget[0])
            flash(f"You have bought the book successfully","success")
            return redirect(url_for("getBook", gadget_id=gadget_id))
       else:
            return redirect(url_for("getBook", gadget_id=gadget_id))
    else:
        flash("The book is already sold.", "danger")
        return redirect(url_for('getBook', gadget_id=gadget_id))	    

    
@project.route('/profile')
def profile():
	if 'username' in session:
		return render_template("profile.html", user=db.getUser(connection, session['username']))

	flash("You need to Login first", "danger")
	return redirect(url_for("signIn"))

@project.route('/withdraw')
def withdraw():
	if 'username' in session:
		return render_template("withdraw.html", user=db.getUser(connection, session['username']))

	flash("You need to Login first", "danger")
	return redirect(url_for("signIn"))

if __name__ == '__main__':
	db.init_db(connection)
	db.init_gadget_table(connection)
	db.init_comments_table(connection)
	db.seed_admin_user(connection)
	project.run(debug=True ,port=5002)
