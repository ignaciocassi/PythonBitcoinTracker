import time
import json
from time import gmtime, strftime
import win10toast_click as win10toast
from os import system
from art import text2art
from requests.exceptions import Timeout, TooManyRedirects
from requests import Session

class ObjectiveOutOfRangeException(Exception):
    pass

class ObjectiveNotNumericException(Exception):
    pass

class InvalidChoiceException(Exception):
    pass

class InvalidStopLossException(Exception):
    pass

class StopLossOutOfRangeException(Exception):
    pass

def welcome_message():
    banner = text2art("test","random")
    print(text2art('Bitcoin Tracker', font="small"))
    print("₿ This script allows you to get notified when Bitcoin price hits your price objectives.")
    
def set_stop_loss(actual_price):
    while True:
        try:
            formatted_price = "{:.2f}".format(actual_price)
            print("\n₿ Bitcoin actual price: U$D "+formatted_price)
            choice = input("₿ First things first ¿Do you want to set a stop loss alert? Y/N: ")
            if choice == "Y":
                stop_loss = input ("\nX Enter your desired stop loss alert: U$D ")
                if stop_loss.isnumeric():
                    stop_loss = float(stop_loss)
                    if stop_loss > 0 and stop_loss < actual_price:
                        return stop_loss
                    else:
                        raise StopLossOutOfRangeException
                else:
                    raise InvalidStopLossException
            elif choice == "N":
                return 0
            else:
                raise InvalidChoiceException
            break
        except InvalidStopLossException:
            system("cls")
            welcome_message()
            print("\nX Your stop loss must only contain numbers, please retry: ")
        except InvalidChoiceException:
            system("cls")
            welcome_message()
            print("\nX Command not recognized, you must enter Y or N. ")
        except StopLossOutOfRangeException:
            system("cls")
            welcome_message()
            formatted_price = "{:.2f}".format(actual_price)
            print("\nX The stop loss you entered is invalid. It must be lower than Bitcoin's actual price of U$D "+formatted_price+" Please retry: ")    

def get_alert_prices():
    system("cls")
    welcome_message()
    formatted_price = "{:.2f}".format(get_actual_price())
    print("\n₿ Bitcoin actual price: U$D "+formatted_price)
    print("\n₿ Now set your price objectives: \n₿ To start type 'GO!'")
    alert_prices = []
    while True:
        try:
            price_objective = input("-> USD ")
            while price_objective != "GO!":
                if price_objective.isnumeric():
                    price_objective = float(price_objective)
                    if price_objective > 0 and price_objective < 1000000:
                        alert_prices.append(float(price_objective))
                    else:
                        raise ObjectiveOutOfRangeException
                else:
                    raise ObjectiveNotNumericException
                price_objective = input("-> USD ")
            return alert_prices
        except ObjectiveOutOfRangeException:
            system("cls")
            welcome_message()
            print("\nX Your price objectives can only contain numbers, please retry: ")
        except ObjectiveNotNumericException:
            system("cls")
            welcome_message()
            print("\nX Your price objectives can only contain numbers, please retry: ")    
    
def get_actual_price():
    url, parameters, headers = get_request_content()
    session = make_session(headers)
    data = make_request(session, url, parameters)
    return data["data"][0]["quote"]["USD"]["price"]

def get_objectives(actual_price, alert_prices):
    alert_prices.sort()
    objectives = {"actual_upper_objective" : 0.0, "actual_lower_objective" : 0.0}
    i = 0
    while i < len(alert_prices)-1:
        if alert_prices[i] > actual_price:
            break
        i=i+1
    if i == 0:
        if alert_prices[i] > actual_price:
            objectives["actual_upper_objective"] = alert_prices[i]
        else:
            objectives["actual_lower_objective"] = alert_prices[i]
    elif i == len(alert_prices):
        objectives["actual_lower_objective"] = alert_prices[i-1]
    else:
        objectives["actual_lower_objective"] = alert_prices[i-1]
        objectives["actual_upper_objective"] = alert_prices[i]
    return objectives

def start_watching_price(objectives, stop_loss, alert_prices, actual_price, toaster):
    system("cls")
    welcome_message()
    formatted_price = "{:.2f}".format(actual_price)
    formatted_lower_objective = "{:.2f}".format(objectives["actual_lower_objective"])
    formatted_upper_objective = "{:.2f}".format(objectives["actual_upper_objective"])
    if objectives["actual_upper_objective"] != 0.0:
        print("\n˄ Actual upper objective: U$D "+formatted_upper_objective)
    print("₿ Bitcoin actual price:   U$D "+formatted_price)
    if objectives["actual_lower_objective"] != 0.0:
        print("˅ Actual lower objective: U$D "+formatted_lower_objective)
    check_objectives(objectives, stop_loss, alert_prices, actual_price, toaster)
    time.sleep(120)
    actual_price = get_actual_price()
    start_watching_price(objectives, stop_loss, alert_prices, actual_price, toaster)

def get_request_content():
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    parameters = {'start':'1',
                    'limit':'1',
                    'convert':'USD'}
    headers = {'Accepts': 'application/json',
               'X-CMC_PRO_API_KEY': 'a7d138ac-a1c6-4ed5-8daf-3c685c8d3cb2',}
    return url,parameters,headers

def make_session(headers):
    session = Session()
    session.headers.update(headers)
    return session

def make_request(session, url, parameters):
    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        return data
    except (ConnectionError, Timeout, TooManyRedirects) as exception_info:
        print(exception_info)
        
def get_toaster():
    return win10toast.ToastNotifier()

def print_json_formatted(data):
    print(json.dumps(data, indent=4, sort_keys=True))

def check_objectives(objectives, stop_loss, alert_prices, actual_price, toaster):
    print("\n⧖ Last checked at: "+strftime("%Y-%m-%d %H:%M:%S", gmtime()))
    formatted_stop_loss = "{:.2f}".format(stop_loss)
    formatted_actual_upper_objective = "{:.2f}".format(objectives["actual_upper_objective"])
    formatted_actual_lower_objective = "{:.2f}".format(objectives["actual_lower_objective"])
    if actual_price <= stop_loss:
        toaster.show_toast("Stop loss!","Bitcoin price has hit your stop loss ("+formatted_stop_loss+").")
    elif objectives["actual_lower_objective"] != 0.0 and actual_price <= objectives["actual_lower_objective"]:
        toaster.show_toast("Bitcoin has hit your lower objective of "+formatted_actual_lower_objective+"!")
    elif objectives["actual_upper_objective"] != 0.0 and actual_price >= objectives["actual_upper_objective"]:
        toaster.show_toast("Bitcoin has hit your upper objective of "+formatted_actual_upper_objective+"!")
    objectives = get_objectives(actual_price, alert_prices)

def __main__():
    welcome_message()
    actual_price = get_actual_price()
    stop_loss = set_stop_loss(actual_price)
    alert_prices = get_alert_prices()
    objectives = get_objectives(actual_price, alert_prices)
    toaster = get_toaster()
    toaster.show_toast("You're done!","I will notify you if Bitcoin price hits your objectives.")
    start_watching_price(objectives, stop_loss, alert_prices, actual_price, toaster)

if __name__=="__main__":
    __main__()