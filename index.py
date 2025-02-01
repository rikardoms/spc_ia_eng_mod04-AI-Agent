import json
import os
import re
import requests
from dotenv import load_dotenv, dotenv_values
from pprint import pprint
from openai import OpenAI
from urllib.request import urlopen


load_dotenv()

openai_obj = OpenAI(api_key=os.getenv("openai_apikey"))



def get_current_location():
    d = str(urlopen('http://checkip.dyndns.com/')
            .read())

    response = requests.post("http://ip-api.com/batch", json=[
        {"query": re.compile(r'Address: (\d+\.\d+\.\d+\.\d+)').search(d).group(1)}
        ]).json()

    return response[0]["city"]+', '+ response[0]["region"]+', '+response[0]["country"]


def get_weather():
    return json.dumps({
        "temperature": 78,
        "unit":"F",
        "forecast": "Sunny"
    })


known_actions = {
    "getCurrentWeather": get_weather,
    "getLocation": get_current_location
}

systemPrompt = """You cycle through Thought, Action, PAUSE, Observation. At the end of the loop you output a final Answer. Your final answer should be highly specific to the observations you have from running
"
the actions.
1. Thought: Describe your thoughts about the question you have been asked.
2. Action: run one of the actions available to you - then return PAUSE.
3. PAUSE
4. Observation: will be the result of running those actions.

Available actions:
- getCurrentWeather: 
    E.g. getCurrentWeather: Salt Lake City
    Returns the current weather of the location specified.
- getLocation:
    E.g. getLocation: null
    Returns user's location details. No arguments needed.

Example session:
Question: Please give me some ideas for activities to do this afternoon.
Thought: I should look up the user's location so I can give location-specific activity ideas.
Action: getLocation: null
PAUSE

You will be called again with something like this:
Observation: "New York City, NY"

Then you loop again:
Thought: To get even more specific activity ideas, I should get the current weather at the user's location.
Action: getCurrentWeather: New York City
PAUSE

You'll then be called again with something like this:
Observation: { location: "New York City, NY", forecast: ["sunny"] }

You then output:
Answer: <Suggested activities based on sunny weather that are highly specific to New York City and surrounding areas.>
"""

def agent(query):
    messages = [
            {
                "role":"system",
                "content":systemPrompt
            },
            {
                "role":"user",
                "content":query
            }
        ]
   
    MAX_ITERATION_ALLOWED = 5
    pattern = r'Action:\s*(.*?)\n'

    for i in range(5):
        print(i)
        rsp = openai_obj.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        #pprint(rsp.choices[0].message.content)
        new_item = {"role":"assistant", "content":rsp.choices[0].message.content}
        messages.append(new_item)
        
        #pprint(messages)
        
        #arr_rsp = rsp.choices[0].message.content.split("\n")
        #re.search(r'word:\w\w\w', str)
        
        #print(re.search(pattern,rsp.choices[0].message.content).group())
        action_rsp = re.search(pattern,rsp.choices[0].message.content)
        #action_rsp = re.search(pattern,rsp.choices[0].message.content).group().replace("\n","").split(":")

        print(action_rsp)
        if action_rsp:
            action_rsp = action_rsp.group().replace("\n","").split(":")
            if action_rsp[1].strip() in known_actions:
            #action_rsp = action_rsp.replace("\n","").split(":")
            #pprint(action_rsp)
            #pprint(action_rsp[1].strip())
            #pprint(rsp.choices[0].message.content["Action"])
                observation = known_actions[action_rsp[1].strip()]()
                new_item = {"role":"assistant", "content":"Observation:"+observation}
                messages.append(new_item)
                #pprint(messages)
            else:
                raise Exception(f"Function {action_rsp[1].strip()} not available.")
        else:    
            print("agent finish with task")
            #return rsp.choices
            return rsp.choices[0].message.content
print(agent("Can you suggest some activities to do in my city this weekend?"))