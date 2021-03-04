import elo
import mysql.connector
from dotenv import load_dotenv
import os
import argparse

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
    except (Exception, IndexError) as e:
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


parser = argparse.ArgumentParser()
parser.add_argument("-d", "-deleteUser", nargs='?', help="Deletes a user from the PR, as well as deleting all their matches played", type=str)
parser.add_argument("-r", "-resetUser", nargs='?', help="Resets a user's ELO to 1500 as well as deleting all their matches played", type=str)
parser.add_argument("-u", "-addUser", nargs='?', help="Adds a user to the PR with a default ELO of 1500", type=str)
parser.add_argument("-t", "-getTop", nargs='?', help="Gets the top x users in the PR", type=int)
parser.add_argument("-m", "-addMatch", action="append", nargs='?', help="Adds a match to the PR and changes ELO: Usage: -m [winner], -m [loser], -m [winner_games_won], -m [loser_games_won]", type=str)

args = parser.parse_args()

if args.d is not None:
    delete_user(args.d)
if args.r is not None:
    reset_user(args.r)
if args.u is not None:
    add_user(args.u)
if args.t is not None:
    get_top_x(args.t)
if args.m is not None:
    add_match("jreiss1923", "SmashDee", 2, 1)

