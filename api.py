from flask import Flask
from flask_restful import Resource, Api
from flask_restful import reqparse
from flaskext.mysql import MySQL
#from flask_mysql import MySQL
from lxml import html
from datetime import datetime, timedelta
import requests
import unicodedata
from pytz import UTC, timezone
import re
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

mysql = MySQL()
app = Flask(__name__)

# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = '109QpoL'
app.config['MYSQL_DATABASE_DB'] = 'tibiapk'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

mysql.init_app(app)

api = Api(app)

scheduler = BackgroundScheduler()
scheduler.start()


class AuthenticateUser(Resource):
    def post(self):
        try:
            # Parse the arguments

            parser = reqparse.RequestParser()
            parser.add_argument('email', type=str, help='Email address for Authentication')
            parser.add_argument('password', type=str, help='Password for Authentication')
            args = parser.parse_args()

            _userEmail = args['email']
            _userPassword = args['password']

            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_AuthenticateUser',(_userEmail,))
            data = cursor.fetchall()

            
            if(len(data)>0):
                if(str(data[0][2])==_userPassword):
                    return {'status':200,'UserId':str(data[0][0])}
                else:
                    return {'status':100,'message':'Authentication failure'}

        except Exception as e:
            return {'error': str(e)}


class GetAllItems(Resource):
    def post(self):
        try: 
            # Parse the arguments
            parser = reqparse.RequestParser()
            parser.add_argument('id', type=str)
            args = parser.parse_args()

            _userId = args['id']

            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_GetAllItems',(_userId,))
            data = cursor.fetchall()

            items_list=[];
            for item in data:
                i = {
                    'Id':item[0],
                    'Item':item[1]
                }
                items_list.append(i)

            return {'StatusCode':'200','Items':items_list}

        except Exception as e:
            return {'error': str(e)}

class AddItem(Resource):
    def post(self):
        try: 
            # Parse the arguments
            parser = reqparse.RequestParser()
            parser.add_argument('id', type=str)
            parser.add_argument('item', type=str)
            args = parser.parse_args()

            _userId = args['id']
            _item = args['item']

            print (_userId);

            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_AddItems',(_userId,_item))
            data = cursor.fetchall()

            conn.commit()
            return {'StatusCode':'200','Message': 'Success'}

        except Exception as e:
            return {'error': str(e)}
        
                

class CreateUser(Resource):
    def post(self):
        try:
            # Parse the arguments
            parser = reqparse.RequestParser()
            parser.add_argument('email', type=str, help='Email address to create user')
            parser.add_argument('password', type=str, help='Password to create user')
            args = parser.parse_args()

            _userEmail = args['email']
            _userPassword = args['password']

            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('spCreateUser',(_userEmail,_userPassword))
            data = cursor.fetchall()

            if len(data) is 0:
                conn.commit()
                return {'StatusCode':'200','Message': 'User creation success'}
            else:
                return {'StatusCode':'1000','Message': str(data[0])}

        except Exception as e:
            return {'error': str(e)}

class GetDeaths(Resource):
    def post(self):
        try:
            # Parse the arguments
            parser = reqparse.RequestParser()
            parser.add_argument('email', type=str, help='Email address to create user')
            parser.add_argument('password', type=str, help='Password to create user')
            args = parser.parse_args()

            _userEmail = args['email']
            _userPassword = args['password']

            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('spCreateUser',(_userEmail,_userPassword))
            data = cursor.fetchall()

            if len(data) is 0:
                conn.commit()
                return {'StatusCode':'200','Message': 'User creation success'}
            else:
                return {'StatusCode':'1000','Message': str(data[0])}

        except Exception as e:
            return {'error': str(e)}

def hasDiedLast15Minutes(url):
    page2 = requests.get(url)
    tree2 = html.fromstring(page2.content)

    deathlistFirst2 = tree2.xpath('//*[@id="characters"]/div[5]/div/div/table[3]/tr[2]/td[1]/text()')
    deathConfirm = tree2.xpath('//*[@id="characters"]/div[5]/div/div/table[3]/tr[1]/td/b[text()="Character Deaths"]')
    deathType = tree2.xpath('//*[@id="characters"]/div[5]/div/div/table[3]/tr[2]/td[2]/text()')
    #Jan 23 2017, 20:50:21 CET

    if len(deathConfirm) <= 0:
        return False, False, False

    decodedDate = unicodedata.normalize("NFKD", deathlistFirst2[0])
    decodedDeathType = unicodedata.normalize("NFKD", deathType[0])

    CET = timezone('CET')
    EST = timezone('US/Eastern')
    
    a = datetime.strptime(decodedDate.rsplit(' ', 1)[0], '%b %d %Y, %H:%M:%S')#.timestamp()
    b = datetime.now()#.timestamp()

    #print(CET.localize(a).astimezone(UTC))

    deathTime = CET.localize(a).astimezone(UTC).timestamp()
    nowTime = EST.localize(b).astimezone(UTC).timestamp()

    pvpTerms = ['Killed', 'Slain', 'Crushed', 'Eliminated', 'Annihilated']
    if decodedDeathType.split(' ', 1)[0] in pvpTerms:
        dtype = 'Player '
    else:
        dtype = 'Monster'

    timeInSeconds = (nowTime - deathTime)

    m, s = divmod(timeInSeconds, 60)
    deathAge = ("%02dm %02ds ago" % (m, s))

    #print(deathAge)

    if timeInSeconds > 900:
        death = False
    elif timeInSeconds < 900:
        death = True
    else:
        death = False
        
    return death, dtype, deathAge
    
def isRecentDeath(datetime):
    decodedDate = unicodedata.normalize("NFKD", datetime)

    CET = timezone('CET')
    EST = timezone('US/Eastern')
    
    a = datetime.strptime(decodedDate.rsplit(' ', 1)[0], '%b %d %Y, %H:%M:%S')
    b = datetime.now()

    deathTime = CET.localize(a).astimezone(UTC).timestamp()
    nowTime = EST.localize(b).astimezone(UTC).timestamp()
    
    timeInSeconds = (nowTime - deathTime)

    m, s = divmod(timeInSeconds, 60)
    deathAge = ("%02dm %02ds ago" % (m, s))

    if timeInSeconds > 900:
        death = False
    elif timeInSeconds < 900:
        death = True
    else:
        death = False
        
    return death
    
def resetOnlinePlayers():
    conn = mysql.connect()
    cursor = conn.cursor()
    
    cursor.callproc('removeOldPlayers')
    playerTable = getOnlinePlayers('https://secure.tibia.com/community/?subtopic=worlds&world=Antica')
    for x in range(0, len(playerTable) - 1):
        playerName = playerTable[x]
        print(playerName)
        cursor.callproc('addPlayer',(playerName,))
        data = cursor.fetchall()
        conn.commit()
        
def getOnlinePlayers(url):
    tree = html.fromstring(requests.get(url).content)
    oddPlayers = tree.xpath('//tr[@class="Odd"]/td[1]/a[contains(@href,"tibia.com")]/text()')
    evenPlayers = tree.xpath('//tr[@class="Even"]/td[1]/a[contains(@href,"tibia.com")]/text()')
    combined = oddPlayers + evenPlayers
    
    return combined

def storePlayerDeaths():
    conn = mysql.connect()
    cursor = conn.cursor()
    
    cursor.callproc('removeOldDeaths')
    cursor.callproc('getAllPlayers')
    data = cursor.fetchall()

    for player in data:
        #i = player[0]
        #players_list.append(i)
        storeDeaths(player[0])
        
def storeDeaths(name):
    url = 'https://secure.tibia.com/community/?subtopic=characters&name=' + name + ''
    page = requests.get(url)
    tree = html.fromstring(page.content)
    
    deathConfirm = tree.xpath('//*[@id="characters"]/div[5]/div/div/table[3]/tr[1]/td/b[text()="Character Deaths"]')
    
    if len(deathConfirm) <= 0:
      return False
    
    conn = mysql.connect()
    cursor = conn.cursor()
    
    numDeaths = len(tree.xpath('//*[@id="characters"]/div[5]/div/div/table[3]/tr'))
    
    x = 2
    deathRowTime = tree.xpath('//*[@id="characters"]/div[5]/div/div/table[3]/tr[' + x + ']/td[1]/text()')
    deathRowMessage = tree.xpath('//*[@id="characters"]/div[5]/div/div/table[3]/tr[' + x + ']/td[2]/text()')
    while (isRecentDeath(deathRow) and x < numDeaths):
        cursor.callproc('addDeath',(name,deathRowTime,deathRowMessage,))

#def getPlayerDeaths

#resetOnlinePlayers('https://secure.tibia.com/community/?subtopic=worlds&world=Antica')
    
#for x in range(0, len(antica) - 1):
#    player = antica[x]
#    dead, dtype, deathAge = hasDiedLast15Minutes(player)
#    if dead:
#        name = unicodedata.normalize("NFKD", re.search('characters&name=(\S+)$', player).group(1))
#        print("DEATH (" + dtype + ") [" + deathAge + "] - " + name.replace("+", " "))

#print(datetime.now() - startTime)
                        
api.add_resource(CreateUser, '/CreateUser')
api.add_resource(AuthenticateUser, '/AuthenticateUser')
api.add_resource(AddItem, '/AddItem')
api.add_resource(GetAllItems, '/GetAllItems')
api.add_resource(GetDeaths, '/GetDeaths')

if __name__ == '__main__':
    app.run(debug=True)
