import ast
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


def get_weather(location):
    return json.dumps({
        "city": location,
        "temperature": 78,
        "unit":"F",
        "forecast": "Sunny"
    })


known_actions = {
    "getCurrentWeather": get_weather,
    "getLocation": get_current_location
}

systemPrompt = """"You are a helpful AI agent. Give highly specific answers based on the information you're provided. Prefer to gather information with the tools provided to you rather than giving basic, generic answers."""

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

        rsp = openai_obj.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            tools= [
                    {
                        "type": "function",
                        "function": {
                            "name": "getCurrentWeather",
                            "description": "Get the current weather",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "location":{
                                        "type": "string",
                                        "description": "the city"
                                    }
                                }
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "getLocation",
                            "description": "Get the user's current location",
                            "parameters": {
                                "type": "object",
                                "properties": {}
                            }
                        }
                    },
                ]
        
        )
        
        if rsp.choices[0].finish_reason == "stop":
            print("Here the answer for our question")
            return rsp.choices[0].message.content
        elif rsp.choices[0].finish_reason == "tool_calls":
            
            messages.append(rsp.choices[0].message)
            for i in rsp.choices[0].message.tool_calls:
               
                args = ast.literal_eval(i.function.arguments)

                observation = None
                if len(args) > 0:
                    observation = known_actions[i.function.name.strip()](i.function.arguments)
                else:
                    observation = known_actions[i.function.name.strip()]()
                    
                new_item = {
                    "tool_call_id":i.id,
                    "role":"tool", 
                    "content":observation}
                
                messages.append(new_item)
       
        
print(agent("Discover my location and give me a list of outdoors activites I can do this weekend!"))
"""
[Choice(finish_reason='tool_calls', index=0, logprobs=None, message=ChatCompletionMessage(content=None, refusal=None, role='assistant', audio=None, function_call=None, tool_calls=[ChatCompletionMessageToolCall(id='call_rlc5JvFxfOryoXzZcybttt1i', function=Function(arguments='{}', name='getLocation'), type='function')]))]
"""