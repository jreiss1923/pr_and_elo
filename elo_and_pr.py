import elo
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

kkr_elo_calc = elo.Elo(k_factor=32, rating_class=float, initial=1500, beta=200)

elo_database = mysql.connector.connect(
    host=os.getenv('HOST'),
    user=os.getenv('USERNAME_DB'),
    password=os.getenv('PASSWORD'),
    database=os.getenv("DB_NAME")
)

cursor = elo_database.cursor()


def add_user(username):
    try:
        query = "INSERT INTO elo (username, elo) VALUES ('" + username + "', 1500)"
        cursor.execute(query)

        elo_database.commit()

        print("Successfully added " + username + " to the PR")
    except Exception as e:
        print(repr(e))


def add_match(winner, loser, gw, gl):

    try:

        query = "INSERT INTO match_history (winner, loser, gw, gl) VALUES ('" + winner + "', '" + loser + "', " + str(gw) + ", " + str(gl) + ")"
        cursor.execute(query)

        query = "SELECT elo FROM elo WHERE username='" + winner + "'"
        cursor.execute(query)
        winner_elo = cursor.fetchall()

        query = "SELECT elo FROM elo WHERE username='" + loser + "'"
        cursor.execute(query)
        loser_elo = cursor.fetchall()

        elos = kkr_elo_calc.rate_1vs1(winner_elo[0][0], loser_elo[0][0])

        winner_elo = elos[0]
        loser_elo = elos[1]

        query = "UPDATE elo SET elo=" + str(winner_elo) + " WHERE username='" + winner + "'"
        cursor.execute(query)

        query = "UPDATE elo SET elo=" + str(loser_elo) + " WHERE username='" + loser + "'"
        cursor.execute(query)

        elo_database.commit()

        print("Successfully logged match between " + winner + "(" + str(gw) + ") and " + loser + "(" + str(gl) + ")")
    except Exception as e:
        print(repr(e))


def get_top_x(top_num):
    try:
        query = "SELECT username FROM elo ORDER BY elo DESC LIMIT " + str(top_num)
        cursor.execute(query)
        top_users = cursor.fetchall()
        top_users_list = []

        for sublist in top_users:
            list(sublist)
            for item in sublist:
                top_users_list.append(item)

        print("The top " + str(top_num) + " users are: " + str(top_users_list))
    except Exception as e:
        print(repr(e))


def reset_user(username):
    try:
        query = "UPDATE elo SET elo=1500 WHERE username='" + username + "'"
        cursor.execute(query)

        query = "DELETE FROM match_history WHERE winner='" + username + "' OR loser='" + username + "'"
        cursor.execute(query)

        elo_database.commit()

        print("Reset " + username + "'s elo and match history")
    except Exception as e:
        print(repr(e))


def delete_user(username):
    try:
        query = "DELETE FROM elo WHERE username='" + username + "'"
        cursor.execute(query)

        query = "DELETE FROM match_history WHERE winner='" + username + "' OR loser='" + username + "'"
        cursor.execute(query)

        elo_database.commit()

        print("Deleted " + username + "'s elo and match history")
    except Exception as e:
        print(repr(e))