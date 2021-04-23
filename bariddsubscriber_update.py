import requests, logging, time, schedule
from logging.config import fileConfig
from dbhelper import initdb
from utils import geturltyped

fileConfig('logging_bariddsubscriber.conf')

logger = logging.getLogger(__name__)
requests.packages.urllib3.disable_warnings()

def bariddsubs(dn, allow):
    b = False

    try:
        u = geturltyped('api/subs/lcc/{0}/{1}'.format(dn, allow))
        k = requests.post(u, verify=False)
        j = k.json()
        if j.get('success') == 1:
            b = True

    except Exception as e:
        logger.exception(str(e))

    time.sleep(2)

    return b


def checking_data_match(dn, allow):
    h = False
    try:
        #u = geturltyped('api/pbx/suspend/{0}'.format(dn))
        #u =('http://localhost:20167/api/pbx/suspend/{0}'.format(dn))
        #u =('https://billing.redtone.com/metaswitchapi1/api/subs/lcc/{0}'.format(dn))
        u = geturltyped('api/subs/lcc/{0}'.format(dn))

        #print('==='+str(allow))
        k = requests.get(u, verify=False)
        j = k.json()
        x= j['data']['lineClassCode19Field']['valueField']
        print(x)

        # 1 Allow International
        x=x[0:2]
        print(x)
        if int(x) == int(allow):
           print('sync')
           h = True
            
    except Exception as e:
        logger.exception(str(e))

    time.sleep(2)

    return h



def job():
    db = None

    try:
        db = initdb()
        l = []
        q = """
            select top 2000 m_id, accountid, directorynumber, allow from MetaSwitchBarIDDPBX_dup where m_status = 0
            """
        rows = db.cur.execute(q).fetchall()
        for r in rows:
            dn = r.directorynumber.strip()
            b = bariddsubs(dn, r.allow)
            if b:
                l.append(r.m_id)

        q = """
            update MetaSwitchBarIDDPBX_dup set m_status = 1 where m_id = ?
            """
        for s in l:
            db.cur.execute(q, s)

        #comparing data with metaswitch
        
        q = """
            select top 2000 m_id, accountid, directorynumber,allow from [MetaSwitchBarIDDPBX_dup] where status_comparing = 0
            """
        rows = db.cur.execute(q).fetchall()
        for r in rows:
            dn = r.directorynumber.strip()
            h= checking_data_match(dn, r.allow)
            print(h)
            if h == False:
                h =0

            if h == True:
                h =1
           
            if h:
                l.append(r.m_id)
        q = """
            update [MetaSwitchBarIDDPBX_dup] set status_comparing = ? where m_id = ?
            """
        for s in l:
            db.cur.execute(q, h, s)





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
