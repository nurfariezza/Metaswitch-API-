import requests, logging, time, schedule
from logging.config import fileConfig
from dbhelper import initdb
from utils import geturltyped

fileConfig('logging_updateportpbx.conf')

logger = logging.getLogger(__name__)
requests.packages.urllib3.disable_warnings()

def updateportpbx(callerid, mcaport, SIPPassword ):
    b = False

    try:
        print("==debug==" + callerid)
        #u = geturltyped('api/subs/{0}/'.format(callerid))
        u = geturltyped('api/subs/pbxchgmca')
        #u ='http://localhost:20167/api/subs/pbxchgmca'

        
        data = {
            'dn': callerid,
            'sippassword': SIPPassword,
            'mca': mcaport,
        }
        
        k = requests.post(u, json=data, verify=False)
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
            select top 1000 m_id, accountid, callerid, mcaport, SIPPassword from MetaSwitchUpdatePbxport where m_status = 0
            """
        rows = db.cur.execute(q).fetchall()
        for r in rows:
            callerid = r.callerid.strip()
            b = updateportpbx(callerid, r.mcaport, r.SIPPassword)
            if b:
                l.append(r.m_id)

        q = """
            update MetaSwitchUpdatePbxport set m_status = 1 where m_id = ?
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
