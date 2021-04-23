import requests, logging, time, schedule
from logging.config import fileConfig
from requests.auth import HTTPBasicAuth
from dbhelper import initdb
from utils import geturltyped

#fileConfig('logging_suspendpbx.conf')

logger = logging.getLogger(__name__)
#requests.packages.urllib3.disable_warnings()

def checking_data_match(dn):
    b = False
    try:
        #u = geturltyped('api/pbx/suspend/{0}'.format(dn))
        #u =('http://localhost:20167/api/pbx/suspend/{0}'.format(dn))
        u =('https://billing.redtone.com/metaswitchapi1/api/subs/lcc/{0}'.format(dn))
        
        k = requests.get(u, verify=False)
        j = k.json()
        h= j['data']['lineClassCode19Field']['valueField']
        print(h)

      #  1 Allow International
        h=h[0:2]
        print(h)
        if int(h) == 1:
           print('sync')
           #if value same, update as 1(true)

        else:
            #if value not same, update as 0(false)

            print('data not sync')
            
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
            select top 2000 m_id, accountid, directorynumber, suspend from metaswitchsuspendpbx 
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

        # q = """
        #     update metaswitchsuspendpbx set m_status = 1 where m_id = ?
        #     """
        # for s in l:
        #     db.cur.execute(q, s)

    except Exception as e:
        logger.exception(str(e))

    finally:
        if db is not None:
            db.dispose()

# if __name__ == '__main__':
#     schedule.every(1).minutes.do(job)
#     while True:
#         schedule.run_pending()
#         time.sleep(5)
checking_data_match('01548407904')
