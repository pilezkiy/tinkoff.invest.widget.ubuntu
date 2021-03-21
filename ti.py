import ti_config as cfg, requests, asyncio, time
from rich.console import Console
from operator import itemgetter
console = Console()

headers = {"Authorization": "Bearer " + cfg.tinkoffToken}

def get_currencies():
    return requests.get(cfg.tinkoffApiEndpoint + "/market/currencies", {}, headers=headers).json()

async def get_currencies__async():
    return get_currencies()

def get_orderbook(figi, depth):
    return requests.get(cfg.tinkoffApiEndpoint + "/market/orderbook", {"figi":figi, "depth": depth}, headers=headers).json()

async def get_orderbook__async(figi, depth):
    return get_orderbook(figi, depth)

def get_portfolio():
    return requests.get(cfg.tinkoffApiEndpoint + "/portfolio", {}, headers=headers).json()

async def get_portfolio__async():
    return get_portfolio()

def get_portfolio_currencies():
    return requests.get(cfg.tinkoffApiEndpoint + "/portfolio/currencies", {}, headers=headers).json()

async def get_portfolio_currencies__async():
    return get_portfolio_currencies()


def get_portfolio_calculated():
    portfolio = {"items":[],"USDRUB":0, "totalPortfolioSumRUB": 0, "totalPortfolioProfitRUB":0}
    
    ioloop = asyncio.new_event_loop()
    initTasks = []
    # get USD price in RUB
    task = ioloop.create_task(get_orderbook__async("BBG0013HGFT4",1))
    task.set_name("usdTask")
    initTasks.append(task)
    # get currencies list
    task = ioloop.create_task(get_currencies__async())
    task.set_name("currenciesTask")
    initTasks.append(task)
    # get portfolio list
    task = ioloop.create_task(get_portfolio__async())
    task.set_name("portfolioTask")
    initTasks.append(task)
    # get portfolio currencies list
    task = ioloop.create_task(get_portfolio_currencies__async())
    task.set_name("portfolioCurrenciesTask")
    initTasks.append(task)
    # request all
    ioloop.run_until_complete(asyncio.wait(initTasks))
    ioloop.close()

    tasksResults = {}
    for t in initTasks:
        tasksResults[t.get_name()] = t.result()


    if tasksResults["usdTask"] and "payload" in tasksResults["usdTask"]:
        portfolio["USDRUB"] = tasksResults["usdTask"]["payload"]["lastPrice"]

    currencies = {}

    if tasksResults["currenciesTask"] and "payload" in tasksResults["currenciesTask"]:
        for v in tasksResults["currenciesTask"]["payload"]["instruments"]:
            currency = v["ticker"][:3].upper();
            currencies[currency] = v
    

    if tasksResults["portfolioTask"] and "payload" in tasksResults["portfolioTask"]:
        for item in tasksResults["portfolioTask"]["payload"]["positions"]:
            if cfg.isFake :
                item["balance"] *= random.uniform(10,50)

            itemValue = {
                "ticker": item["ticker"],  
                "figi": item["figi"],  
                "balance": item["balance"],
                "name": item["name"],
                "price": item["averagePositionPrice"]["value"],
                "priceCurrency": item["averagePositionPrice"]["currency"],
                "totalPrice": item["balance"] * item["averagePositionPrice"]["value"] + item["expectedYield"]["value"],
                "profit": item["expectedYield"]["value"],
                "profitCurrency": item["expectedYield"]["currency"],
            }
            portfolio["items"].append(itemValue)
            

    ioloop = asyncio.new_event_loop()
    portfolioItemTasks = []
    
    for item in portfolio["items"]:
        if item["figi"]:
            task = ioloop.create_task(get_orderbook__async(item["figi"],0))
            task.set_name(item["figi"])
            portfolioItemTasks.append(task)
    ioloop.run_until_complete(asyncio.wait(portfolioItemTasks))
    ioloop.close()                        

    portfolioItemTasksResults = {}
    for t in portfolioItemTasks:
        portfolioItemTasksResults[t.get_name()] = t.result()

    for item in portfolio["items"]:
        if item["figi"] and item["figi"] in portfolioItemTasksResults and "payload" in portfolioItemTasksResults[item["figi"]]:
            priceItem = portfolioItemTasksResults[item["figi"]]["payload"]
            item["price"] = priceItem["lastPrice"]
            item["totalPrice"] = item["balance"] * item["price"]
        if item["ticker"] == 'USD000UTSTOM':
            item["ticker"] = 'USD'
            if portfolio["USDRUB"] <= 0:
                portfolio["USDRUB"] = item["price"]
    
    if tasksResults["portfolioCurrenciesTask"] and "payload" in tasksResults["portfolioCurrenciesTask"]:
        for v in tasksResults["portfolioCurrenciesTask"]["payload"]["currencies"]:
            if v["currency"] == 'USD' or v["balance"] <= 0:
                continue
            itemValue = {
                "ticker": v["currency"],
                "balance": v["balance"],
                "name": v["currency"],
                "price": 1,
                "priceCurrency": v["currency"],
                "totalPrice": v["balance"],
                "profit": 0,
                "profitCurrency": v["currency"],
            }

            portfolio["items"].append(itemValue)
    
    for item in portfolio["items"]:
        sum = item["totalPrice"]
        if item["priceCurrency"] == 'USD':
            sum = sum * portfolio["USDRUB"]
        portfolio["totalPortfolioSumRUB"] += sum
        item["totalPriceRUB"] = sum

        profit = item["profit"]
        if item["profitCurrency"] == 'USD':
            profit = profit * portfolio["USDRUB"]
        portfolio["totalPortfolioProfitRUB"] += profit
        
    for item in portfolio["items"]:
        item["percent"] = 0
        if item["totalPriceRUB"] > 0 and portfolio["totalPortfolioSumRUB"] > 0:
            item["percent"] = (item["totalPriceRUB"]/portfolio["totalPortfolioSumRUB"]) * 100

    portfolio["items"].sort(key = itemgetter('totalPriceRUB'), reverse = True)
    
    return portfolio
