import win10toast_click as win10toast
import time
import json
from requests.exceptions import Timeout, TooManyRedirects
from time import gmtime, strftime
from requests import Session
from art import text2art
from os import system


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
    """
    Shows a welcome message to the user.
    """
    print(text2art('Bitcoin Tracker', font="small"))
    print("₿ This script allows you to get notified when Bitcoin price hits your price objectives.")


def set_stop_loss(actual_price):
    """
    Optional, allows the user to set a stop loss price that is under Bitcoins actual price.
    :param actual_price: Bitcoin's actual price. It is needed to ensure that the stop loss is under it.
    :return: The stop loss defined by the user, or 0 if user decides not to set it.
    """
    while True:
        try:
            formatted_price = "{:.2f}".format(actual_price)
            print("\n₿ Bitcoin actual price: U$D " + formatted_price)
            choice = input("₿ First things first ¿Do you want to set a stop loss alert? Y/N: ")
            if choice == "Y":
                stop_loss = input("\nX Enter your desired stop loss alert: U$D ")
                if stop_loss.isnumeric():
                    stop_loss = float(stop_loss)
                    if 0 < stop_loss < actual_price:
                        return stop_loss
                    else:
                        raise StopLossOutOfRangeException
                else:
                    raise InvalidStopLossException
            elif choice == "N":
                return 0
            else:
                raise InvalidChoiceException
        except InvalidStopLossException:
            system("cls")
            welcome_message()
            print("\nX Your stop loss must only contain numbers, please retry: ")
        except InvalidChoiceException:
            system("cls")
            welcome_message()
            print("\nX Command not recognized, you must enter Y or N, please retry: ")
        except StopLossOutOfRangeException:
            system("cls")
            welcome_message()
            formatted_price = "{:.2f}".format(actual_price)
            print(
                "\nX Your stop loss should be under Bitcoin's price U$D " + formatted_price + ". Please retry: ")


def get_alert_prices():
    """
    Allows the user to set one or more price objectives.
    :return: The ordered list of price objectives.
    """
    system("cls")
    welcome_message()
    formatted_price = "{:.2f}".format(get_actual_price())
    print("\n₿ Bitcoin actual price: U$D " + formatted_price)
    print("\n₿ Now set your price objectives: \n₿ To start type 'GO!'")
    alert_prices = []
    while True:
        try:
            price_objective = input("-> USD ")
            while price_objective != "GO!":
                if price_objective.isnumeric():
                    price_objective = float(price_objective)
                    if 0 < price_objective < 1000000:
                        alert_prices.append(float(price_objective))
                    else:
                        raise ObjectiveOutOfRangeException
                else:
                    raise ObjectiveNotNumericException
                price_objective = input("-> USD ")
            alert_prices.sort()
            return alert_prices
        except ObjectiveOutOfRangeException:
            system("cls")
            welcome_message()
            print("\nX Your price objectives can only contain numbers, please retry: ")
        except ObjectiveNotNumericException:
            system("cls")
            welcome_message()
            print("\nX Your price objectives can only contain numbers, please retry: ")


def get_request_content():
    """
    Sets the API endpoint URL, parameters and headers of the request that will be done to CoinMarketCap API
    :return: Request URL, parameters and headers
    """
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    parameters = {'start': '1',
                  'limit': '1',
                  'convert': 'USD'}
    headers = {'Accepts': 'application/json',
               'X-CMC_PRO_API_KEY': 'a7d138ac-a1c6-4ed5-8daf-3c685c8d3cb2', }
    return url, parameters, headers


def make_session(headers):
    """
    Creates the session needed to make the HTTP request to the API.
    :param headers: The headers included in the request.
    :return: The new session.
    """
    session = Session()
    session.headers.update(headers)
    return session


def make_request(session, url, parameters):
    """
    Makes an HTTP (get) request to CoinMarketCap API, parses the response to JSON.
    :param session: The session used to make the HTTP request to the API.
    :param url: The HTTP request URL.
    :param parameters: The HTTP request parameters.
    :return: JSON response from the API.
    """
    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        return data
    except (ConnectionError, Timeout, TooManyRedirects) as exception_info:
        print(exception_info)


def get_actual_price():
    """
    Using the obtained information from the API in JSON format, gets the actual Bitcoin to U$D pair actual price.
    :return: Bitcoin to U$D pair actual price.
    """
    url, parameters, headers = get_request_content()
    session = make_session(headers)
    data = make_request(session, url, parameters)
    return data["data"][0]["quote"]["USD"]["price"]


def get_objectives(actual_price, alert_prices):
    """
    Using the ordered list of price objectives, gets the actual upper objective and the actual lower objective.
    :param actual_price: Bitcoins actual price.
    :param alert_prices: List of price objectives.
    :return: Dict: Objectives with the actual upper and lower prices in key-value pairs.
    """
    objectives = {"actual_upper_objective": 0.0, "actual_lower_objective": 0.0}
    i = 0
    while i < len(alert_prices) - 1:
        if alert_prices[i] > actual_price:
            break
        i = i + 1
    if i == 0:
        if alert_prices[i] > actual_price:
            objectives["actual_upper_objective"] = alert_prices[i]
        else:
            objectives["actual_lower_objective"] = alert_prices[i]
    elif i == len(alert_prices):
        objectives["actual_lower_objective"] = alert_prices[i - 1]
    else:
        objectives["actual_lower_objective"] = alert_prices[i - 1]
        objectives["actual_upper_objective"] = alert_prices[i]
    return objectives


def start_watching_price(objectives, stop_loss, alert_prices, actual_price, toaster):
    """
    Obtains Bitcoin's actual price every 120 seconds and checks if it has hit the upper or lower objectives.
    If the price has hit an objective, sends a notification to the user.
    :param objectives: Dict: Objectives with the actual upper and lower prices in key-value pairs.
    :param stop_loss: The actual stop loss set by the user.
    :param alert_prices: The price objectives set by the user.
    :param actual_price: Bitcoin's actual price
    :param toaster: win10toast-click object used to send notifications to the user.
    """
    system("cls")
    welcome_message()
    formatted_price = "{:.2f}".format(actual_price)
    formatted_lower_objective = "{:.2f}".format(objectives["actual_lower_objective"])
    formatted_upper_objective = "{:.2f}".format(objectives["actual_upper_objective"])
    if objectives["actual_upper_objective"] != 0.0:
        print("\n˄ Actual upper objective: U$D " + formatted_upper_objective)
    print("₿ Bitcoin actual price:   U$D " + formatted_price)
    if objectives["actual_lower_objective"] != 0.0:
        print("˅ Actual lower objective: U$D " + formatted_lower_objective)
    check_objectives(objectives, stop_loss, alert_prices, actual_price, toaster)
    time.sleep(120)
    actual_price = get_actual_price()
    start_watching_price(objectives, stop_loss, alert_prices, actual_price, toaster)


def get_toaster():
    """Creates an instance of win10toast and returns it."""
    return win10toast.ToastNotifier()


def check_objectives(objectives, stop_loss, alert_prices, actual_price, toaster):
    """
    Compares Bitcoin's actual price to the actual upper and lower objectives.
    :param objectives: Dict: Objectives with the actual upper and lower prices in key-value pairs.
    :param stop_loss: The actual stop loss set by the user.
    :param alert_prices: The price objectives set by the user.
    :param actual_price: Bitcoin's actual price
    :param toaster: win10toast-click object used to send notifications to the user.
    """
    print("\n⧖ Last checked at: " + strftime("%Y-%m-%d %H:%M:%S", gmtime()))
    formatted_stop_loss = "{:.2f}".format(stop_loss)
    formatted_actual_upper_objective = "{:.2f}".format(objectives["actual_upper_objective"])
    formatted_actual_lower_objective = "{:.2f}".format(objectives["actual_lower_objective"])
    if actual_price <= stop_loss:
        toaster.show_toast("Stop loss!", "Bitcoin price has hit your stop loss (" + formatted_stop_loss + ").")
    elif objectives["actual_lower_objective"] != 0.0 and actual_price <= objectives["actual_lower_objective"]:
        toaster.show_toast("Bitcoin has hit your lower objective of " + formatted_actual_lower_objective + "!")
    elif objectives["actual_upper_objective"] != 0.0 and actual_price >= objectives["actual_upper_objective"]:
        toaster.show_toast("Bitcoin has hit your upper objective of " + formatted_actual_upper_objective + "!")
    objectives = get_objectives(actual_price, alert_prices)


def __main__():
    welcome_message()
    actual_price = get_actual_price()
    stop_loss = set_stop_loss(actual_price)
    alert_prices = get_alert_prices()
    objectives = get_objectives(actual_price, alert_prices)
    toaster = get_toaster()
    toaster.show_toast("You're done!", "I will notify you if Bitcoin price hits your objectives.")
    start_watching_price(objectives, stop_loss, alert_prices, actual_price, toaster)


if __name__ == "__main__":
    __main__()
