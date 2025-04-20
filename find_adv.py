import os
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from fetchinfo import cmsFetcher


def search_info(subject, level):
    query = f"{subject} {level} tutoring peer guidance competition assistance"
    search_url = f"https://www.google.com/search?q={query}&tbm=isch"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(search_url, headers=headers)
    if response.status_code != 200:
        return "No valid response", ""
    soup = BeautifulSoup(response.text, "html.parser")
    images = soup.find_all("img")
    img_url = ""
    if len(images) > 1:
        img_url = images[14]["src"]
        info_text = f"Resources for {subject} ({level} level). Consider online courses, study groups, or competitions."
    return info_text, img_url


def download_image(img_url, subject):
    if not img_url:
        return ""
    try:
        response = requests.get(img_url)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            img_path = f"images/{subject}.jpg"
            os.makedirs("images", exist_ok=True)
            image.save(img_path)
            return img_path
    except Exception:
        return ""
    return ""


def process_subjects(decision):
    for subject, level in decision.items():
        print(level)
        if level:
            info, img_url = search_info(subject, level)
            img_path = download_image(img_url, subject)
            decision[subject] = {"level": level, "info": info, "image": img_path}
    return decision


def calculate_subject_decisions(scores, referrals):
    decisions = {}
    for subject in scores:
        # calclulate average
        average = sum(scores[subject]) / len(scores[subject])

        # adjust score by negative referral
        negative_count = referrals[subject].count(False)
        finalscore = max(
            0.0, average - negative_count * 0.1
        )  # prevent final score to be less than 0
        finalscore = round(finalscore, 1)  # round final score
        # categorizing
        if finalscore <= 0.3:
            category = "weak"
        elif finalscore > 0.7:
            category = "strong"
        else:
            category = "normal"
            decisions[subject] = [finalscore, category]

    return decisions


if __name__ == "__main__":
    # Example usage
    # fetcher = cmsFetcher(input("Input username: "), input("Input password: "))
    # fetcher = cmsFetcher("s24425", "wj8u0n44")
    # with open("captcha.png", "wb") as f:
    #     f.write(fetcher.login())
    # captcha = input("Input captcha: ")
    # fetcher.set_safecode(captcha)
    # if fetcher.auth():
    #     print("Login successful.")
    # else:
    #     print("Login failed.")
    #     exit()
    # if fetcher.fetch_score() and fetcher.fetch_referrals():
    # scores = fetcher.get_scores()
    # referrals = fetcher.get_referrals()
    scores = {
        "Computer Science": [
            0.97,
            0.8,
            1.0,
            1.0,
            1.0,
            0.97,
            0.95,
            1.0,
            1.0,
            1.0,
            0.87,
            1.0,
        ],
        "Biology": [
            1.0,
            0.97,
            1.0,
            0.93,
            0.89,
            0.96,
            0.95,
            0.94,
            0.97,
            0.88,
            0.97,
            0.97,
        ],
        "PE": [0.85, 0.83, 0.81, 0.85, 0.85, 0.85],
        "Economics": [
            0.88,
            0.85,
            0.86,
            0.88,
            0.94,
            0.88,
            0.8,
            1.0,
            0.84,
            0.95,
            0.9375,
            0.875,
        ],
        "Mathematics": [
            1.0,
            0.97,
            0.95,
            0.93,
            0.98,
            0.99,
            1.0,
            0.97,
            0.8,
            0.9,
            1.0,
            0.88,
        ],
        "Physics": [0.95, 0.95, 0.971, 0.95, 0.85, 0.95, 1.0, 1.0, 0.85, 0.914, 0.971],
        "English": [
            0.9,
            0.9,
            0.85,
            0.8,
            0.77,
            0.6346153846153846,
            0.9,
            0.9,
            0.8,
            0.8,
            0.83,
            0.65,
            0.9,
            0.875,
            0.93,
            0.9333333333333333,
            0.93,
            0.9,
            0.7,
            0.6,
        ],
        "Chemistry": [
            0.9333333333333333,
            0.8421052631578947,
            1.0,
            1.0,
            0.9571428571428572,
            0.85,
            1.0,
            1.0,
            0.8378378378378378,
            0.9166666666666666,
            1.0,
        ],
        "Chinese": [0.92, 0.89, 0.9, 1.0, 0.85, 0.92, 0.78, 0.86, 0.85],
    }
    referrals = {
        "Biology": [
            (
                "Willes achieved 100% in his most recent biology topic test. Congratulations!",
                True,
            )
        ],
        "Economics": [
            (
                "Excellent work in today's lesson where you attempted all tasks at the best of your ability worked well in a team and challenged yourself to work harder. Keep up the great work you are doing in Economics! Well done!",
                True,
            ),
            (
                "HW incomplete - ATL survey not completed which will have a detrimental impact on ATL 10% grade",
                False,
            ),
            ("Homework was not attempted - 24 hour extension provided", False),
            (
                "Student did not complete the HW, unfortunately. 24 hour extension provided as per the school HW policy",
                False,
            ),
            (
                "A truly exceptional performance in the challenging 5th Economics test where Wiles earned full marks. Hard work pays off Wiles so keep pushing yourself to keep on improving performance. Again MASSIVE WELL DONE!!",
                True,
            ),
        ],
        "Physics": [
            (
                "Willes scored full marks in our latest practical test, which shows his commitment to Physics and to his academics. Keep working hard Willes!",
                True,
            ),
            (
                "Willes achieved an excellent result in the latest Physics assessment. This result shows his commitment to succeed in this subject. Keep up with the good work Willes!",
                True,
            ),
        ],
        "Chinese": [
            (
                "Willes has not only made impressive sense of the text at this stage of the reading task but has also shown personalized understanding and expression, keep it up.",
                True,
            )
        ],
        "Biology": [
            (
                "Congratulations on scoring a 97% of topic test 2! Willes always pays attention in class and participates in discussions. Keep it up!",
                True,
            )
        ],
    }
    decisions = calculate_subject_decisions(scores, referrals)
    processed_decisions = process_subjects(decisions)
    print(processed_decisions)
# else:
#     print("Failed to fetch data.")
