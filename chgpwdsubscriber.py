import requests, logging, time, schedule
from logging.config import fileConfig
from requests.auth import HTTPBasicAuth
from dbhelper import initdb
from utils import geturltyped, geturluntyped

fileConfig('logging_chgpwdsubscriber.conf')

logger = logging.getLogger(__name__)
requests.packages.urllib3.disable_warnings()

def updatestatus(dn, action):
    b = False

    try:
        u = geturluntyped('api/subsstatus')
        data = {
            'dn': dn,
            'action': action
        }
        k = requests.put(u, json=data, verify=False)
        j = k.json()
        if j.get('success') == 1:
            b = True

    except Exception as e:
        logger.exception(str(e))

    return b

def chgpwd(accountid, dn, pwd):
    b = False
    err = False

    try:
        r = updatestatus(dn, 'disable')

        u = geturltyped('api/subs/chgpwd')
        data = {
            'dn': dn,
            'accountid': accountid,
            'sippassword': pwd[:15]
        }
        k = requests.post(u, json=data, verify=False)
        j = k.json()
        if j.get('success') == 1:
            b = True
            r = updatestatus(dn, 'enable')

        elif j.get('error') == 2:
            err = True

    except Exception as e:
        logger.exception(str(e))

    time.sleep(.200)

    return b, err

def job():
    db = None

    try:
        db = initdb()
        l = []
        le = []
        q = """
            select top 2000 m_id, directorynumber, accountid, sippassword from metaswitchchgpwdsubs 
            where m_status = 0
            """
        rows = db.cur.execute(q).fetchall()
        for r in rows:
            dn = r.directorynumber.strip()
            b, err = chgpwd(r.accountid, dn, r.sippassword)
            if b:
                l.append(r.m_id)

            if err:
                le.append(r.m_id)

        q = """
            update metaswitchchgpwdsubs set m_status = ? where m_id = ?
            """
        for s in l:
            db.cur.execute(q, 1, s)

        for s in le:
            db.cur.execute(q, 2, s)

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
