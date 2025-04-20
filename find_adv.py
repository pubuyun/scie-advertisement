import requests
import random
from fetchinfo import cmsFetcher

API_KEY = "6d6093569ddde814c5d259127045d26d5eb306340dd5624023942b871aaf3f71"


def search_info(subject, level):
    match level:
        case "weak":
            query = f"{subject} tutoring"
        case "normal":
            query = f"{subject} online course"
        case "strong":
            query = f"{subject} competition"

    # Call Bing Images API through SerpApi
    params = {
        "engine": "bing_images",
        "q": query,
        "api_key": API_KEY,
    }

    response = requests.get("https://serpapi.com/search", params=params)
    result = response.json()

    if "images_results" in result and len(result["images_results"]) > 0:
        first_result = result["images_results"][0]
        return first_result["source"], first_result["original"]

    return None, None


def process_subjects(decision):
    ramdom_subject = random.choice(list(decision.keys()))
    subject = decision[ramdom_subject][0]
    level = decision[ramdom_subject][1]
    source_url, image_url = search_info(subject, level)
    if image_url and source_url:
        return {
            "subject": subject,
            "level": level,
            "image_url": image_url,
            "source_url": source_url,
        }
    return None


def calculate_subject_decisions(scores, referrals):
    decisions = {}
    for subject in scores:
        avg = sum(scores[subject]) / len(scores[subject])
        referral_score = 0
        if subject in referrals:
            for subject in referrals:
                for ref, is_positive in referrals[subject]:
                    if is_positive:
                        referral_score += 0.05  # positive +0.05
                    else:
                        referral_score -= 0.1  # negative -0.1

        final_score = round(avg, 2) + referral_score
        final_score = max(
            0.0, min(1.0, final_score)
        )  # make sure final_score is between 0 and 1
        final_score = round(final_score, 2)

        # classify the final score
        if final_score <= 0.3:
            category = "weak"
        elif final_score > 0.7:
            category = "strong"
        else:
            category = "normal"

        decisions[subject] = [subject, category]

    return decisions


if __name__ == "__main__":
    # Example usage
    fetcher = cmsFetcher(input("Input username: "), input("Input password: "))
    with open("captcha.png", "wb") as f:
        f.write(fetcher.login())
    captcha = input("Input captcha: ")
    fetcher.set_safecode(captcha)
    if fetcher.auth():
        print("Login successful.")
    else:
        print("Login failed.")
        exit()
    if fetcher.fetch_score() and fetcher.fetch_referrals():
        scores = fetcher.get_scores()
        referrals = fetcher.get_referrals()
        decisions = calculate_subject_decisions(scores, referrals)
        processed_decisions = process_subjects(decisions)
        print(processed_decisions)
    else:
        print("Failed to fetch data.")
