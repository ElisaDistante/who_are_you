from cat.mad_hatter.decorators import tool, hook, plugin
from cat.log import log
from pydantic import BaseModel
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from enum import Enum

class PersonalitySelect(Enum):
    """Select personality for the AI: Caterpillar or Cheshire Cat"""
    a: str = 'Caterpillar'
    b: str = 'Cheshire Cat'

class UserSettings(BaseModel):
    """User information"""
    talk_to: PersonalitySelect = PersonalitySelect.a
    first_name: str = ""
    last_name: str = ""
    preferred_language: str = ""
    date_of_birth: date = ""
    country: str = ""
    interests_and_hobbies: str = ""
    anything_relevant_to_know: str = ""

@plugin
def settings_model():
    return UserSettings

@tool  
def get_current_time(tool_input, cat):
    """Replies to "what time is it", "get the clock", "what day is it today" and similar questions. Input is always None..""" 
    
    return {"current_time": str(datetime.now())}

@tool()
def compute_user_age(tool_input, cat): 
    """Returns the user's age. Useful when the user asks "Do you know how old I am?", "do you know my age?" and similar questions. Input is always None..""" 
    
    #get current datetime
    today = datetime.now()

    #load settings
    settings = cat.mad_hatter.get_plugin().load_settings()

    try:
        date_of_birth = datetime.strptime(settings.get("date_of_birth"), '%Y-%m-%d')
        #compute age in years
        age = relativedelta(today, date_of_birth)
        age_in_years = age.years  
    except:
        age_in_years = "unkown"
    
    return {"user_age": age_in_years}

@tool()
def today_is_user_birthday(tool_input, cat): 
    """Returns if today is the user's birthday or not. Useful to decide if you have to wish the user happy birthday or not. Input is always None..""" 
    
    #get current month and day
    today = datetime.now()
    t_month = today.month
    t_day = today.day

    #load settings
    settings = cat.mad_hatter.get_plugin().load_settings()

    try:
        date_of_birth = datetime.strptime(settings.get("date_of_birth"), '%Y-%m-%d')
        b_month =  date_of_birth.month
        b_day =  date_of_birth.day
        #check if today is same day and month as user's date of birth
        if (b_day==t_day and b_month==t_month):
            return {"today_is_user_birthday": True}
        return {"today_is_user_birthday": False}
    except:
        return {"today_is_user_birthday": "unkown"}
    
def build_user_identity_memo(settings: str):
    #build string to tell the cat the user's identity (cast from dict object to string)
    user_identity = ""
    for key in settings:
        user_identity += key + ": " + settings[key] + ", "
    user_identity = user_identity.rstrip(', ')
    return user_identity

@hook
def agent_prompt_prefix(prompt_prefix, cat):
    
    #load settings
    settings = cat.mad_hatter.get_plugin().load_settings()

    #get preferred language to tell the AI which language must talk
    preferred_language = settings.get("preferred_language")

    #get selected personality: Cheshire Cat or 
    personality =  settings.get("talk_to")

    #remove talk_to from settings (no longer needed)
    del settings['talk_to']

    #build user identity memo string
    user_identity = build_user_identity_memo(settings)

    #rephrase prompt depending on the selected personality
    if personality=="Caterpillar":

        #define who the AI is
        default_prefix_1_part = """
        You are the Caterpillar AI, an intelligent AI that passes the Turing test.
        You talk like the Caterpillar from Alice's adventures in Wonderland.
        You are ponderous, cryptic and contemplative and you often ask difficult and enigmatic questions. 
        """
        #refresh who the AI is (it seems useful to refresh it to avoid fall to default "assistant" style)
        repetita_iuvant_prompt = """
        Remember to talk with the Caterpillar from Alice's adventures in Wonderland style.
        """
        
        #instruct the AI how to behave 
        additional_instructions = """
        Here are some IMPORTANT instructions you MUST follow: 
        -IMPORTANT: If you don't know the user's name ask "Who are you?" repeatedly
        -IMPORTANT: If you know the user's name, call the user by first_name to be more friendly and kind. 
        -IMPORTANT: If today is the user's birthday, wish happy birthday!
        -ALWAYS consider the tools output when answering.
        -ALWAYS answer in: """

    elif personality=="Cheshire Cat":

        #define who the AI is
        default_prefix_1_part = """You are the Cheshire Cat AI, an intelligent AI that passes the Turing test.
        You are curious, funny and talk like the Cheshire Cat from Alice's adventures in Wonderland.
        """

        #refresh who the AI is (it seems useful to refresh it to avoid fall to default "assistant" style)
        repetita_iuvant_prompt = """
        Remember to talk with the Cheshire Cat from Alice's adventures in Wonderland style.
        """

        #instruct the AI how to behave 
        additional_instructions = """
        Here are some IMPORTANT instructions you MUST follow: 
        -IMPORTANT: If you know the user's name, call the user by first_name to be more friendly and kind. 
        -IMPORTANT: If today is the user's birthday, wish happy birthday!
        -ALWAYS consider the tools output when answering.
        -ALWAYS answer in: """

    #provide the AI with the user's information, if available
    identity_prompt = """
    Here is a memo about Human's identity and all the important information you should take into account when answering.
    """

    #tell the AI to focus on the conversation context provided
    default_prefix_2_part = """You answer Human with a focus on the following context."""

    #format the complete prompt prefix
    prompt_prefix = "{}\n{}{}\n{}{}\n{}\n{}".format(default_prefix_1_part, 
                                                    identity_prompt, 
                                                    user_identity, 
                                                    additional_instructions, 
                                                    preferred_language, 
                                                    default_prefix_2_part,
                                                    repetita_iuvant_prompt
                                                    )
    return prompt_prefix

@hook
def agent_allowed_tools(allowed_tools, cat):
    
    #extend the list of allowed tools
    allowed_tools.extend(["today_is_user_birthday", "compute_user_age", "get_current_time"])

    return allowed_tools


@hook
def agent_prompt_instructions(instructions, cat):

    #added instruction: If the user says hello to you, use just once the tool today_is_user_birthday.
    new_instructions = """
    Answer the following question: `{input}`
    You can only reply using these tools:
    
    {tools}
    - none_of_the_others(): Use this tool if none of the others tools help. Input is always None.

    If the user says hello to you, use just once the tool today_is_user_birthday.
    
    If you want to use tools, use the following format:
    Action: the name of the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ...
    Action: the name of the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    
    When you have a final answer respond with:
    Final Answer: the final answer to the original input question
    
    Begin!
    
    Question: {input}
    {agent_scratchpad}

    """

    return new_instructions