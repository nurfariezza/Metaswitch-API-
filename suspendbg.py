import requests, logging, time, schedule
from logging.config import fileConfig
from requests.auth import HTTPBasicAuth
from dbhelper import initdb
from utils import geturltyped

fileConfig('logging_suspendpbx.conf')

logger = logging.getLogger(__name__)
requests.packages.urllib3.disable_warnings()

def suspendbg(accountid, dn, suspend):
    b = False
    try:
        #u = geturltyped('api/pbx/suspend/{0}'.format(dn))
        u =('http://localhost:20167/api/bg/suspend/{0}'.format(dn))
        print(u)
        data = {
            'accountid': accountid,
            'dn': dn,
            'suspend': suspend
        }
        print(data)
        #u =('http://localhost:20167/api/pbx/suspend/01548407904')
        if suspend == 0:
            #u =('http://localhost:20167/api/pbx/suspend/01548407904')

            #u = geturltyped('api/pbx/resume/{0}'.format(dn))
            u =('http://localhost:20167/api/pbx/resume/{0}'.format(dn))

            print(dn)
           
        k = requests.put(u, json=data, verify=False)  
        # k = requests.put(u, verify=False)
        print(k)
        j = k.json()
        print(j)
        if j.get('success') == 1:
            b = True

    except Exception as e:
        logger.exception(str(e))

    time.sleep(2)

    return b

def job():
    db = None

    try:
        db = initdb()
        l = []
        q = """
            select top 2000 m_id, accountid, directorynumber, suspend from metaswitchsuspendbg 
            where m_status = 0 
            order by m_id
            """
        rows = db.cur.execute(q).fetchall()
        for r in rows:
            dn = r.directorynumber.strip()
            print(dn)
            b = suspendpbx(r.accountid, dn, r.suspend)
            print(b)
            if b:
                l.append(r.m_id)

        q = """
            update metaswitchsuspendbg set m_status = 1 where m_id = ?
            """
        for s in l:
            db.cur.execute(q, s)

    except Exception as e:
        logger.exception(str(e))

    finally:
        if db is not None:
            db.dispose()

if __name__ == '__main__':
    schedule.every(1).minutes.do(job)
    while True:
        schedule.run_pending()
        time.sleep(5)
