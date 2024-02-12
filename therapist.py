from typing import Optional
from db import USERS
import openai
COST_PER_TOKEN = 0.000002

def create_new_user(ip: str, email: Optional[str] = None):
    new_user = {"ip": ip, "email": email, "credits": 5}
    USERS.insert_one(new_user)
    return new_user

def add_email_and_credits(user, email: str):
    user["email"] = email
    user["credits"] += 10
    USERS.update_one({"_id": user["_id"]}, {"$set": user})
    return user

def therapize(user_input: dict, message_history: list, email: Optional[str] = None):
    user = USERS.find_one({"email": email})
    if message_history == []:
        summary = user["summary"] if user.get("summary") else ""
        message_history.append({"role": "system", "content": therapy_prompt(summary)})
        
    user_input = {"role": "user", "content": user_input}    
    message_history.append(user_input)
    if user:
        if len(user["message_history"]) % 3 == 0:
            if ("summary" not in user and len(user["message_history"])) > 3:
                summary, usage = summarize_messages(user["message_history"])
                print("full summary")
            else:
                last_3_messages = user["message_history"][-3:]
                summary, usage = summarize_messages(last_3_messages)
                print("partial summary")
            user["summary"] = summary + user["summary"] if user.get("summary") else summary
            print(summary)
            user["total_cost"] += usage * COST_PER_TOKEN
            if len(user["summary"]) > 4000:
                user["summary"], summary_usage = summarize_summary(user["summary"])
                print("summarized summary")
                user["total_cost"] += summary_usage * COST_PER_TOKEN
            USERS.update_one({"_id": user["_id"]}, {"$set": user})
        
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=message_history,
        max_tokens=256,
    )

    response = completion.choices[0].message.content
    usage = completion.usage["total_tokens"]
    print(completion.usage)
    therapist_response = {"role": "assistant", "content": response}
    message_history.append(therapist_response)
    return [response, message_history, usage, [user_input, therapist_response]]


def summarize_messages(messages) -> str:
    summary = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content":f"Summarize the last three messages, while keeping emotional details, and key personal info. Return a single string. These are the messages:\n{messages}\n\nSummary:",}],
        max_tokens=256,
    )
    return summary.choices[0].message.content, summary.usage["total_tokens"]

def summarize_summary(summary: str) -> str:
    summary = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=[{"role": "system", "content": f"Summarize the summary, while keeping emotional details, and key personal info. Return a single string.\n\nSummary:\n{summary}\n\nSummary of summary:",}],
        max_tokens=256,
    )
    return summary.choices[0].message.content, summary.usage["total_tokens"]