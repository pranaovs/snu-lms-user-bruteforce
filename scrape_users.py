#!./.venv/bin/python

# Python script to scrape users in a particular course in SNU LMS (Moodle)

import sys

import requests
from bs4 import BeautifulSoup

import csv

LOGIN_URL = "https://lms.snuchennai.edu.in/login/index.php"

# Predefined message displayed when login successful and credentials incorrect
# May change in future
WELCOME_MSG = "Welcome to the Learning Management System (LMS) at Shiv Nadar University, Chennai !!"
ERROR_MSG = "Invalid login, please try again"

COURSE_URL = "https://lms.snuchennai.edu.in/user/index.php?page=0&perpage=5000&contextid=0&id={id}&newcourse&tsort=firstname&tdir=4"


def login(session, username, password):
    # Get login token from page
    login_token = BeautifulSoup(session.get(LOGIN_URL).text, "html.parser").find(
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

    response = session.post(LOGIN_URL, data=data)
    if checkLogin(response):
        return session
    else:
        raise Exception("Authentication failed")


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
        raise Exception("Unknown error while checking auth session")


def getUsers(session, courseId):
    response = session.get(COURSE_URL.format(id=courseId))

    # Only continue if course found
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        # items = soup.findAll("table")[0].findAll("tr")

        # print(soup.find(id="participantsform").p.text)

        # Get total participants count
        participants = int(
            soup.select_one(
                "#participantsform > div:nth-child(1) > p:nth-child(3)"
            ).text.split()[0]  # type:ignore
        )

        userList = []

        # Iterate through each participant number obtained from total participant count
        for i in range(0, participants):
            userUrl = (
                soup.select_one(
                    f"#user-index-participants-{courseId}_r{i}_c0 > a:nth-child(1)"
                ).get("href")  # type:ignore
            )
            # Add the user profile url to the list
            userList.append(userUrl)

        return userList

    else:
        raise requests.exceptions.InvalidURL


def getUserEmail(session, url):
    response = session.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Page inconsistent. Some have email in email section, some have names.
    try:
        userEmail = soup.select_one(
            "section.node_category:nth-child(1) > div:nth-child(1) > ul:nth-child(2) > li:nth-child(1) > dl:nth-child(1) > dd:nth-child(2) > a:nth-child(1)"
        ).text  # type:ignore
    except AttributeError:
        try:
            userEmail = soup.select_one(".no-overflow").text  # type:ignore
        except AttributeError:
            userEmail = ""

    return userEmail


def listToCsv(data: list[str], filename="users.csv"):
    with open(filename, "w+") as f:
        writer = csv.writer(f)
        writer.writerow(data)


def main():
    # Provide arguments
    try:
        username = sys.argv[1]
        password = sys.argv[2]

        # Enter only the course id
        # Example: https://lms.snuchennai.edu.in/course/view.php?id={id}
        courseId = sys.argv[3]

    except IndexError:
        print("Required arguments not provided: <username> <password> <id>")
        return

    with requests.session() as session:
        authSession = login(session, username, password)

        emailList = []

        for userLink in getUsers(authSession, courseId):
            userEmail = getUserEmail(session, userLink)

            if userEmail != "":
                print(userEmail)
                emailList.append(userEmail)
            else:
                print(f"Unable to find email for user {userLink}")

        listToCsv(emailList)


if __name__ == "__main__":
    main()
