from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet, ConversationPaused, UserUtteranceReverted
import sqlite3
import re

class ValidateResetPasswordForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_reset_password_form"

    def validate_account(self, slot_value: Any, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict) -> Dict[Text, Any]:
        
        account_exist = False
        account = int(slot_value)
        conn = sqlite3.connect('data/account.db')
        cursor = conn.cursor()
        cursor.execute("SELECT account FROM Account_INFO")
        results = cursor.fetchall()
        for result in results:
            for value in result:               
                if account == value:
                    account_exist = True                
        if account_exist:
            dispatcher.utter_message("Your account has been found.")
        else:
            dispatcher.utter_message("Sorry, your account has not been found.")
            return {"account": None}
       
    def validate_security_number(self, slot_value: Any, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict) -> Dict[Text, Any]:
        account = int(tracker.get_slot('account'))
        security_number = int(slot_value)
        number_correct = False
        conn = sqlite3.connect('data/account.db')
        cursor = conn.cursor()
        cursor.execute("SELECT Security_number FROM Account_INFO WHERE Account = ?", (account,))
        result = cursor.fetchone()
        if result and result[0] == security_number:
            number_correct = True
        if number_correct:                
            dispatcher.utter_message("Your security number is correct.")
        else:
            dispatcher.utter_message("Sorry, your security number is wrong.")
            return {"security_number": None}

class QueryCompanyDetails(Action):

    def name(self) -> Text:
        return "query_company_details"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
     
        conn = DbQueryingMethods.create_connection(db_file="data/account.db")

        get_query_results = DbQueryingMethods.select_by_slot(conn=conn,slot_value=tracker.get_slot('company_type'))
        
        dispatcher.utter_message(text=str(get_query_results))
 

class DbQueryingMethods:
    def create_connection(db_file):
        """ 
        create a database connection to the SQLite database
        specified by the db_file
        :param db_file: database file
        :return: Connection object or None
        """
        conn = None
        try:
            conn = sqlite3.connect(db_file)
        except sqlite3.Error as e:
            print(e)

        return conn

    def select_by_slot(conn, slot_value):
        """
        Query all rows in the Orders table
        :param conn: the Connection object
        :return:
        """
        cur = conn.cursor()
        slot_value = slot_value.replace('"', '')
        cur.execute(f'''SELECT Info from Company_INFO
                    WHERE Type="{slot_value}"''')

        # return an array
        Info = cur.fetchall()
        return Info

class ActionDefaultAskAffirmation(Action):
    def name(self) -> Text:
        return "action_default_ask_affirmation"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict[Text, Any]
    ):
        # top three intents selected
        predicted_intents = tracker.latest_message["intent_ranking"][1:4]
        
        # Convert technical intent names to natural everyday langauge
        intent_mappings = { "affirm" : "yes",
                            "bot_challenge" : "are you a bot",
                            "deny": "no",
                            "forget_password":"lose password",
                            "goodbye":"bye",
                            "greet":"hello",
                            "provide_account": "give account",
                            "provide_company_type":"give company type",
                            "provide_feedback":"give feedback",
                            "provide_new_password":"give new password",
                            "provide_security_number":"give security number",
                            "query_company_information": "company information",
                            "query_login_or_registration_question":" log in or register",
                            "switch_human_service":"talk to human",
                           }
        
        # show the top three intents as buttons for user's convenience
        
        buttons = [
            {
                "title": intent_mappings[intent['name']],
                "payload": "/{}".format(intent['name'])
            }
            for intent in predicted_intents
        ]
        
        # buttons = [{"title": intent_mappings[intent['name']],"payload": "/{}".format(intent['name'])}
        
        # add one more button "None of these", if the user does not agree with any of the above options
        buttons.append({
            "title": "None of these",
            "payload": "/out_of_scope"
        })
        
        #Chatbot asks the user to confirm by selecting one of the optinos
        message = "Sorry, I am not sure I understood you correctly. Please confirm:"
        
        dispatcher.utter_message(text=message, buttons=buttons)
        return []

class ActionDefaultFallback(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        message = "This is out of my scope, I will transfer you to our customer service..."
        dispatcher.utter_message(text=message)
        return [ConversationPaused(), UserUtteranceReverted()]
        # dispatcher.utter_message(template="my_custom_fallback_template")
        # return [UserUtteranceReverted()]



class CustomGreet(Action):

    def name(self) -> Text:
        return "Greet_by_name"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        name = tracker.get_slot('name')
        if name != None:
            name = name.replace('"', '')
            dispatcher.utter_message(template="utter_greet_by_name", name=name)
        else:
            dispatcher.utter_message(template="utter_greet")
           
class CustomBye(Action):

    def name(self) -> Text:
        return "Bye_by_name"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        name = tracker.get_slot('name')
        if name != None:
            name = name.replace('"', '')
            dispatcher.utter_message(template="utter_goodbye_by_name", name=name)
        else:
            dispatcher.utter_message(template="utter_goodbye")
        
class ChangePassword(Action):

    def name(self) -> Text:
        return "Change_password"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        new_password = tracker.get_slot('password')
        if new_password == None:
            new_password ="000000"
        account = tracker.get_slot('account')
        new_password = new_password.replace('"', '')
        account = account.replace('"', '')[1:]
        pattern = r'^[A-Za-z]{2}\d{6}$'
        if re.match(pattern, new_password):
           con = sqlite3.connect('data/account.db')
           cursor = con.cursor()
           dispatcher.utter_message(f"Your account is {account}, Your password has been changed to {new_password}.")
           cursor.execute("UPDATE Account_INFO SET Password = ? WHERE Account = ?", (new_password, account))
           con.commit()
           return [SlotSet("password", None), SlotSet("account", None), SlotSet("security_number", None)]
        else:
            dispatcher.utter_message(template="utter_password_error")
            return [SlotSet("password", None)]
        