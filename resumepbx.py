import requests, logging, time, schedule
from logging.config import fileConfig
from requests.auth import HTTPBasicAuth
from dbhelper import initdb
from utils import geturltyped

fileConfig('logging_resumepbx.conf')

logger = logging.getLogger(__name__)
requests.packages.urllib3.disable_warnings()

def resumepbx(accountid, dn):
    b = False

    try:
        u = geturltyped('api/pbx/resume/{0}'.format(dn))
        k = requests.put(u, verify=False)
        j = k.json()
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
            select top 2000 m_id, accountid, directorynumber from metaswitchsuspendpbx where suspend = 0 and m_status = 0
            """
        rows = db.cur.execute(q).fetchall()
        for r in rows:
            dn = r.directorynumber.strip()
            b = resumepbx(r.accountid, dn)
            if b:
                l.append(r.m_id)

        q = """
            update metaswitchsuspendpbx set m_status = 1 where m_id = ?
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
