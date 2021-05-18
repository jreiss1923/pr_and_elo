from __future__ import print_function
import elo
import mysql.connector
from dotenv import load_dotenv
import os
import argparse
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# load hidden variables from .env file located in same folder
load_dotenv()

# uses 32 k factor as the classical standard for chess and for a (imo) good-sized swing in points
kkr_elo_calc = elo.Elo(k_factor=32, rating_class=float, initial=1500, beta=200)

# if you want to use this for yourself, replace this with your own mysql credentials
# connect to mysql db locally
elo_database = mysql.connector.connect(
    host=os.getenv('HOST'),
    user=os.getenv('USERNAME_DB'),
    password=os.getenv('PASSWORD'),
    database=os.getenv("DB_NAME")
)

cursor = elo_database.cursor()

# spreadsheet data
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
RANGE_NAME_ELO = 'ELO!A3:E1000'
RANGE_NAME_MATCHES = 'Match History!A3:D1000'


# log into google sheets using given credentials
def login_sheets():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    created_service = build('sheets', 'v4', credentials=creds)
    return created_service


service = login_sheets()


# returns data from spreadsheet
def get_sheet_data(range_code):
    global service
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=range_code).execute()
    values = result.get('values', [])
    return values


# appends data to first row after end of range code
def append_sheet_data(values, range_code):
    global service
    body = {
        'values': values
    }
    sheet = service.spreadsheets()
    sheet.values().append(spreadsheetId=SPREADSHEET_ID, range=range_code, body=body, valueInputOption='RAW').execute()


# updates data in range code
def update_sheet_data(values, range_code):
    global service
    body = {
        'values': values
    }
    sheet = service.spreadsheets()
    sheet.values().update(spreadsheetId=SPREADSHEET_ID, range=range_code, body=body, valueInputOption='RAW').execute()


# adds user to the database with a default starting ELO of 1500
def add_user(username):
    try:
        query = "INSERT INTO elo (username, elo, pr) VALUES ('" + username + "', 1500, 1)"
        cursor.execute(query)

        elo_database.commit()

        values = [
            [
                username, 1500, 0
            ]
        ]

        append_sheet_data(values, RANGE_NAME_ELO)
        update_pr()

        print("Successfully added " + username + " to the PR")
    except Exception as e:
        print("Could not add " + username + " to PR. Check if they already exist.")
        print(repr(e))


# gets the row, column of elo or matchmaking for that user
def find_elo(row, elo_data, username):
    winner_string = "ELO!"

    for elo_row in elo_data:
        if username in elo_row:
            if row == "ELO":
                winner_string += "B" + str(elo_data.index(elo_row) + 3)
            elif row == "PR":
                winner_string += "C" + str(elo_data.index(elo_row) + 3)
            elif row == "row":
                winner_string += "A" + str(elo_data.index(elo_row)+3) + ":C" + str(elo_data.index(elo_row)+3)

    return winner_string


# adds a match to the db and updates elo. Assumes both users exist already
def add_match(winner, loser, gw, gl):
    try:

        values = [
            [
                winner, loser, gw, gl
            ]
        ]

        query = "INSERT INTO match_history (winner, loser, gw, gl) VALUES ('" + winner + "', '" + loser + "', " + str(
            gw) + ", " + str(gl) + ")"
        cursor.execute(query)

        append_sheet_data(values, RANGE_NAME_MATCHES)

        query = "SELECT elo FROM elo WHERE username='" + winner + "'"
        cursor.execute(query)
        winner_elo = cursor.fetchall()

        elo_data = get_sheet_data(RANGE_NAME_ELO)
        winner_elo_str = find_elo("ELO", elo_data, winner)
        loser_elo_str = find_elo("ELO", elo_data, loser)

        query = "SELECT elo FROM elo WHERE username='" + loser + "'"
        cursor.execute(query)
        loser_elo = cursor.fetchall()

        elos = kkr_elo_calc.rate_1vs1(winner_elo[0][0], loser_elo[0][0])

        winner_elo = elos[0]
        loser_elo = elos[1]

        winner_values = [
            [
                winner_elo
            ]
        ]

        loser_values = [
            [
                loser_elo
            ]
        ]

        query = "UPDATE elo SET elo=" + str(winner_elo) + " WHERE username='" + winner + "'"
        cursor.execute(query)

        query = "UPDATE elo SET elo=" + str(loser_elo) + " WHERE username='" + loser + "'"
        cursor.execute(query)

        elo_database.commit()

        update_sheet_data(winner_values, winner_elo_str)
        update_sheet_data(loser_values, loser_elo_str)

        update_pr()

        print("Successfully logged match between " + winner + "(" + str(gw) + ") and " + loser + "(" + str(gl) + ")")
    except (Exception, IndexError) as e:
        print("Was not able to log match: Check to see if both users are in the PR")
        print(repr(e))


# returns a list of the top x users by ELO
def list_top_x(top_num):
    try:
        query = "SELECT username FROM elo ORDER BY elo DESC LIMIT " + str(top_num)
        cursor.execute(query)
        top_users = cursor.fetchall()
        top_users_list = []

        for sublist in top_users:
            list(sublist)
            for item in sublist:
                top_users_list.append(item)

        return top_users_list
    except Exception as e:
        print(repr(e))


# gets the top x users by ELO. If there are less than x users, just gets all.
def get_top_x(top_num):
    top_users_list = list_top_x(top_num)
    print("The top " + str(len(top_users_list)) + " users are: " + str(top_users_list))


# updates the power ranking order for users
def update_pr():
    elo_data = get_sheet_data(RANGE_NAME_ELO)
    top_list = list_top_x(1000)
    for user in top_list:

        query = "UPDATE elo SET pr=" + str(top_list.index(user) + 1) + " WHERE username='" + user + "'"
        cursor.execute(query)

        elo_database.commit()

        pr_square = find_elo("PR", elo_data, user)
        values = [
            [
                top_list.index(user) + 1
            ]
        ]
        update_sheet_data(values, pr_square)


# resets user's ELO, but not their match history
# keeps track of matches to show why elo might jump
# should use if temporarily banning or suspected cheating/wintrading has occurred
def reset_user(username):
    try:
        query = "UPDATE elo SET elo=1500 WHERE username='" + username + "'"
        cursor.execute(query)

        elo_data = get_sheet_data(RANGE_NAME_ELO)
        elo_range = find_elo("ELO", elo_data, username)

        print(elo_range)

        values = [
            [
                1500
            ]
        ]

        update_sheet_data(values, elo_range)

        elo_database.commit()

        update_pr()

        print("Reset " + username + "'s elo")
    except Exception as e:
        print(repr(e))


# deletes user
# keeps match history to demonstrate why elo changed for another user
def delete_user(username):
    try:
        query = "DELETE FROM elo WHERE username='" + username + "'"
        cursor.execute(query)

        elo_data = get_sheet_data(RANGE_NAME_ELO)
        elo_range = find_elo("row", elo_data, username)

        values = [
            [
                "", "", ""
            ]
        ]

        update_sheet_data(values, elo_range)

        elo_database.commit()

        update_pr()

        print("Deleted " + username + "'s elo")
    except Exception as e:
        print(repr(e))


def initialize_parser():
    # these are the commands for the CLI - only works if you have your own MySQL db (for now)
    parser = argparse.ArgumentParser()

    # elo_and_pr {-d | -deleteUser} [username]
    parser.add_argument("-d", "-deleteUser", nargs='?',
                        help="Deletes a user from the PR", type=str)

    # elo_and_pr {-r | -resetUser} [username]
    parser.add_argument("-r", "-resetUser", nargs='?',
                        help="Resets a user's ELO to 1500", type=str)

    # elo_and_pr {-u | -addUser} [username]
    parser.add_argument("-u", "-addUser", nargs='?', help="Adds a user to the PR with a default ELO of 1500", type=str)

    # elo_and_pr {-t | -getTop} [length]
    parser.add_argument("-t", "-getTop", nargs='?', help="Gets the top x users in the PR", type=int)

    # elo_and_pr {-m | -addMatch} [winner] {-m | -addMatch} [loser] {-m | -addMatch} [won] {-m | -addMatch} [lost]
    parser.add_argument("-m", "-addMatch", action="append", nargs='?',
                        help="Adds a match to the PR and changes ELO: Usage: -m [winner], -m [loser], -m [winner_games_won], -m [loser_games_won]",
                        type=str)

    args = parser.parse_args()

    # wish this datatype was better :(
    if args.d is not None:
        delete_user(args.d)
    if args.r is not None:
        reset_user(args.r)
    if args.u is not None:
        add_user(args.u)
    if args.t is not None:
        get_top_x(args.t)
    if args.m is not None:
        add_match(args.m[0], args.m[1], args.m[2], args.m[3])


def main():
    initialize_parser()


main()