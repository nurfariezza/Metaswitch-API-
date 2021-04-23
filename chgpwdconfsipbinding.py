import requests, logging, time, schedule
from logging.config import fileConfig
from requests.auth import HTTPBasicAuth
from dbhelper import initdb
from utils import geturltyped

fileConfig('logging_chgpwdconfsipbinding.conf')

logger = logging.getLogger(__name__)
requests.packages.urllib3.disable_warnings()

def chgpwd(name, sipusername, pwd):
    b = False

    try:
        u = geturltyped('api/configuredsipbinding/chgpwd')
        data = {
            'name': name,
            'sipusername': sipusername,
            'sippassword': pwd[:15]
        }
        k = requests.post(u, json=data, verify=False)
        j = k.json()
        if j.get('success') == 1:
            b = True

    except Exception as e:
        logger.exception(str(e))

    time.sleep(.200)

    return b

def job():
    db = None

    try:
        db = initdb()
        l = []
        q = """
            select top 2000 m_id, directorynumber, accountid, sippassword from metaswitchchgpwdconfsipb 
            where m_status = 0
            """
        rows = db.cur.execute(q).fetchall()
        for r in rows:
            dn = r.directorynumber.strip()
            b = chgpwd(r.accountid, dn, r.sippassword)
            if b:
                l.append(r.m_id)

        q = """
            update metaswitchchgpwdconfsipb set m_status = 1 where m_id = ?
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
        time.sleep(2)
