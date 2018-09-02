# a file that import books.csv to the database
import os
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def create_books ():
	columns = """
		id SERIAL PRIMARY KEY,
		ISBN VARCHAR UNIQUE ,
		title VARCHAR,
		author VARCHAR,
		year VARCHAR
	"""
	db.execute(f"CREATE TABLE IF NOT EXISTS books ({columns});")
	db.commit()
	print("books table created")

def main ():
	create_books()
	file = open('books.csv')
	reader= csv.reader(file)
	for num,title,auth,yr in reader :
		db.execute("INSERT INTO books (ISBN,title,author,year) VALUES(:ISBN,:title,:author,:year)"
			,{"ISBN":num,"title":title,"author":auth,"year":yr})
		print(f"Added {num},{title},{auth},{yr} into books")
		
	# at the end of any change made on database , you should commit these changes
	db.commit()

if __name__ == "__main__":
	main()