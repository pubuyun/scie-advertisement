# encryption function of CMS login
# function encryption(){
#         var f=$("#username").val();
#         var g=$("#passwd").val();
#         $.ajax({
#             url:"/user/encryption/",
#             type:"POST",
#             secureuri:false,
#             cache:false,
#             async:false,
#             dataType:"json",
#             data:"username="+f,
#             success:function(a,b){
#                 if(a["status"]=="OK"){
#                     var c=a["salt"];
#                     var d=c+$.md5(c+g).toUpperCase();
#                     $("#passwd").val(d);
#                     $("#username_flag").val("ok");
#                     $("#nosence").val(a["nosence"])
#                 }else{
#                     $("#username_info_span").html(a["info"])
#                 }
#             },
#             error:function(a,b,e){
#                 if(e){
#                     $("#username_info_span").html(e)
#                 }
#             }
#         })
#     }

import requests
import time
import hashlib
import re
from bs4 import BeautifulSoup
import getpass


class cmsFetcher:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://www.alevel.com.cn",
        "Host": "www.alevel.com.cn",
        "Priority": "u=0, i",
    }
    mainurl = "https://www.alevel.com.cn/"
    encrypturl = "https://www.alevel.com.cn/user/encryption/"
    loginurl = "https://www.alevel.com.cn/login/"

    def __init__(self, username, passwd):
        self.username = username
        self.passwd = passwd
        self.scoreurl = f"https://www.alevel.com.cn/user/{username}/assessment/list/"
        self.referralurl = f"https://www.alevel.com.cn/user/{username}/referralcomment"
        self.safecode = None
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def login(self):
        response = self.session.get(self.loginurl)
        if response.status_code == 200:
            # check if the page contains "登录" (login) to see if the login page is loaded
            if "登录" not in response.text:
                print("Login page not loaded.")
                return False
            # get the src of the image with id="safecode"
            soup = BeautifulSoup(response.text, "html.parser")
            safecode_img = soup.find("img", id="safecode")
            if safecode_img:
                safecode_src = self.mainurl + safecode_img.get("src")
                response = self.session.get(safecode_src)
                if response.status_code == 200:
                    return True, response.content
            else:
                return False, self.auth(with_safecode=False)

        else:
            print(f"[{response.status_code}] ", response.text)
            return False

    def set_safecode(self, safecode):
        self.safecode = safecode

    def auth(self, with_safecode=True):
        response = self.session.post(self.encrypturl, data=f"psid={self.username}")
        if response.status_code == 200:
            ResponseData = response.json()
            if ResponseData["status"] == "OK":
                salt = ResponseData["salt"]
                PasswdEncrypted = (
                    salt
                    + hashlib.md5((salt + self.passwd).encode()).hexdigest().upper()
                )
                Nosence = ResponseData["nosence"]
            else:
                print("Encrypt Failed: ", ResponseData["info"])
                return False
        else:
            print(f"[{response.status_code}] ", response.text)
            return False

        RequestData = {
            "nosence": Nosence,
            "psid": self.username,
            "passwd": PasswdEncrypted,
            "rememberusername": 1,
            "post": "登 录/Login",
        }
        if with_safecode:
            RequestData["authnum"] = self.safecode

        response = self.session.post(self.loginurl, data=RequestData)
        if response.status_code == 200:
            if "登录" in response.text:
                print("Login Failed: Password error or limit exceeded.")
                return False
            cookies = self.session.cookies.get_dict()
            print("Login successfully!")
            print("id:", self.username)
            print("Login cookies", cookies)
            return True
        else:
            print(f"[{response.status_code}] ", response.text)
            return False

    def fetch_score(self):
        response = self.session.get(self.scoreurl)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            score_cells = soup.find_all(
                lambda tag: (
                    (
                        tag.name == "td"
                        and tag.get("style")
                        == "color:red;font-size:20px;line-height:30px;text-align: left;"  # subject
                    )
                    or (tag.name == "tr" and tag.get("bgcolor") == "#76EE00")  # score
                )
            )
            results = {}

            # for every bgcolor="#76EE00" <tr> there are 7 <td>, the fifth <td> is the score, the sixth <td> is the full score
            for score_cell in score_cells:
                if score_cell.name == "td":  # the cell contains subject name
                    currentSubject = score_cell.text.split("-")[0].strip()
                    results[currentSubject] = []
                if score_cell.name == "tr":  # the cell contains score
                    scores = score_cell.find_all("td")
                    # remove non-digit characters except dot
                    score = "".join(
                        [
                            char
                            for char in scores[4].text  # mark
                            if char.isdigit() or char == "."
                        ]
                    )
                    full_score = "".join(
                        [
                            char
                            for char in scores[5].text  # outof
                            if char.isdigit() or char == "."
                        ]
                    )
                    if score and full_score:
                        results[currentSubject].append(float(score) / float(full_score))
        else:
            print(f"[{response.status_code}] ", response.text)
            return False
        self.scores = results
        return True

    def fetch_referrals(self):
        referrals = {}
        response = self.session.get(self.referralurl)

        # find all <a>, text = Detail
        soup = BeautifulSoup(response.text, "html.parser")
        referral_cells = soup.find_all("a", text="Detail")
        # get the href of every <a>
        referral_links = [self.mainurl + cell.get("href") for cell in referral_cells]

        for link in referral_links:
            response = self.session.get(link)
            if response.status_code == 200:
                try:
                    soup = BeautifulSoup(response.text, "html.parser")
                    referral = soup.find("p", text=True).text
                    subject = soup.find_all("strong")[
                        0
                    ].text  # the first <strong> is the subject
                    categories = soup.find_all("strong")[
                        1
                    ].text  # the second <strong> is the categories
                    categories = categories.split(",")[1].strip()
                    positive = "Area of Concern" not in categories
                    if subject not in referrals:
                        referrals[subject] = []
                    referrals[subject].append((referral, positive))
                except Exception as e:
                    print(f"Error parsing referral: {e}")
                    continue
            else:
                print(f"[{response.status_code}] ", response.text)
                return False

        self.referrals = referrals
        return True

    def get_scores(self):
        return self.scores

    def get_referrals(self):
        return self.referrals


if __name__ == "__main__":
    usrname = input("Input username: ")
    password = getpass.getpass("Input password: ")
    cms_fetcher = cmsFetcher(usrname, password)
    needs_captcha, captcha_image = cms_fetcher.login()
    if needs_captcha:
        with open("captcha.png", "wb") as f:
            f.write(captcha_image)
        print("Captcha image saved as captcha.png")
        captcha = input("Input captcha: ")
        cms_fetcher.set_safecode(captcha)
        if not cms_fetcher.auth():
            print("Authentication failed: Wrong captcha or session expired")
            exit(1)
    else:
        print("No captcha needed, login successful!")
    if cms_fetcher.fetch_score():
        print(cms_fetcher.get_scores())
    if cms_fetcher.fetch_referrals():
        print(cms_fetcher.get_referrals())
