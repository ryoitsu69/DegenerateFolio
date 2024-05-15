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


chartsTimeframe = 5 #mins
chartRecordsHourly = (60/chartsTimeframe)
chartRecordsDaily = (60/chartsTimeframe)*24
chartRecordsWeekly = chartRecordsDaily*7
weeklyChart = "1 H/168";

startedAt = datetime.datetime.now()

initDone = False;

binanceTime = -3
binanceClient = Client("zdoSQtX7nWhlJe2122TaGbKteqq6pBwCKJ095iYOvLUmGvogyDuG2sRQSfzOFTrs", "k8DJA9vAjJHnZlywfq81BR4cp2ufUWi9dYxcQvGAzCiH3LwU8scDn6MD9fpzlO6l")
binanceHas = ["SUI",'APT',"CYBER","NEAR","OP","ARB","ETH","ID","BNB","AVAX","WOO","FTM","GLMR","STG","USDC","MATIC","DOT","MANTA","STRK","PYTH","JUP","SEI","TIA","ALGO","FIL", "SOL", "ATOM","ICP","LINK"]
updateTimer = 15*60 #15 mins





waitToLoad = 5 #seconds
tokens = []


        
def new_client(client, server):
	server.send_message_to_all("Hey all, a new client has joined us")

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
        server.send_message(client,'balances/'+allBalancesToJson())
    elif type =='updateAllBalances':
        server.send_message_to_all('updateAllBalances/'+allBalancesToJson())
    elif type == 'update':
        token = params[1]
        update = params[2]
        server.send_message_to_all('update/'+token+'/'+update)
    print(message)
    
def startWsServer():
    server = WebsocketServer(host='192.168.50.252', port=13226 , loglevel=logging.INFO)
    server.set_fn_new_client(new_client)
    server.set_fn_message_received(new_message)
    server.run_forever(True)
    return server

driver = webdriver.Firefox()
driver2 = webdriver.Chrome()

print("Started at:",datetime.datetime.now())



def allBalancesToJson():
    jsonResponse = '['
    
    for i in range(0,len(tokens)):
        if tokens[i].amount > 0:
            jsonResponse += '{'
            jsonResponse += '"ticker":'
            jsonResponse += '"'+tokens[i].name+'",'
            jsonResponse += '"amount":'
            jsonResponse += str(tokens[i].amount)+','
            jsonResponse += '"price":'
            jsonResponse += str(tokens[i].price) if tokens[i].price is not None else 'null'
            jsonResponse += ','
            jsonResponse += '"fullname":'
            jsonResponse += '"'+str(tokens[i].fullname)+'"' if tokens[i].fullname is not None else 'null'
            jsonResponse += ','
            jsonResponse += '"decimals":'
            jsonResponse += str(tokens[i].decimals)
            jsonResponse += ','
            jsonResponse += '"staked":'
            jsonResponse += str(tokens[i].staked)
            jsonResponse += ','
            jsonResponse += '"landed":'
            jsonResponse += str(tokens[i].landed)
            jsonResponse += ','
            jsonResponse += '"locked":'
            jsonResponse += str(tokens[i].locked)
            jsonResponse += ','
            jsonResponse += '"h1Change":'
            jsonResponse += str(tokens[i].h1Change)
            jsonResponse += ','
            jsonResponse += '"h24Change":'
            jsonResponse += str(tokens[i].h24Change)
            jsonResponse += ','
            jsonResponse += '"d7Change":'
            jsonResponse += str(tokens[i].d7Change)
            jsonResponse += '}'
            jsonResponse += '' if i==(len(tokens)-1) else ","
    jsonResponse += ']'
    #print(jsonResponse)
    return jsonResponse

class Token:
    def __init__(self, name=None, price=0, amount=0, value=None,chart=None,links=None,fullname=None,contracts=None,staked=0,landed=0,locked=0,free=0,decimals=4,h1Change=0,h24Change=0,d7Change=0):
        self.name = name
        self.price = price
        self.amount = amount
        self.value = value
        self.chart=chart
        self.links = links
        self.fullname = fullname
        self.contracts = contracts
        self.staked = staked
        self.landed = landed
        self.locked = locked
        self.free = free
        self.decimals = decimals
        self.h1Change = h1Change
        self.h24Change = h24Change
        self.d7Change = d7Change

def calcChanges(token):
    print('im here :',token.name)
    if token.chart is not None:
        candlesHourly = int(60/chartsTimeframe)
        token.h1Change = round(((float(token.price)/float(token.chart.open.iloc[candlesHourly]))-1)*100,2)
        print('price :',token.price)
        print('price 1h ago :',token.chart.open.iloc[candlesHourly])
        print('change :',token.h1Change)
        token.h24Change = round(((float(token.price)/float(token.chart.open.iloc[candlesHourly*24]))-1)*100,2)
        print('price :',token.price)
        print('price 24h ago :',token.chart.open.iloc[candlesHourly*24])
        print('change :',token.h24Change)
        token.d7Change = round(((float(token.price)/float(token.chart.open.iloc[candlesHourly*24*7]))-1)*100,2)
        print('price :',token.price)
        print('price 7d ago :',token.chart.open.iloc[candlesHourly*24*7])
        print('change :',token.d7Change)

def appendToken(token,update):
    tokenSaved = getToken(token.name) 
    if tokenSaved is not None:
        tokenSaved.free= token.free if update else tokenSaved.free+token.free
        tokenSaved.staked= token.staked if update else tokenSaved.staked+token.staked
        tokenSaved.price = token.price if token.price !=0 else tokenSaved.price
        updateValue(tokenSaved)
        return tokenSaved
    else:
        tokens.append(token)
        updateValue(token)
        return token

def updateValue(token):
    token.amount = float(token.free+token.staked+token.landed+token.locked)
    token.value = token.amount*float(token.price) if token.price is not None else 0

def getApiResponseChart(tokenName,has,timeframe="1 D",limit=1000):
    
    token = getToken(tokenName)
    if token.chart is None:
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
        
def getToken(name):
    for token in tokens:
        if token.name == name:
            return token
    return None


def printTokens():
    for token in tokens:
        print(token.name," price:",token.price," amount:",token.amount,"value:",token.value)




def saveChart(df,tokenName):
    if df is not None:
        p = Path("charts/"+tokenName+"USDT")
        df.to_json(p)

def GetHistoricalDataBinance(howLongMins,howLongDays, tokenName):
        for check in binanceHas:
            if check==tokenName:
                print("getting "+tokenName)
                ticker = tokenName+"USDT"
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
    for token in tokens:
        for check in binanceHas:
            if check==token.name:
                df = GetHistoricalDataBinance(0,2000,token.name)
                token.chart = df
                saveChart(df,token.name)

def getChartFromFile(tokenName):
    return pd.read_json('charts/'+tokenName+"USDT")

def getCharts():
    for token in tokens:
        p = Path('charts/'+token.name+"USDT")
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
    for token in tokens:
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

def getAlgoTokens(address,update=True):
    driver.get("https://explorer.perawallet.app/address/"+address+"/")
    time.sleep(waitToLoad)
    algoTokensList = driver.find_elements(By.XPATH,"//li[contains(@class, 'asset-table-row') and contains(@class, 'typography--label')]")
    for token in algoTokensList:
        name = token.find_element(By.XPATH,"a/div[1]/p").text
        price = float(token.find_element(By.XPATH,"a/div[2]/p").text[3:])
        amount = token.find_element(By.XPATH,"a/div[3]/p").text
        value = float(token.find_element(By.XPATH,"a/div[4]/p").text[3:])
        amount = float(re.sub(r'([A-Z ])\w+','',amount).replace(',',''))
        temp = Token(name,price=price,free=amount) 
        if name == "Defly Token":
            temp.name = "DEFLY"
            temp.fullname = "Defly Token"
            temp.price = value/amount
        updateValue(appendToken(temp,update))
        


def getSei(address,update=True):
    driver.get('https://sei.explorers.guru/account/'+address)
    time.sleep(waitToLoad)
    name = driver.find_element(By.XPATH,"/html/body/div[1]/div[2]/div/div[2]/div/div[1]/div[2]/div/div[1]/div/div/p[1]").text
    price = float(driver.find_element(By.XPATH,"/html/body/div[1]/div[2]/div/div[2]/div/div[1]/div[2]/div/div[3]/div/p[2]").text[1:])
    amount = float(driver.find_element(By.XPATH,"/html/body/div[1]/div[2]/div/div[2]/div/div[1]/div[2]/div/div[2]").text)
    appendToken(Token(name,price=price,free=amount),update)

def getAtom(address,update=True):
    driver.get('https://cosmos.explorers.guru/account/'+address)
    try:
        time.sleep(waitToLoad)
        name = driver.find_element(By.XPATH,"/html/body/div[1]/div[2]/div/div[2]/div/div[1]/div[2]/div/div[1]/div/div/p[1]").text
        price = float(driver.find_element(By.XPATH,"/html/body/div[1]/div[2]/div/div[2]/div/div[1]/div[2]/div/div[3]/div/p[2]").text[1:])
        amount = float(driver.find_element(By.XPATH,"/html/body/div[1]/div[2]/div/div[2]/div/div[1]/div[2]/div/div[2]").text)
        appendToken(Token(name,price=price,free=amount),update)
    except:
        driver.get("https://atomscan.com/accounts/cosmos1d6j4xs7l55s2lsy2vqdalj25ef9rj72y05ne0m")
        time.sleep(waitToLoad)
        name = "ATOM"
        price = float(driver.find_element(By.XPATH,"/html/body/div[1]/div[2]/div/div/div[2]/div[1]/div[2]/div[1]/div[1]/div/div[1]/div[2]").split("(")[1].text[1:-1])
        amount = float(driver.find_element(By.XPATH,"/html/body/div[1]/div[2]/div").split(" ")[0].text)
        appendToken(Token(name,price=price,free=amount),update)

def getTia(address,update=True):
    driver.get('https://celestia.explorers.guru/account/'+address)
    time.sleep(waitToLoad)
    name = driver.find_element(By.XPATH,"/html/body/div[1]/div[2]/div/div[3]/div/div[1]/div[2]/div/div[1]/div/div/p[1]").text
    price = float(driver.find_element(By.XPATH,"/html/body/div[1]/div[2]/div/div[3]/div/div[1]/div[2]/div/div[3]/div/p[2]").text[1:])
    amount = float(driver.find_element(By.XPATH,"/html/body/div[1]/div[2]/div/div[3]/div/div[1]/div[2]/div/div[2]").text)
    appendToken(Token(name,price=price,free=amount),update)

def getSolTokens(address,update=True):
    driver.get('https://solscan.io/account/'+address+'#stakeAccounts')
    time.sleep(waitToLoad+3)
    driver.find_element(By.XPATH,"html/body/div[1]/div[1]/div[3]/div[1]/div[2]/div/div[1]/div[1]/div/div[2]/div[3]/div[1]").find_element(By.TAG_NAME,'svg').click()
    SolTokensList = driver.find_element(By.XPATH,'/html/body/div[2]/div/div[2]').find_elements(By.XPATH,'div/div')
    for token in SolTokensList:
        name = token.find_element(By.XPATH,"div[2]/div[1]").text.split(' ')[1]
        price = float(token.find_element(By.XPATH,"div[2]/div[2]").text[0:-1])
        amount = float(token.find_element(By.XPATH,"div[2]/div").text.split(' ')[0].replace(",",''))
        appendToken(Token(name,price,free=amount),update)
    stakedSol = float(driver.find_element(By.XPATH,'/html/body/div[1]/div[1]/div[3]/div[1]/div[2]/div/div[2]/div/div[7]/div/div[1]/div[2]/div/div/div/table/tbody/tr/td[4]/div/div').text)
    freeSol = driver.find_element(By.XPATH,'/html/body/div[1]/div[1]/div[3]/div[1]/div[2]/div/div[1]/div[1]/div/div[2]/div[1]/div[2]/div/div[1]').text
    freeSol = float(re.sub(r'([A-Z ])\w+','',freeSol).replace(',',''))
    freeSolValue = float(driver.find_element(By.XPATH,'/html/body/div[1]/div[1]/div[3]/div[1]/div[2]/div/div[1]/div[1]/div/div[2]/div[1]/div[2]/div/div[2]').text[2:-1])
    price = freeSolValue/freeSol
    appendToken(Token("SOL",price=price,free=freeSol,staked=stakedSol),update)

def getStark(address,update=True):
    driver.get('https://starkscan.co/contract/'+address+'#portfolio')
    time.sleep(waitToLoad)
    tokenName = driver.find_element(By.XPATH,'/html/body/div[1]/div/main/div/div/div[3]/dl/div/div/div/div/div/table/tr/td[1]/div[2]').text
    tokenAmount = float(driver.find_element(By.XPATH,'/html/body/div[1]/div/main/div/div/div[3]/dl/div/div/div/div/div/table/tr/td[3]').text)
    token = Token(tokenName,free=tokenAmount)
    token.price = getCoinMarketCapPrice(token)
    appendToken(token,update)

def getManta(address,update=True):
    driver2.get('https://manta.subscan.io/account/'+address)
    time.sleep(waitToLoad)
    whole = driver2.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[2]/div[2]/div[2]/div/div/div/div/div[2]/div/div/div/div/div[1]').text
    decimals = driver2.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[2]/div[2]/div[2]/div/div/div/div/div[2]/div/div/div/div/div[2]').text
    amount = float(whole)+float(decimals)
    value = float(driver2.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[2]/div[2]/div[2]/div/div/div/div/div[2]/div/div[2]').text[3:].replace(',',''))
    name = driver2.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[2]/div[2]/div[2]/div/div/div/div/div[1]/div/a/div').text
    price = value/amount
    appendToken(Token(name,price=price,free=amount),update)

def getAptos(address,update=True):
    driver2.get('https://aptoscan.com/account/'+address)
    time.sleep(waitToLoad)
    try:
        price = float(driver2.find_element(By.XPATH,'/html/body/div[1]/section/main/div/div[2]/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[2]/div/div[2]/div').text[1:-9])
        staked = float(driver2.find_element(By.XPATH,'/html/body/div[1]/section/main/div/div[2]/div/div[1]/div[2]/div/div[2]/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div').text)
        free = float(driver2.find_element(By.XPATH,'/html/body/div[1]/section/main/div/div[2]/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div/div[2]/div/div[1]/div').text)
        name = driver2.find_element(By.XPATH,'/html/body/div[1]/section/main/div/div[2]/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div/div[2]/div/div[2]/a/div').text
        appendToken(Token(name,price=price,free=free,staked=staked),update)
    except:
        driver2.get('https://aptos-explorer.xangle.io/accounts/'+address+'/coins')
        time.sleep(waitToLoad)
        price = getCoinMarketCapPrice(getToken("APT"))
        free = float(driver2.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[1]/div[4]/div[1]/table/tbody/tr/td[2]/span').text)
        name = "APT"
        staked = getToken("APT").staked
        appendToken(Token(name,price=price,free=free,staked=staked),update)

def getSui(address,update=True,announcement = False):
    driver.get('https://suiscan.xyz/mainnet/staking/'+address)
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
        appendToken(Token(name,price=price,free=suiTotal),update)
    except NoSuchElementException:
        getSui(address,update,True)

def getNearTokens(address,update=True):
    driver.get('https://pikespeak.ai/wallet-explorer/'+address+'/global')
    time.sleep(waitToLoad)
    near = Token(name='NEAR',price=0,free=0)
    nearTokensList = driver.find_elements(By.XPATH,'/html/body/div[1]/div[3]/div[2]/div[2]/div/div/div/div[2]/div/div[2]/div/div/div[7]/div/div[2]/div/div/div[2]/div/table/tbody/tr')
    hNearCounted = False
    for token in nearTokensList:
        name = token.find_element(By.XPATH,'td/span/span').text
        amount = token.find_element(By.XPATH,'td[2]').text
        if(re.search(r'0.00',amount)):
            continue
        if((name=='NEAR' or name=='hNEAR')):
            if name=='hNEAR':
                if hNearCounted==False:
                    near.free += float(amount)
                    hNearCounted = True
            else:
                near.free += float(amount)
        else:
            appendToken(Token(name,None,float(amount),None),update)
    if near.free > 0.001:
        near.price = getCoinMarketCapPrice(near)
        appendToken(near,update)

def getDot(address,update=True):
    driver.get('https://www.statescan.io/#/accounts/'+address+'?tab=transfers&page=1')
    time.sleep(waitToLoad)
    freeDot = float(driver.find_element(By.XPATH,'/html/body/div[1]/div[2]/main/div[2]/div/div[2]/div/div/span/div/span[1]').text)
    name = 'DOT'
    token = Token(name=name,free=freeDot)
    token.price = getCoinMarketCapPrice(token)
    appendToken(token,update)



def getEvmTokens(address,update=True):
    #0x4AE673F8898408d39966dE7ECC0BD7128b4b912E
    driver2.get('https://bscscan.com/address/'+address+'#multichain-portfolio')
    time.sleep(waitToLoad)
    evmTokensList = driver2.find_elements(By.XPATH,'/html/body/main/section[3]/div[4]/div[18]/div/div[3]/div/table/tbody/tr')
    i = 1
    print("Im retarded getEvmTokens()", len(evmTokensList))
    for token in evmTokensList:
        name = token.find_element(By.XPATH,'/html/body/main/section[3]/div[4]/div[18]/div/div[3]/div/table/tbody/tr['+str(i)+']/td[2]/div').text.split("(")[1][0:-1]

        price = float((token.find_element(By.XPATH,'/html/body/main/section[3]/div[4]/div[18]/div/div[3]/div/table/tbody/tr['+str(i)+']/td[4]').text[1:].replace(',','')))
        amount = float(token.find_element(By.XPATH,'/html/body/main/section[3]/div[4]/div[18]/div/div[3]/div/table/tbody/tr['+str(i)+']/td[5]').text.replace(',',''))
        
        temp = Token(name=name,price=price,free=amount)
        
        if temp.name=="BSC":
            temp.name="BNB"
            temp.fullname = "Binance Smart Chain"
        elif name=='PoS)':
            temp.name="USDC"     
        elif temp.name=='LINK':
            temp.fullname = 'Chainlink'
        appendToken(temp,update)
        i+=1


def getIcp(address,update=True):
    driver2.get('https://dashboard.internetcomputer.org/account/'+address)
    time.sleep(waitToLoad)
    amount = float(driver2.find_element(By.XPATH,'/html/body/div[1]/div/div[32]/main/div/div[2]/div/div[2]/div[1]/div/div/div/div[2]/div/div[1]/table/tbody/tr[2]/td[2]/div/div/div/div[2]/span[1]').text)
    name = driver2.find_element(By.XPATH,'/html/body/div[1]/div/div[32]/main/div/div[2]/div/div[2]/div[1]/div/div/div/div[2]/div/div[1]/table/tbody/tr[2]/td[2]/div/div/div/div[2]/span[2]').text
    price = getCoinMarketCapPrice(getToken(name))
    appendToken(Token(name=name,free=amount,price=price),update)

def getAllBalances(update):
    getIcp('4b6e620621b73ac1e3d04ac6e79263ff5d2f558746d24526135d0e70b40bb6bf',update)
    getSolTokens('4cmGDc1HZDAnvgD1L8a3TB4kYkP3Ax25DH4PJsszVHAx',update)
    getEvmTokens('0x4AE673F8898408d39966dE7ECC0BD7128b4b912E',update)
    getSui('0x87cd28977f1f891d514de4ef094d08b5cfcc05d0994c98e19afd1a90d557e0bf',update)
    getNearTokens('ifalafel.tg',update)
    getDot('13gBrKGMhttuNjywbmEfK5NFeNbHpbQGbJtFVRMmUWHaSNZf',update)
    getAptos('0x76ad44ec66b2169b10eb53b4daa856624d47c007e69efd8418f20dc5d92b7071',update)
    getManta('dfXTwYi1M9KsyoqjHNaoSJQ1eEUFPVY1Xdjh1DnnL5VcUYn4f',update)
    getStark('0x045e33392ae862fbcdf880a6aae90807c3c784bd323378884861182cda264762',update)
    getAtom('cosmos1d6j4xs7l55s2lsy2vqdalj25ef9rj72y05ne0m',update)
    getSei('sei1nk77dnzkesy2dju74n3lj4ru0h8pac0hq6kaz9',update)
    getTia('celestia1d6j4xs7l55s2lsy2vqdalj25ef9rj72y77zf4k',update)
    getAlgoTokens('4TMDKRZYJGMG4FJXFSROSGWBJ7KW26ZWLDH7XKS4D6PAS6YK6DUOEAD65Q',update)

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
                token.staked = coin["staked"] if "staked" in coin else 0
                token.landed = coin["landed"] if "landed" in coin else 0
                token.locked = coin["locked"] if "locked" in coin else 0
                print("i'm in data")
                print(token.links)
            
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
    
    for token in tokens:
        logo = Path('images/logo/'+token.name+".png")
        
        if token.links:
            driver.get(token.links["CoinMarketCap"])
            time.sleep(2)
            
            if token.fullname is None:
                    token.fullname = driver.find_element(By.XPATH,'/html/body/div[1]/div[2]/div/div[2]/div/div/div[2]/section/div/div[1]/h1/span').text 
            
            if token.price == 0:
                token.price = float(driver.find_element(By.XPATH,'/html/body/div[1]/div[2]/div/div[2]/div/div/div[2]/section/div/div[2]/span').text[1:])
                
            
            if(logo.exists()):
                print(token.name)
            else: 
                if token.links:
                    driver.get(token.links["CoinMarketCap"])
                    time.sleep(2)
                    # get the image source
                    img = driver.find_element(By.XPATH,'/html/body/div[1]/div[2]/div/div[2]/div/div/div[2]/section/div/div[1]/div/img')
                    src = img.get_attribute('src')
    
    # download the image
                    urlretrieve(src, "images/logo/"+token.name+".png")
            
        updateValue(token)


def init():
    getTokensData()
    getAllBalances(False)
    checkAllCoinmarketcapData()
    printTokens()
    getCharts()
    
def updateCycle(isHourlyUpdate):
    getAllBalances(True) 
    updateAllHistoricalDataBinance(isHourlyUpdate)
    new_message(None, server, 'updateAllBalances/')
    printTokens()
    


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
    time.sleep(secondsLeft)
    print("cycle:",i)
    updateCycle(isHourlyUpdate)
    i+=1
    print('collected',gc.collect(),'trash')

driver.close()
driver2.close()
