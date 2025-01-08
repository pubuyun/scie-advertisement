# function encryption(){
#         var f=$("#psid").val();
#         var g=$("#passwd").val();
#         $.ajax({
#             url:"/user/encryption/",
#             type:"POST",
#             secureuri:false,
#             cache:false,
#             async:false,
#             dataType:"json",
#             data:"psid="+f,
#             success:function(a,b){
#                 if(a["status"]=="OK"){
#                     var c=a["salt"];
#                     var d=c+$.md5(c+g).toUpperCase();
#                     $("#passwd").val(d);
#                     $("#psid_flag").val("ok");
#                     $("#nosence").val(a["nosence"])
#                 }else{
#                     $("#psid_info_span").html(a["info"])
#                 }
#             },
#             error:function(a,b,e){
#                 if(e){
#                     $("#psid_info_span").html(e)
#                 }
#             }
#         })
#     }

import requests
import time
import hashlib
from bs4 import BeautifulSoup

def fetchinfo(psid, passwd):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://www.alevel.com.cn',
        'Host': 'www.alevel.com.cn',    
        'Priority': 'u=0, i',
    }

    session = requests.Session()

    mainurl = "https://www.alevel.com.cn/"
    encrypturl = "https://www.alevel.com.cn/user/encryption/"
    loginurl = "https://www.alevel.com.cn/login/"
    scoreurl = f'https://www.alevel.com.cn/user/{psid}/assessment/list/'
    referralurl = f'https://www.alevel.com.cn/user/{psid}/referralcomment'

    session.headers.update(headers)
    response = session.get(loginurl)
    print('cookies', session.cookies.get_dict())
    time.sleep(0.2)

    response = session.post(encrypturl, data=f'psid={psid}')
    if response.status_code == 200:
        ResponseData = response.json()
        if ResponseData['status'] == "OK":
            salt = ResponseData['salt']
            PasswdEncrypted = salt + hashlib.md5((salt + passwd).encode()).hexdigest().upper()
            Nosence = ResponseData['nosence']
        else:
            print("Encrypt Failed: ", ResponseData['info'])
            return False
    else:
        print(f'[{response.status_code}] ', response.text)
        return False

    RequestData = {'nosence': Nosence, 'psid': psid, 'passwd': PasswdEncrypted, 'rememberpsid': 1, 'post':"登 录/Login"}
    print(RequestData)
    response = session.post(loginurl, data=RequestData)
    if response.status_code == 200 :
        if '登录' in response.text:
            print("Login Failed: Password error or limit exceeded.")
            return False
        cookies = session.cookies.get_dict()
        print('Login successfully!')
        print("id:", psid)
        print("Login cookies", cookies)
    else:
        print(f'[{response.status_code}] ', response.text)
        
    response = session.get(scoreurl)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        score_cells = soup.find_all(lambda tag: (
            (tag.name == 'td' and tag.get('style') == "color:red;font-size:20px;line-height:30px;text-align: left;")
            or
            (tag.name == 'tr' and tag.get('bgcolor') == "#76EE00")
    ))
        results = {'English': [], 'Biology': [], 'Chemistry': [], 'Physics': [], 'Mathematics': [], 'Computer Science': []}
        referrals = {'English': [], 'Biology': [], 'Chemistry': [], 'Physics': [], 'Mathematics': [], 'Computer Science': []}
        # for every bgcolor="#76EE00" <tr> there are 7 <td>, the fifth <td> is the score, the sixth <td> is the full score
        for score_cell in score_cells:
            if score_cell.name == 'td':
                currentSubject = next((subject for subject in results.keys() if subject in score_cell.text), None)
            # if currentSubject=None, jump to next iteration
            if currentSubject is None:
                continue
            if score_cell.name == 'tr':     
                scores = score_cell.find_all('td')
                # remove non-digit characters except dot
                score = ''.join([char for char in scores[4].text if char.isdigit() or char == '.'])
                full_score = ''.join([char for char in scores[5].text if char.isdigit() or char == '.'])
                if score and full_score:
                    results[currentSubject].append(float(score)/float(full_score))
    else:
        print(f'[{response.status_code}] ', response.text)
        return False
    
    response = session.get(referralurl)
    # find all <a>, text = Detail
    soup = BeautifulSoup(response.text, 'html.parser')
    referral_cells = soup.find_all('a', text='Detail')
    # get the href of every <a>
    referral_links = [mainurl+cell.get('href') for cell in referral_cells]
    for link in referral_links:
        response = session.get(link)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            referral = soup.find('p', text=True).string
            subject = soup.find('strong').string
            if subject in referrals.keys():
                referrals[subject].append(referral)
        else:
            print(f'[{response.status_code}] ', response.text)
            return False
    return results, referrals

if __name__ == "__main__":
    psid = input("Input username: ")
    passwd = input("Input password: ")
    print(fetchinfo(psid, passwd))  