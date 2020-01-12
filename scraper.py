#!/usr/bin/python3
import requests, base64, json, pickle, argparse
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser(
    description="Download all of the correct submission by a user on HackerRank. By @0xecho"
)
parser.add_argument(
    "username", metavar="username", help="Username of the HackerRank account"
)
parser.add_argument(
    "password", metavar="password", help="Password of the HackerRank account"
)

args = parser.parse_args()
USERNAME = args.username
PASSWORD = args.password

main_session = requests.Session()
main_session.headers[
    "User-Agent"
] = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:70.0) Gecko/20100101 Firefox/70.0"

response = main_session.get("http://www.hackerrank.com/auth/login")

text = BeautifulSoup(response.text, features="lxml")

csrf_tag = text.find("meta", {"id": "csrf-token"})

csrf_token = csrf_tag["content"]

main_session.headers["X-CSRF-Token"] = csrf_token

login_data = {
    "login": USERNAME,
    "password": PASSWORD,
    "remember_me": False,
    "fallback": True,
}

response = main_session.post("https://www.hackerrank.com/auth/login", data=login_data)

response_data = json.loads(response.text)

assert response_data["status"], "[-] Login Failed \n Incorrect Username or Password"

print("[*] Login Successful")
print("[*] Getting Questions")

main_session.headers["X-CSRF-Token"] = response_data["csrf_token"]

question_models = []
cursor = ""
while True:
    resp = main_session.get(
        f"http://www.hackerrank.com/rest/hackers/{USERNAME}/recent_challenges?limit=5&cursor={cursor}&response_version=v2"
    )
    resp_data = json.loads(resp.text)
    cursor = resp_data["cursor"]
    question_models.append(resp_data["models"])
    if resp_data["last_page"]:
        break

questions = []

for i in question_models:
    for j in i:
        questions.append(j)

submissions = []

print("[*] Getting Submissions")

for i in questions:
    resp = main_session.get(
        "https://www.hackerrank.com/rest/contests/master/challenges/{}/submissions/?offset=0&limit=1000".format(
            i["ch_slug"]
        )
    )
    resp_data = json.loads(resp.text)
    submissions.append(resp_data)

accepted_solutions = []

print("[*] Filtering Submissions")

for i in submissions:
    for j in i["models"]:
        slug = j["challenge"]["slug"]
        if j["status"] == "Accepted":
            accepted_solutions.append((slug, j["id"]))
            break

temp_map = {}

EXTENSIONS = {
    "cpp": "cpp",
    "python3": "py",
    "python": "py",
    "pypy": "py",
    "bash": "sh",
}

print("[*] Saving Files")

for i in accepted_solutions:
    slug, ch_id = i
    resp = main_session.get(
        f"https://www.hackerrank.com/rest/contests/master/challenges/{slug}/submissions/{ch_id}"
    )
    resp_data = json.loads(resp.text)
    file_lang = resp_data["model"]["language"]
    file_ext = EXTENSIONS.get(file_lang, file_lang)
    count = temp_map.get(slug, 0)
    file_name = slug
    if count:
        file_name += "_" + str(count)
    file_name += "." + file_ext
    with open(file_name, "w") as f:
        f.write(resp_data["model"]["code"])

print("[+] Finished....")
print("[+] Enjoy")
