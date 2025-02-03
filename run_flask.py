
# import Flask , redirect, url_for , flash,  request, render_template, pretty much standard in flask 
from flask import Flask , redirect, url_for , request, render_template,flash,session
# import generate_password_hash, check_password_hash for securing and verifying passwords
from werkzeug.security import generate_password_hash, check_password_hash   
# import flask sql alchemy 
from flask_sqlalchemy import SQLAlchemy 

from sqlalchemy.exc import SQLAlchemyError
# import UserMixing to handle login sessions, LoginManager to manage login's, login_required to 
# decorate login page and other pages that requires login acess, logout user's to log out and login_users to 
# to login users
from flask_login import  UserMixin, LoginManager,  login_required, logout_user, login_user, current_user  
# import email validator to validate emails,  EmailNotValidError for execeptions
from email_validator import validate_email , EmailNotValidError 

# import os and secret to create a secure secret key , Create an environemnt variable to  
# to export the secret key ,   export FLASH_SECRET_KEY='The hash you genberated using the below command'
#  cmnd in python   FLASK_SECRET_KEY = secrets.token_hex(32) this will create 
# 32 bytes = 64 characters in hex
import os, secrets


# create and initialize the flask app 
app = Flask(__name__)


app.config.from_pyfile('config.py')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app) 

login_manager = LoginManager(app) 

login_manager.login_view = 'login'





class Member(db.Model, UserMixin):

	id = db.Column(db.Integer, primary_key=True, nullable=False)
	name = db.Column(db.String(250), nullable=False)
	last_name = db.Column(db.String(250), nullable=False)
	email = db.Column(db.String(200), unique=True, nullable=False)
	password = db.Column(db.String(200), nullable=False)
	blog = db.relationship('Blog', backref='member', cascade='all, delete-orphan') 



class Blog(db.Model, UserMixin):

	id = db.Column(db.Integer, primary_key=True, nullable=False) 
	blog_name = db.Column(db.String(250))
	member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False) 





@login_manager.user_loader
def load_user(user_id):
    return Member.query.get(int(user_id))






@app.route('/create_blogs', methods=["POST"])
def create_blogs():


	if request.method == "POST":

		blog = request.form.get("blog")



		member_blog = Blog(blog_name=blog, member_id=current_user.id) 



		if member_blog:


			try:

				db.session.add(member_blog)

				db.session.commit()

				return redirect(url_for('profile')) 

			except SQLAlchemyError as e:


				flash("Erro while trying to add the blog, Try again. {e}")

				return redirect(url_for('profile'))


	return redirect(url_for('profile')) 





@app.route('/delete_blogs/<int:blog_id>', methods=["POST"])

def delete_blogs(blog_id):

	if request.method == "POST":

		blog = Blog.query.get_or_404(blog_id)

		if blog.member_id != current_user.id:


		    flash("You can not delete this blog")

		    return redirect(url_for('profile'))



		try:

		   db.session.delete(blog)

		   db.session.commit()

		except SQLAlchemyError as e:

			flash("Unable to delete the blog at this time.")
			db.session.rollback()

	return redirect(url_for('profile'))




@app.route('/edit_blog/<int:blog_id>', methods=["POST"])

def edit_blog(blog_id):


	if request.method == "POST":

		blog = Blog.query.get_or_404(blog_id)


		if blog.member_id != current_user.id:

			flash("You are not permitted to edit this blog", 'warning')

			return redirect(url_for('profile'))


		new_blog = request.form.get("content")



		blog.blog_name = new_blog 


		db.session.commit() 


		return redirect(url_for('profile'))	

	return redirect(url_for('profile'))






@app.route('/')
def home():


	return render_template('home.html') 



@app.route('/register', methods=["POST", "GET"]) 
def register():

	current_members = Member.query.all()

	if request.method == "POST": 

		name = request.form.get('name')
		last_name = request.form.get('last_name')
		email = request.form.get('email')
		password = request.form.get('password')
		confirm_password = request.form.get('confirm_password')

		current_members_emails = [member.email for member in current_members] 


		if not current_members_emails:

			try:
				validate_email(email)
			except EmailNotValidError:
				flash('Invalid email format, Exmp: John@gmail.com', 'error')
				return redirect(url_for('home'))


		elif email in current_members_emails:
			flash('Email already exist, Please try to login, Or use a new email', 'warning')
			return redirect(url_for('home'))



		

		if confirm_password != password:
			flash('Passwords do not match')
			return redirect(url_for('home'))


		valid_password = generate_password_hash(password)


		member = Member(name=name, last_name=last_name, email=email, password=valid_password)


	
		try:
			db.session.add(member)
			db.session.commit()
			flash("Registration successful, You can now login with your credentials", "success")
			#session.pop('_flashes', None)  # Clear flash messages



		except SQLAlchemyError as e:

			flash(f"Database error while trying to add Member ,Try again {e}") 
			db.session.rollback()

			return redirect(url_for('home'))


	return render_template('home.html')






@app.route('/login', methods=["POST", "GET"]) 
def login():


	if request.method == "POST":

		email = request.form.get('email')
		password = request.form.get('password')
		member = Member.query.filter_by(email=email).first()


		if member and check_password_hash(member.password, password):
			login_user(member)
			return redirect(url_for('profile'))

		else:

			flash("Invalid credentials, check your details and try again", "warning")

			return redirect(url_for('home'))



	return render_template('home.html')









@app.route('/profile', methods=["POST", "GET"])
@login_required
def profile():


   # Edge cases, The root of most Evils

	if not current_user.is_authenticated:

		flash("You are accessing a restricted page, Please try to login or register, Thank you", "danger")

		return redirect(url_for('login')) 

	user_name = current_user.name


	all_current_member_blogs = Blog.query.filter_by(member_id=current_user.id).all()

	


	return render_template('profile.html', username=user_name, blogs=all_current_member_blogs)






@app.route('/logut')
@login_required 
def logout():
	logout_user()

	flash('Logging out succesful', 'success')


	return redirect(url_for('login'))













def get_data():
    members = Member.query.all()
    
    if members:
        
        for member in members:

        	blogs = member.blog


        	if blogs:

        		for b in blogs:

        			print(member.name, " Has the : -->' ",  b.blog_name , " ' Blog")
        	else:

        		print(member.name , "Has No Blogs, But the func is just getting starting")

        		print()
        	
        	
    
    
 
    # member_id  = Member.query.get(4)

    # blog = 'This is the second blog belonging to flask, WELCOME'



    # if member_id:

    # 	member_blog = Blog(blog_name=blog, member_id=member_id.id)


    # try:

    # 	db.session.add(member_blog)

    # 	db.session.commit()

    # 	print("Blog added succesfully. ")

    # except SQLAlchemyError as e:

    # 	print(f"An error ocurred while trying to add the blog, Try agin {e}") 






     

if __name__ == '__main__':

	with app.app_context():
		db.create_all()
		#get_data()
		app.run(debug=True) 
		




 




