import json
import time
import win10toast_click as win10toast
from requests.exceptions import Timeout, TooManyRedirects
from requests import Session

def welcome_message():
    print("Welcome to Bitcoin price alerter!")
    
def request_alert_prices():
    alert_prices = []
    print("Please set your price objectives to configure alerts:\nExample: '52353,00'\nTo stop setting alerts write 'Done!'")
    price_objective = input("Enter a price objective: ")
    while(price_objective != "Done!"):
        if price_objective.isnumeric:
            price_objective = float(price_objective)
            if (price_objective>0 and price_objective<1000000):
                alert_prices.append(float(price_objective))
        else:
            print("The price you entered is invalid, it must be in the range of (0 - 1000000) and can only contain numbers, please retry:\n")
        price_objective = input("Enter a price objective: ")
    return alert_prices

def get_actual_price():
    url, parameters, headers = get_request_content()
    session = make_session(headers)
    data = make_request(session, url, parameters)
    return data["data"][0]["quote"]["USD"]["price"]

def get_objectives(actual_price, alert_prices):
    objectives = dict()
    for i in range(len(alert_prices)):
        if alert_prices[i] > actual_price:
            if i==0:
                print("WARNING: There is no stop loss set. No price objectives are lower than the actual price: "+str(actual_price)+".")
                objectives["actual_upper_objective"] = alert_prices[i]
            else:
                objectives["actual_lower_objective"] = alert_prices[i-1]
                objectives["actual_upper_objective"] = alert_prices[i]
            break
    return objectives
    
def start_watching_price(objectives, alert_prices, actual_price):
    print("Actual price: "+str(actual_price)+"\nUpper objective: "+str(objectives["actual_upper_objective"])+".\nLower objective: "+str(objectives["actual_lower_objective"])+".")
    check_objectives(objectives, alert_prices, actual_price)
    time.sleep(10)
    actual_price = get_actual_price()
    start_watching_price(objectives, alert_prices, actual_price)

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

def check_objectives(objectives, alert_prices, actual_price):
    if actual_price <= objectives["actual_lower_objective"]:
        print("ALERT! Bitcoin price is: "+str(actual_price)+" and has hit the lower objective of "+str(objectives["actual_lower_objective"])+".")
        get_objectives(objectives)
    elif actual_price >= objectives["actual_upper_objective"]:
        print("ALERT! Bitcoin price is: "+str(actual_price)+" and has hit the higher objective of "+str(objectives["actual_upper_objective"])+".")
        get_objectives(objectives)

def __main__():
    welcome_message()
    alert_prices = request_alert_prices()
    actual_price = get_actual_price()
    objectives = get_objectives(actual_price, alert_prices)
    toaster = get_toaster()
    start_watching_price(objectives, alert_prices, actual_price)

if __name__=="__main__":
    __main__()