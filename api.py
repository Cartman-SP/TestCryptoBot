import requests
from config import COINMARKET_API_KEY 


headers = {
    'X-CMC_PRO_API_KEY': COINMARKET_API_KEY
}


# Получение списка монет
def get_top_crypto():
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['data']
    else:
        print(f"Error: {response.status_code}, {response.text}")

# Получение id монеты по названию
def get_coin_id_by_name(name, coins):
    for coin in coins:
        if coin['name'] == name:
            return coin['id']
    return None

#def get_coin_value_by_id(id,coins):
#    for coin in coins:
#        if  coin['id']== id:
#            return coin['quote']['USD']['price']
#    return None


# Функция получения монеты по id 
def get_coin_by_id(coin_id):
    url = f'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?id={coin_id}'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()['data']
        if str(coin_id) in data:
            return data[str(coin_id)]
        else:
            print(f"Coin with id {coin_id} not found in response")
            return None
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None
