from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import re
import time
from binance.client import Client
import datetime
import pandas as pd
from pathlib import Path
import logging
from websocket_server import WebsocketServer
import gc
import math, json
from urllib.request import urlretrieve
import os

host = '192.168.50.252'
port = 13280

chartsTimeframe = 5 #mins
chartRecordsHourly = (60/chartsTimeframe)
chartRecordsDaily = (60/chartsTimeframe)*24
chartRecordsWeekly = chartRecordsDaily*7
weeklyChart = "1 H/168";

defaultDecimals = 2
startedAt = datetime.datetime.now()

initDone = False;

binanceTime = -3
binanceClient = Client("zdoSQtX7nWhlJe2122TaGbKteqq6pBwCKJ095iYOvLUmGvogyDuG2sRQSfzOFTrs", "k8DJA9vAjJHnZlywfq81BR4cp2ufUWi9dYxcQvGAzCiH3LwU8scDn6MD9fpzlO6l")
binanceHas = ["ENA","MANA","BAT","GNO","SHIB","SAND","DAI","TUSD","MATIC","USDT","SUI",'APT',"CYBER","NEAR","OP","ARB","ETH","ID","BNB","AVAX","WOO","FTM","GLMR","STG","USDC","MATIC","DOT","MANTA","STRK","PYTH","JUP","SEI","TIA","ALGO","FIL", "SOL", "ATOM","ICP","LINK"]

tokensInUse = []





retryIncrement = 2 #seconds
maxRetries = 5


portfoliosGlobal = []
walletsGlobal = []
tokensGlobal = []
networksGlobal = []


def getAvailableShadersList():
    subfolders= [f.path for f in os.scandir("../DegenerateFolio React/React/src/shaders") if f.is_dir()]
    result = "["
    for subfolder in subfolders:
        result+='"'
        result+=(subfolder.split("/")[-1])
        result+='"'
        if subfolder != subfolders[-1]:
            result+=","
    result+="]"
    print(result)
    return result

getAvailableShadersList()
        
def new_client(client, server):
    
	server.send_message_to_all('shaders/'+getAvailableShadersList())


def new_message(client,server,message):
    params = message.split('/')
    type = params[0]
    print("type:",type)
    if type == 'chart':
        token = params[1]
        since = params[2]
        timeframe = params[3]
        limit = params[4]
        response = getApiResponseChart(token,since,timeframe,limit)
        server.send_message(client,('chart7D/' if since=='0' and timeframe == '1 H' and limit == '168' else 'chart/')+token+'/'+response)
    elif type == 'getAllBalances':
        #portfolioName = params[1]
        server.send_message(client,'balances/'+allBalancesToJson(getPortfolio("Testfolio")))
    elif type =='updateAllBalances':
        server.send_message_to_all('updateAllBalances/'+allBalancesToJson(getPortfolio("Testfolio")))
    elif type == 'update':
        token = params[1]
        update = params[2]
        server.send_message_to_all('update/'+token+'/'+update)
    print(message)
    
def startWsServer():
    server = WebsocketServer(host, port, loglevel=logging.INFO)
    server.set_fn_new_client(new_client)
    server.set_fn_message_received(new_message)
    server.run_forever(True)
    return server

driver = webdriver.Firefox()
driver2 = webdriver.Chrome()

print("Started at:",datetime.datetime.now())



def allBalancesToJson(portfolio):
    jsonResponse = '['
    tokens = portfolio.getHoldings()
    for token in tokens:
        jsonResponse += '{'
        jsonResponse += '"ticker":'
        jsonResponse += '"'+token.name+'",'
        jsonResponse += '"amount":'
        jsonResponse += str(token.amount)+','
        jsonResponse += '"price":'
        jsonResponse += str(getTokenPrice(token.name)) if getToken(token.name) is not None else 'null'
        jsonResponse += ','
        jsonResponse += '"fullname":'
        jsonResponse += '"'+str(getToken(token.name).fullname)+'"' if getToken(token.name) is not None else 'null'
        jsonResponse += ','
        jsonResponse += '"decimals":'
        jsonResponse += str(getToken(token.name).decimals)  if getToken(token.name) else str(defaultDecimals)
        jsonResponse += ','
        jsonResponse += '"h1Change":'
        jsonResponse += str(getToken(token.name).h1Change) if getToken(token.name) else "0"
        jsonResponse += ','
        jsonResponse += '"h24Change":'
        jsonResponse += str(getToken(token.name).h24Change) if getToken(token.name) else "0"
        jsonResponse += ','
        jsonResponse += '"d7Change":'
        jsonResponse += str(getToken(token.name).d7Change) if getToken(token.name) else "0"
        jsonResponse += '}'
        jsonResponse += ','
    jsonResponse = jsonResponse[:-1]
    jsonResponse += ']'
    #print(jsonResponse)
    return jsonResponse

class Wallet:
    def __init__(self,address,network):
        self.address = address
        self.network = network
        self.tokens = []
        self.lastUpdate = -1 #cycle
        
    def updateToken(self,token):
        
        if not token.name in tokensInUse:
            tokensInUse.append(token.name)
            
        if token.price != 0:
            getToken(token.name).price = token.price
        findToken = getToken(token.name,self.tokens)
        if findToken:
            findToken.free = token.free
            findToken.staked = token.staked
            findToken.locked = token.locked
            findToken.lended = token.lended
        else:
            self.addToken(token)
    
    def addToken(self,token):
        self.tokens.append(token)
        
    def printMe(self):
        print("-------")
        print("Holdings of address:",self.address)
        print("In :",self.network,"network")
        for token in self.tokens:
            amount = float(token.free)+float(token.locked)+float(token.lended)+float(token.staked)
            print(token.name," price:",getTokenPrice(token.name)," amount:",amount,"value:",amount*getTokenPrice(token.name))
        print("------")
            

class Portfolio:
    def __init__(self,name,description):
        self.name = name
        self.description = description
        self.wallets = []
        self.unparsableTokens = []
        self.staked = []
        self.locked = []
        self.lended = []
        
        
    def getHoldings(self):
        temp = []
        for wallet in self.wallets:
            for token in wallet.tokens:
                tempToken = getToken(token.name,temp)
                if tempToken is None:
                    tempToken = Token(name=token.name,staked=token.staked,locked=token.locked,lended=token.lended)
                    temp.append(tempToken)
                
                tempToken.amount+=float(token.free)+float(token.staked)+float(token.locked)+float(token.lended)
                
        for token in self.unparsableTokens:
            tempToken = getToken(token.name,temp)
            if tempToken is None:
                tempToken = Token(name=token.name,staked=token.staked,locked=token.locked,lended=token.lended)   
                temp.append(tempToken)
                
            tempToken.amount+=float(token.free)+float(token.staked)+float(token.locked)+float(token.lended)
                
        for token in temp:
            token.value = float(token.amount)*float(getTokenPrice(token.name))
                
        for tempToken in temp:
            tempToken.printMe()
        return temp
                
    def addUnparsableToken(self,tokenName,amount):
        tempToken = getToken(tokenName,self.unparsableTokens)
        if tempToken:
            tempToken.free+=amount
        else:
            newToken = Token(name=tokenName,free=amount)
            self.unparsableTokens.append(newToken)
        
        
    def getWallet(self,address):
        for tempWallet in self.wallets:
            if tempWallet.address==address:
                return tempWallet
        
    def addWallet(self, wallet):
        
        if wallet.address == 0:
            self.wallets
        
        for tempWallet in self.wallets:
            if tempWallet.address == wallet.address:
                return "wallet already exist"
        self.wallets.append(wallet)
        
        for tempWallet in walletsGlobal:
            if tempWallet.address == wallet.address:
                return "added to portfolio, already exist in global"
        walletsGlobal.append(wallet)
                
        
    def printMe(self):
        print("--------------------")
        print("Portfilio:",self.name)
        print("Description:",self.description)
        print("Holdings:")
        tokens = self.getHoldings()
        for token in tokens:
            token.printMe()
        print("--------------------")
        
    

class Network:
    def __init__(self,name=None,parseFunction=None,wallets=[]):
        self.name = name
        self.parseFunction = parseFunction
        self.wallets = wallets

class Token:
    def __init__(self, name=None, price=0, amount=0, value=None,chart=None,links=None,fullname=None,contracts=None,staked=0,lended=0,locked=0,free=0,decimals=4,h1Change=0,h24Change=0,d7Change=0):
        self.name = name
        self.price = price
        self.amount = amount
        self.value = value
        self.chart=chart
        self.links = links
        self.fullname = fullname
        self.contracts = contracts
        self.staked = staked
        self.lended = lended
        self.locked = locked
        self.free = free
        self.decimals = decimals
        self.h1Change = h1Change
        self.h24Change = h24Change
        self.d7Change = d7Change
        
    def printMe(self):
        print("--------")
        print("token name:",self.name)
        print("amount:",self.amount)
        print("value:",self.value)
        print("--------")

def calcChanges(token):
    token = getToken(token.name)
    if token.chart is not None:
        candlesHourly = int(60/chartsTimeframe)
        token.h1Change = round(((float(token.price)/float(token.chart.open.iloc[candlesHourly]))-1)*100,2)
        token.h24Change = round(((float(token.price)/float(token.chart.open.iloc[candlesHourly*24]))-1)*100,2)
        token.d7Change = round(((float(token.price)/float(token.chart.open.iloc[candlesHourly*24*7]))-1)*100,2)

def appendToken(token,update):
    tokenSaved = getToken(token.name) 
    if tokenSaved is not None:
        tokenSaved.free= token.free if update else tokenSaved.free+token.free
        tokenSaved.price = token.price if token.price !=0 else tokenSaved.pricetokensGlobal[i].price
        updateValue(tokenSaved)
        return tokenSaved
    else:
        tokensGlobal.append(token)
        return token

def updateValue(token):
    token.amount = float(token.free+token.staked+token.lended+token.locked)
    token.value = token.amount*float(token.price) if token.price is not None else 0

def getApiResponseChart(tokenName,has,timeframe="1 D",limit=1000):
    
    token = getToken(tokenName)
    if token is None:
        return 'null'
    elif token.chart is None:
        return 'null'
    
    isWeeklyChart = timeframe == weeklyChart.split('/')[0] and limit==int( weeklyChart.split('/')[1])
    
    limit = int(limit)-1
    modePower = int(timeframe.split(" ")[0])   
    mode = timeframe.split(" ")[1]  
    skip = int(float(has)*(chartRecordsHourly if mode == 'H' else chartRecordsDaily if mode == 'D' else chartRecordsWeekly if mode == 'W' else 0)*float(modePower))
    response = pd.DataFrame(columns=(['dateTime', 'open', 'high', 'low', 'close', 'volume'] if isWeeklyChart else ['dateTime', 'open']))
    response.index = pd.to_datetime(response.index, unit='ms')
    response.set_index('dateTime', inplace=True)
    chart = token.chart
    close = 0
    open = chart.open.iloc[0+skip]
    highMax = 0
    lowMax = 1000000.0
    volume = 0
    counter = 0
    candleCounter = 0;
    

    for i in range(1+skip,len(chart.index)):        
        
        volume+=float(chart.volume.iloc[i])
        lowMax = float(lowMax) if float(lowMax) < float(chart.low.iloc[i]) else float(chart.low.iloc[i]) 
        highMax = float(highMax) if float(highMax) > float(chart.high.iloc[i]) else float(chart.high.iloc[i])
        close = chart.close.iloc[i] if close == 0 else close
        if mode=="D":            
            
            if (chart.index[i].hour == 0 and chart.index[i].minute == 0) or i==len(chart.index)-1:
                counter+=1
                if counter == modePower or i==len(chart.index)-1:
                    newRow = ""
                    if isWeeklyChart:
                        newRow = pd.DataFrame([{'index':chart.index[i],'open':open}])
                    else:
                        newRow = pd.DataFrame([{'index':chart.index[i],'open':open,'high':highMax,'low':lowMax,'close':chart.close.iloc[i],'volume':volume}])
                    newRow.index = pd.to_datetime(newRow.index, unit='ms')
                    newRow.set_index('index', inplace=True)
                    response = pd.concat([response,newRow]) if response.empty == False else newRow
                    candleCounter+=1
                    highMax = 0
                    lowMax = 1000000.0
                    volume = 0
                    close = 0
                    counter=0
                    open = chart.open[i]
                    if candleCounter > int(limit):
                        break
            else:
                continue
        elif mode=="W":
            if(chart.index[i].day_of_week==0 and chart.index[i].hour == 0 and chart.index[i].minute == 0) or i==len(chart.index)-1:
                counter+=1
                if counter==modePower or i==len(chart.index)-1:
                    newRow = ""
                    if isWeeklyChart:
                        newRow = pd.DataFrame([{'index':chart.index[i],'open':open}])
                    else:
                        newRow = pd.DataFrame([{'index':chart.index[i],'open':open,'high':highMax,'low':lowMax,'close':chart.close.iloc[i],'volume':volume}])
                    newRow.index = pd.to_datetime(newRow.index, unit='ms')
                    newRow.set_indexGetHistoricalDataBinance('index', inplace=True)
                    response = pd.concat([response,newRow]) if response.empty == False else newRow
                    candleCounter+=1
                    highMax = 0
                    lowMax = 1000000
                    volume = 0
                    close = 0
                    counter=0
                    open = chart.open[i]
                    if candleCounter > int(limit):
                        break                
                else:
                    continue
        elif mode=='H':
            if chart.index[i].minute == 0 or i==len(chart.index)-1:
                counter+=1
                if counter==modePower or i==len(chart.index)-1:
                    newRow = ""
                    if isWeeklyChart:
                        newRow = pd.DataFrame([{'index':chart.index[i],'open':open}])
                    else:
                        newRow = pd.DataFrame([{'index':chart.index[i],'open':open,'high':highMax,'low':lowMax,'close':chart.close.iloc[i],'volume':volume}])
                    newRow.index = pd.to_datetime(newRow.index, unit='ms')
                    newRow.set_index('index', inplace=True)
                    response = pd.concat([response,newRow]) if response.empty == False else newRow
                    candleCounter+=1
                    highMax = 0
                    lowMax = 1000000
                    volume = 0
                    close = 0
                    counter=0
                    open = chart.open.iloc[i]
                    if candleCounter > int(limit):
                        break
                else:
                    continue

               
            
    #print(response)
    response = response.drop(['close', 'high', 'low', 'volume'], axis=1)      
    return response.to_json()
       
def getTokenPrice(tokenName):
    return getToken(tokenName).price if getToken(tokenName) else 0

def getNetwork(name):
    for network in networksGlobal:
        if network.name == name:
            return network
    return None
    
def getToken(name,tokenList=tokensGlobal):
    for token in tokenList:
        if token.name == name:
            return token
    return None

def getPortfolio(name):
    for portfolio in portfoliosGlobal:
        if portfolio.name == name:
            print(portfolio.name)
            return portfolio

def getNetworkByName(name):
    for network in networksGlobal:
        if network.name == name:
            return network
    return None



def printPortfolios():
    for portfolio in portfoliosGlobal:
        portfolio.printMe()


def saveChart(df,tokenName):
    if df is not None:
        if tokenName == 'USDT':
            chartName = 'USDCUSDT'
        else:
            chartName = tokenName+"USDT"
        p = Path("charts/"+chartName)
        df.to_json(p)

def GetHistoricalDataBinance(howLongMins,howLongDays, tokenName):
        for check in binanceHas:
            if check==tokenName:
                print("getting "+tokenName)
                ticker = tokenName+"USDT"
                if tokenName == 'USDT':
                    ticker = 'USDCUSDT'
                # Calculate the timestamps for the binance api function
                untilThisDate = datetime.datetime.now()+datetime.timedelta(hours=binanceTime)
                sinceThisDate = untilThisDate - datetime.timedelta(days = howLongDays, minutes=howLongMins)
                # Execute the query from binance - timestamps must be converted to strings !
                candle = binanceClient.get_historical_klines(ticker, Client.KLINE_INTERVAL_5MINUTE, str(sinceThisDate), str(untilThisDate))
                candle = candle[::-1]
                # Create a dataframe to label all the columns returned by binance so we work with them later.
                df = pd.DataFrame(candle, columns=['dateTime', 'open', 'high', 'low', 'close', 'volume', 'closeTime', 'quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseVol', 'takerBuyQuoteVol', 'ignore'])
                # as timestamp is returned in ms, let us convert this back to proper timestamps.
                df.dateTime = pd.to_datetime(df.dateTime, unit='ms')
                df.set_index('dateTime', inplace=True)
                # Get rid of columns we do not needpriceLastWeek
                df = df.drop(['closeTime', 'quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseVol','takerBuyQuoteVol', 'ignore'], axis=1)

                return df
            else:
                continue

def getAllHistoricalDataBinance():
    for token in tokensGlobal:
        for check in binanceHas:
            if check==token.name:
                df = GetHistoricalDataBinance(0,2000,token.name)
                token.chart = df
                saveChart(df,token.name)

def getChartFromFile(tokenName):
    chartName = tokenName+"USDT" if tokenName != 'USDT' else 'USDCUSDT'
    p = Path('charts/'+chartName)
    return pd.read_json(p)

def getCharts():
    for token in tokensGlobal:
        if token.name in tokensInUse:
            chartName = token.name+"USDT" if token.name != 'USDT' else 'USDCUSDT'
            p = Path('charts/'+chartName)
            chart = None
            if(p.exists()):
                print(token.name,"exists")
                chart = updateHistoricalDataBinance(token.name)
            else:
                chart = GetHistoricalDataBinance(0,2000,token.name)
                saveChart(chart,token.name)
            
            token.chart = chart
            calcChanges(token)

def updateAllHistoricalDataBinance(isHourlyUpdate = False):
    for token in tokensGlobal:
        if token.chart is not None:
            token.chart = updateHistoricalDataBinance(token.name,isHourlyUpdate)
            calcChanges(token)

def updateHistoricalDataBinance(tokenName,isHourlyUpdate = False):
    token = getToken(tokenName)
    df = getChartFromFile(token.name)
    lastRow = df.index[0]
    minutesLag = (int((datetime.datetime.now()-lastRow).total_seconds()/60))+binanceTime*60
    update = GetHistoricalDataBinance(minutesLag,0,token.name)
    print("updating: "+tokenName)
    if initDone == True and isHourlyUpdate:
        updateResponse = update.drop(['close', 'high', 'low', 'volume'], axis=1)      
        new_message(None,server,'update/'+tokenName+'/'+updateResponse.to_json())
    
    chart = pd.concat([update,df]) if update.empty == False else df
    chart.index = pd.to_datetime(chart.index, unit='ms')
    if len(update.index) !=0:
        token.price = update.tail(1).close.iloc[0]
    saveChart(chart, token.name)
    return chart

def getAlgoTokens(cycle=0,wallet=None,portfolio=None,update=True,waitToLoad=0,tries=0):
    driver.get("https://explorer.perawallet.app/address/"+wallet.address+"/")
    time.sleep(waitToLoad)
    algoTokensList = driver.find_elements(By.XPATH,"//li[contains(@class, 'asset-table-row') and contains(@class, 'typography--label')]")
    for token in algoTokensList:
        name = token.find_element(By.XPATH,"a/div[1]/p").text
        price = float(token.find_element(By.XPATH,"a/div[2]/p").text[3:])
        amount = token.find_element(By.XPATH,"a/div[3]/p").text
        value = float(token.find_element(By.XPATH,"a/div[4]/p").text[3:].replace(",",""))
        amount = float(re.sub(r'([A-Z ])\w+','',amount).replace(',',''))
        temp = Token(name,price=price,free=amount) 
        if name == "Defly Token":
            temp.name = "DEFLY"
            temp.fullname = "Defly Token"
            temp.price = value/amount
        wallet.updateToken(temp)
    wallet.lastUpdate = cycle
        


def getSei(cycle=0,wallet=None,portfolio=None,update=True,waitToLoad=0,tries=0):
    driver.get('https://sei.explorers.guru/account/'+wallet.address)
    time.sleep(waitToLoad)
    name = driver.find_element(By.XPATH,"/html/body/div[1]/div[2]/div/div[2]/div/div[1]/div[2]/div/div[1]/div/div/p[1]").text
    price = float(driver.find_element(By.XPATH,"/html/body/div[1]/div[2]/div/div[2]/div/div[1]/div[2]/div/div[3]/div/p[2]").text[1:])
    amount = float(driver.find_element(By.XPATH,"/html/body/div[1]/div[2]/div/div[2]/div/div[1]/div[2]/div/div[2]").text.replace(" ",""))
    temp = Token(name=name,price=price,free=amount)
    wallet.updateToken(temp)
    wallet.lastUpdate = cycle

def getAtom(cycle=0,wallet=None,portfolio=None,update=True,waitToLoad=0,tries=0):
    driver.get('https://cosmos.explorers.guru/account/'+wallet.address)
    try:
        time.sleep(waitToLoad)
        name = "ATOM"
        amount = driver.find_element(By.XPATH,"/html/body/div[1]/div[2]/div/div[1]/div[2]/div[1]/div/p").text.split(" ")[0]
        price = getCoinMarketCapPrice(getToken(name))
        temp = Token(name,price=price,free=amount)
        wallet.updateToken(temp)
        wallet.lastUpdate = cycle
    except Exception as error:
        print(error)
        driver.get("https://atomscan.com/accounts/"+wallet.address)
        time.sleep(waitToLoad)
        name = "ATOM"
        price = getCoinMarketCapPrice(getToken(name))
        amount = float(re.search(r'(\d+\.\d+)',driver.find_element(By.XPATH,"/html/body/div[1]/div[2]/div/div/div[2]/div[1]/div[2]/div[1]/div[1]/div/div[5]/div[2]").text))
        temp = Token(name,price=price,free=amount)
        wallet.updateToken(temp)
        wallet.lastUpdate = cycle

def getTia(cycle=0,wallet=None,portfolio=None,update=True,waitToLoad=0,tries=0):
    driver.get('https://celestia.explorers.guru/account/'+wallet.address)
    time.sleep(waitToLoad)
    name = driver.find_element(By.XPATH,"/html/body/div[1]/div[2]/div/div[3]/div/div[1]/div[2]/div/div[1]/div/div/p[1]").text
    price = float(driver.find_element(By.XPATH,"/html/body/div[1]/div[2]/div/div[3]/div/div[1]/div[2]/div/div[3]/div/p[2]").text[1:])
    amount = float(driver.find_element(By.XPATH,"/html/body/div[1]/div[2]/div/div[3]/div/div[1]/div[2]/div/div[2]").text)
    temp = Token(name,price=price,free=amount)
    wallet.updateToken(temp)
    wallet.lastUpdate = cycle

def getSolTokens(cycle=0,wallet=None,portfolio=None,update=True,waitToLoad=0,tries=0):
    driver.get('https://solscan.io/account/'+wallet.address+'#stakeAccounts')
    time.sleep(waitToLoad+3)
    driver.find_element(By.XPATH,"html/body/div[1]/div[1]/div[3]/div[1]/div[2]/div/div[1]/div[1]/div/div[2]/div[3]/div[1]").find_element(By.TAG_NAME,'svg').click()
    SolTokensList = driver.find_element(By.XPATH,'/html/body/div[2]/div/div[2]').find_elements(By.XPATH,'div/div')
    for token in SolTokensList:
        name = token.find_element(By.XPATH,"div[2]/div[1]").text.split(' ')[1]
        price = float(token.find_element(By.XPATH,"div[2]/div[2]").text[0:-1])
        amount = float(token.find_element(By.XPATH,"div[2]/div").text.split(' ')[0].replace(",",''))
        temp = Token(name,price=price,free=amount)
        wallet.updateToken(temp)
    stakedSol = float(driver.find_element(By.XPATH,'/html/body/div[1]/div[1]/div[3]/div[1]/div[2]/div/div[2]/div/div[7]/div/div[1]/div[2]/div/div/div/table/tbody/tr/td[4]/div/div').text)
    freeSol = driver.find_element(By.XPATH,'/html/body/div[1]/div[1]/div[3]/div[1]/div[2]/div/div[1]/div[1]/div/div[2]/div[1]/div[2]/div/div[1]').text
    freeSol = float(re.sub(r'([A-Z ])\w+','',freeSol).replace(',',''))
    freeSolValue = float(driver.find_element(By.XPATH,'/html/body/div[1]/div[1]/div[3]/div[1]/div[2]/div/div[1]/div[1]/div/div[2]/div[1]/div[2]/div/div[2]').text[2:-1])
    price = freeSolValue/freeSol
    temp = Token("SOL",price=price,free=freeSol,staked=stakedSol)
    wallet.updateToken(temp)
    wallet.lastUpdate = cycle

def getStark(cycle=0,wallet=None,portfolio=None,update=True,waitToLoad=0,tries=0):
    driver.get('https://starkscan.co/contract/'+wallet.address+'#portfolio')
    time.sleep(waitToLoad)
    tokenName = driver.find_element(By.XPATH,'/html/body/div[1]/div/main/div/div/div[3]/dl/div/div/div/div/div/table/tr/td[1]/div[2]').text
    tokenAmount = float(driver.find_element(By.XPATH,'/html/body/div[1]/div/main/div/div/div[3]/dl/div/div/div/div/div/table/tr/td[3]').text)
    token = Token(tokenName,free=tokenAmount)
    token.price = getCoinMarketCapPrice(token)
    wallet.updateToken(token)
    wallet.lastUpdate = cycle

def getManta(cycle=0,wallet=None,portfolio=None,update=True,waitToLoad=0,tries=0):
    driver2.get('https://manta.subscan.io/account/'+wallet.address)
    time.sleep(waitToLoad)
    whole = driver2.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[2]/div[2]/div[2]/div/div/div/div/div[2]/div/div/div/div/div[1]').text
    decimals = driver2.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[2]/div[2]/div[2]/div/div/div/div/div[2]/div/div/div/div/div[2]').text
    amount = float(whole)+float(decimals)
    value = float(driver2.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[2]/div[2]/div[2]/div/div/div/div/div[2]/div/div[2]').text[3:].replace(',',''))
    name = driver2.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[2]/div[2]/div[2]/div/div/div/div/div[1]/div/a/div').text
    price = value/amount
    temp = Token(name,price=price,free=amount)
    wallet.updateToken(temp)
    wallet.lastUpdate = cycle

def getAptos(cycle=0,wallet=None,portfolio=None,update=True,waitToLoad=0,tries=0):
    driver2.get('https://aptoscan.com/account/'+wallet.address)
    time.sleep(waitToLoad)
    try:
        staked = float(driver2.find_element(By.XPATH,'/html/body/div[1]/section/main/div/div[2]/div/div[1]/div[2]/div/div[2]/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div').text)
        free = float(driver2.find_element(By.XPATH,'/html/body/div[1]/section/main/div/div[2]/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div/div[2]/div/div[1]/div').text.replace(",",""))
        name = driver2.find_element(By.XPATH,'/html/body/div[1]/section/main/div/div[2]/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div/div[2]/div/div[2]/a/div').text
        price = getCoinMarketCapPrice(getToken("APT"))
        temp = Token(name,price=price,free=free,staked=staked)
        wallet.updateToken(temp)
        wallet.lastUpdate = cycle
    except:
        driver2.get('https://aptos-explorer.xangle.io/accounts/'+wallet.address+'/coins')
        time.sleep(waitToLoad)
        price = getCoinMarketCapPrice(getToken("APT"))
        free = float(driver2.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[1]/div[4]/div[1]/table/tbody/tr/td[2]/span').text)
        name = "APT"
        staked = getToken("APT").staked
        temp = Token(name,price=price,free=free,staked=staked)
        wallet.updateToken(temp)
        wallet.lastUpdate = cycle
        

def getSui(cycle=0,wallet=None,portfolio=None,update=True,announcement = False,waitToLoad=0,tries=0):
    print('im in getSui')
    driver.get('https://suiscan.xyz/mainnet/staking/'+wallet.address)
    time.sleep(waitToLoad)
    stakedSui = 0
    suiRewardsWhole = 0
    suiRewardsDecimals = 0
    suiRewardsTotal = 0
    divNum = 4 if announcement == False else 5 
    try:
        name = driver.find_element(By.XPATH,'/html/body/div[1]/div[2]/div['+str(divNum)+']/div/div[2]/div/div[1]/div[2]/div[1]/div/div/span').text
        #name = driver.find_element(By.XPATH,'/html/body/div[1]/div[2]/div[4]/div/div[2]/div/div[1]/div[2]/div[1]/div/div/span').text
        freeSui = float(driver.find_element(By.XPATH,'/html/body/div[1]/div[2]/div['+str(divNum)+']/div/div[1]/div[1]/div/div[2]/div/div/div[1]/div/div[2]/div[1]/div[1]/span').text)
        freeSuiValue = float(driver.find_element(By.XPATH,'/html/body/div[1]/div[2]/div['+str(divNum)+']/div/div[1]/div[1]/div/div[2]/div/div/div[1]/div/div[2]/div[2]').text[1:])
        try:
            stakedSui = float(driver.find_element(By.XPATH,'/html/body/div[1]/div[2]/div['+str(divNum)+']/div/div[2]/div/div[1]/div[2]/div[1]/div/div').text[0:-3])
            suiRewardsWhole = driver.find_element(By.XPATH,'/html/body/div[1]/div[2]/div['+str(divNum)+']/div/div[2]/div/div[2]/div[2]/div[1]/div/div/span[1]').text
            suiRewardsDecimals = driver.find_element(By.XPATH,'/html/body/div[1]/div[2]/div['+str(divNum)+']/div/div[2]/div/div[2]/div[2]/div[1]/div/div/span[2]/span[2]').text
            suiRewardsTotal = float(suiRewardsWhole+"."+suiRewardsDecimals)
            suiTotal = freeSui+stakedSui+suiRewardsTotal
        except NoSuchElementException:
            suiTotal = freeSui
        price = freeSuiValue/freeSui
        temp = Token(name,price=price,free=suiTotal)
        wallet.updateToken(temp)
    except NoSuchElementException:
        if announcement==True:
            return
        getSui(wallet=wallet,portfolio=portfolio,update=update,announcement=True,waitToLoad=waitToLoad,tries=tries)
    wallet.lastUpdate = cycle

def getNearTokens(cycle=0,wallet=None,portfolio=None,update=True,waitToLoad=0,tries=0):
    driver.get('https://pikespeak.ai/wallet-explorer/'+wallet.address+'/global')
    time.sleep(waitToLoad)
    near = Token(name='NEAR',price=0,free=0)
    nearTokensList = driver.find_elements(By.XPATH,'/html/body/div[1]/div[3]/div[2]/div[2]/div/div/div/div[2]/div/div[2]/div/div/div[7]/div/div[2]/div/div/div[2]/div/table/tbody/tr')
    hNearCounted = False
    for token in nearTokensList:
        name = token.find_element(By.XPATH,'td/span/span').text
        amount = token.find_element(By.XPATH,'td[2]').text
        amount = amount[1:] if amount[0] == "<" else amount
        amount = float(amount[:-1])*1000 if amount[-1] == "K" else float(amount)
        if(re.search(r'0.00',str(amount))):
            continue
        if((name=='NEAR' or name=='hNEAR')):
            if name=='hNEAR':
                if hNearCounted==False:
                    near.free += amount
                    hNearCounted = True
            else:
                near.free += amount
        else:
            temp = Token(name,price=0,free=amount,value=0)
            wallet.updateToken(temp)
            
    if near.free > 0.001:
        near.price = getCoinMarketCapPrice(near)
        wallet.updateToken(near)
    wallet.lastUpdate = cycle

def getDot(cycle=0,wallet=None,portfolio=None,update=True,waitToLoad=0,tries=0):
    driver.get('https://www.statescan.io/#/accounts/'+wallet.address+'?tab=transfers&page=1')
    time.sleep(waitToLoad)
    freeDot = float(driver.find_element(By.XPATH,'/html/body/div[1]/div[2]/main/div[2]/div/div[2]/div/div/span/div/span[1]').text.replace(",",""))
    name = 'DOT'
    token = Token(name=name,free=freeDot)
    token.price = getCoinMarketCapPrice(token)
    wallet.updateToken(token)
    wallet.lastUpdate = cycle



def getEvmTokens(cycle=0,wallet=None,portfolio=None,update=True,waitToLoad=0,tries=0):
    driver2.get('https://bscscan.com/address/'+wallet.address+'#multichain-portfolio')
    time.sleep(waitToLoad)
    evmTokensList = driver2.find_elements(By.XPATH,'/html/body/main/section[3]/div[4]/div[18]/div/div[3]/div/table/tbody/tr')
    i = 1
    tempTokens = []
    for token in evmTokensList:
        name = token.find_element(By.XPATH,'/html/body/main/section[3]/div[4]/div[18]/div/div[3]/div/table/tbody/tr['+str(i)+']/td[2]/div').text.split("(")[1][0:-1]

        price = float((token.find_element(By.XPATH,'/html/body/main/section[3]/div[4]/div[18]/div/div[3]/div/table/tbody/tr['+str(i)+']/td[4]').text[1:].replace(',','')))
        amount = float(token.find_element(By.XPATH,'/html/body/main/section[3]/div[4]/div[18]/div/div[3]/div/table/tbody/tr['+str(i)+']/td[5]').text.replace(',',''))
        
        fullname = None
        if name=="BSC":
            name="BNB"
            fullname = "Binance Smart Chain"
        elif name=='PoS)':
            name="USDC"
        elif name=='LINK':
            fullname = 'Chainlink'
        
        if getToken(name,tempTokens) is None:
            tempTokens.append(Token(name=name,free=amount,price=price,fullname=fullname))
        else:
            getToken(name,tempTokens).free+=amount
        i+=1
    
    for tempToken in tempTokens:
        print(tempToken.name,tempToken.free)
        wallet.updateToken(tempToken)
    wallet.lastUpdate = cycle    


def getIcp(cycle=0,wallet=None,portfolio=None,update=True,waitToLoad=0,tries=0):
    driver2.get('https://dashboard.internetcomputer.org/account/'+wallet.address)
    time.sleep(waitToLoad)
    amount = float(driver2.find_element(By.XPATH,'/html/body/div[1]/div/div[32]/main/div/div[2]/div/div[2]/div[1]/div/div/div/div[2]/div/div[1]/table/tbody/tr[2]/td[2]/div/div/div/div[2]/span[1]').text.replace('’',''))
    name = driver2.find_element(By.XPATH,'/html/body/div[1]/div/div[32]/main/div/div[2]/div/div[2]/div[1]/div/div/div/div[2]/div/div[1]/table/tbody/tr[2]/td[2]/div/div/div/div[2]/span[2]').text
    price = getCoinMarketCapPrice(getToken(name))
    temp = Token(name,price=price,free=amount)
    wallet.updateToken(temp)
    wallet.lastUpdate = cycle

def getAllBalances(update,cycle=0):
    

    for portfolio in portfoliosGlobal:
        for wallet in portfolio.wallets:
            tries = 0
            if wallet.lastUpdate == cycle:
                continue
            while tries < 5:
                try:
                    tries+=1
                    if wallet.address == 0:
                        continue
                    globals()[getNetwork(wallet.network).parseFunction](cycle=cycle,wallet=wallet,update=update,waitToLoad=retryIncrement*tries,tries=tries,portfolio=portfolio)
                    break
                except Exception as error:
                    print(error)


def getNetworks():
    with open('networks', 'r') as f:
        data = json.load(f)
        for i in range(0,len(data["networks"])):      
            name = list(data["networks"][i])[0]
            function = data["networks"][i][name]
            networksGlobal.append(Network(name=name,parseFunction=function))


def applyUnparsableTokens(portfolio):
    for staked in portfolio.staked: 
        tokenName = list(staked)[0]
        amount = staked[tokenName]
        print("Staked")
        print(tokenName,amount)
        portfolio.addUnparsableToken(tokenName,amount)
        if not tokenName in tokensInUse:
            tokensInUse.append(tokenName)
            
    for locked in portfolio.locked:  
        tokenName = list(locked)[0]
        amount = locked[tokenName]
        print("Locked")
        print(tokenName,amount)
        portfolio.addUnparsableToken(tokenName,amount)
        if not tokenName in tokensInUse:
            tokensInUse.append(tokenName) 
            
    for lended in portfolio.lended:   
        tokenName = list(lended)[0]
        amount = lended[tokenName]
        print("Lended")
        print(tokenName,amount)
        portfolio.addUnparsableToken(tokenName,amount)            
        if not tokenName in tokensInUse:
            tokensInUse.append(tokenName)            
            
            
def getPortfolios():
    portfolioFiles= [f.path for f in os.scandir("portfolios")]
    
    for portfolioFile in portfolioFiles:
        with open(portfolioFile, 'r') as f:
            data = json.load(f)
            name = data["name"]
            description = data["description"]
            
            tempPortfolio = Portfolio(name, description)
            tempPortfolio.staked = data["staked"] if "staked" in data else tempPortfolio.staked
            tempPortfolio.locked = data["locked"] if "locked" in data else tempPortfolio.locked
            tempPortfolio.lended = data["lended"] if "lended" in data else tempPortfolio.lended
            
            for i in range(0,len(data["wallets"])):      
                network = list(data["wallets"][i])[0]
                wallets = data["wallets"][i][network]
                for wallet in wallets:
                    tempWallet = Wallet(address=wallet,network=network)
                    tempPortfolio.addWallet(tempWallet)
                
            portfoliosGlobal.append(tempPortfolio)            
            tempPortfolio.printMe()


                
def getTokensData():
    with open('coinsMyData', 'r') as f:
        data = json.load(f)
        for coin in data:
            print("getting data for: "+coin["name"])
            appendToken(Token(name = coin["name"]),False)
            token = getToken(coin["name"])
            if token:
                token.links = coin["links"] if "links" in coin else None
                token.contracts = coin["contracts"] if "contracts" in coin else None
                token.decimals = coin["decimals"] if "decimals" in coin else defaultDecimals

#/html/body/div[1]/div[2]/div/div[2]/div/div/div[2]/section/div/div[1]/div/img
#/html/body/div[1]/div[2]/div/div[2]/div/div/div[2]/section/div/div[1]/h1/span


def getCoinMarketCapPrice(token):
    if(token.links):
        driver.get(token.links["CoinMarketCap"])
        time.sleep(2)
        price = float(driver.find_element(By.XPATH,'/html/body/div[1]/div[2]/div/div[2]/div/div/div[2]/section/div/div[2]/span').text[1:])
        return price
    else:
        return 0

def checkAllCoinmarketcapData():
    
    for token in tokensGlobal:
        if token.name in tokensInUse:
            logo = Path("../DegenerateFolio React/React/public/images/logo/"+token.name+".png")
            
            if token.links:
                driver.get(token.links["CoinMarketCap"])
                time.sleep(2)
                
                if token.fullname is None:
                        token.fullname = driver.find_element(By.XPATH,'/html/body/div[1]/div[2]/div/div[2]/div/div/div[2]/section/div/div[1]/h1/span').text 
                
                if token.price == 0:
                    token.price = float(driver.find_element(By.XPATH,'/html/body/div[1]/div[2]/div/div[2]/div/div/div[2]/section/div/div[2]/span').text[1:].replace(',',''))
                    
                
                if(not logo.exists()):
                    if token.links:
                        driver.get(token.links["CoinMarketCap"])
                        time.sleep(2)
                        # get the image source
                        img = driver.find_element(By.XPATH,'/html/body/div[1]/div[2]/div/div[2]/div/div/div[2]/section/div/div[1]/div/img')
                        src = img.get_attribute('src')
        
        # download the image
                        urlretrieve(src, "../DegenerateFolio React/React/public/images/logo/"+token.name+".png")
                
            


def init():
    getNetworks()
    getPortfolios()
    getTokensData()
    getAllBalances(False)
    
    for portfolio in portfoliosGlobal:
        applyUnparsableTokens(portfolio)
        
    checkAllCoinmarketcapData()
    
    for portfolio in portfoliosGlobal:
        print(portfolio.getHoldings())
    
    printPortfolios()
    getCharts()
    
def updateCycle(isHourlyUpdate,cycleNumber):
    getAllBalances(True,cycleNumber) 
    updateAllHistoricalDataBinance(isHourlyUpdate)
    new_message(None, server, 'updateAllBalances/')
    printPortfolios()
    


init()
initDone = True;
server = startWsServer()
i=0

while True:
    timeUpdate = datetime.datetime.now()
    minuteUpdate = 0 if math.ceil(datetime.datetime.now().minute/chartsTimeframe)*chartsTimeframe == 60 else math.ceil(datetime.datetime.now().minute/chartsTimeframe)*chartsTimeframe
    minuteUpdate = chartsTimeframe if datetime.datetime.now().minute == 0 else minuteUpdate
    hourUpdate = timeUpdate.hour if minuteUpdate != 0 else timeUpdate.hour+1
    isNewDay = True if hourUpdate == 24 else False
    hourUpdate = 0 if hourUpdate==24 else hourUpdate
    timeUpdate = timeUpdate.replace(minute = minuteUpdate, hour = hourUpdate, second=1, day=(timeUpdate.day+1 if isNewDay else timeUpdate.day))
    secondsLeft = (timeUpdate-datetime.datetime.now()).total_seconds()
    isHourlyUpdate = (timeUpdate.minute == 0)
    print('seconds till update:',secondsLeft, str(datetime.datetime.now().hour)+":"+str(datetime.datetime.now().minute))
    print('update time:',secondsLeft, str(timeUpdate.hour)+":"+str(timeUpdate.minute))
    print('is hourly update:', isHourlyUpdate)
    if(secondsLeft<0):
        secondsLeft+=chartsTimeframe*60
    time.sleep(secondsLeft)
    print("cycle:",i)
    updateCycle(isHourlyUpdate,i)
    i+=1
    print('collected',gc.collect(),'trash')

driver.close()
driver2.close()
