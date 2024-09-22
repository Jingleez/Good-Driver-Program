import mysql.connector

db = mysql.connector.connect(
    host="team13-rds.cobd8enwsupz.us-east-1.rds.amazonaws.com",
    user='admin',
    password='Cpsc4910_Team13!Rds',
    database='Team13_database'
)

print("CONNECTED TO MYSQL")

cursor = db.cursor()

print("Enter your username")
name = input()

cursor.execute("SELECT EXISTS(SELECT * FROM users WHERE UserName='"+name+"')")

myinfo = cursor.fetchall()
print(myinfo[0][0])

if(myinfo[0][0]):
    print("You are in the System!")
    cursor.execute("SELECT EXISTS( SELECT UserName, last_in FROM users WHERE last_in >(NOW() - INTERVAL 1 DAY) AND UserName = '"+name+"');")
    last_info = cursor.fetchall()
    if(last_info[0][0]):
        print("You have logged in in the past 24 hours, you may continue!")
        cursor.execute("SELECT driver_id FROM users WHERE UserName = '"+name+"'")
        fetched = cursor.fetchall()
        ID = str(fetched[0][0])
        print(ID) 

        print("Hey look at all this info I have on you! Creepy ya?")
        cursor.execute("SELECT * FROM driver WHERE driver_id ="+ID)
        last_info = cursor.fetchall()
        print(last_info)
    else:
        print("It has been 24 since you last logged in, you need to log in again")
else:
    print("You need to sign up.")

cursor.close()
db.close()
