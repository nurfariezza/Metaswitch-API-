import requests, logging, time, schedule
from logging.config import fileConfig
from dbhelper import initdb
from utils import geturltyped, geturluntyped

fileConfig('logging_createpbx.conf')

logger = logging.getLogger(__name__)
requests.packages.urllib3.disable_warnings()

def getpbx(dn, accountid):
    accid = None
    num = None

    try:
        u = geturltyped('api/pbx/{0}'.format(dn))
        k = requests.get(u, verify=False)
        j = k.json()
        if j.get('success') == 1:
            d = j.get('data')
            accid = d.get('chargeNumberField')
            num = d.get('directoryNumberField')

    except Exception as e:
        logger.exception(str(e))
        raise

    return accid, num

def deletesubs(accountid, dn):
    b = False

    try:
        u = geturluntyped('api/subs/{0}'.format(dn))
        k = requests.delete(u, verify=False)
        j = k.json()
        if j.get('success') == 1:
            b = True

    except Exception as e:
        logger.exception(str(e))

    #time.sleep(2)

    return b

def createpbxlcc(dn):
    b = False

    try:
        u = geturltyped('api/pbx/lcc/{0}'.format(dn))
        k = requests.post(u, verify=False)
        j = k.json()
        if j.get('success') == 1:
            b = True

    except Exception as e:
        logger.exception(str(e))

    time.sleep(.200)

    return b

def createpbxcustinfo(dn, name):
    b = False

    try:
        u = geturltyped('api/pbx/cust')
        data = {
            'dn': dn,
            'name': name
        }
        k = requests.post(u, json=data, verify=False)
        j = k.json()
        if j.get('success') == 1:
            b = True

    except Exception as e:
        logger.exception(str(e))

    time.sleep(.200)

    return b

def createdirectinwardcalling(dn, firstdn, name, accountid):
    b = False
    err = False

    try:
        #deletesubs(accountid, firstdn)
        #u = geturltyped('api/pbx/directinwardcalling')
        #u = ('https://billing.redtone.com/metaswitchapi1/api/pbx/directinwardcalling')
        u = 'http://localhost:20167/api/pbx/directinwardcalling'

        data = {
            'dn': dn,
            'firstdn': firstdn,
            'rangesize': 1,
            'name': name
        }
        
        k = requests.post(u, json=data, verify=False)
        j = k.json()
        print(j)
        if j.get('success') == 1:
            b = True

        elif j.get('error') == 2:
            err = True

    except Exception as e:
        logger.exception(str(e))

    time.sleep(.200)

    return b, err

def createpbxlines(dn, accountid):
    b = False

    try:
        u = geturltyped('api/pbx/lines')
        data = {
            'configuredsipbinding': accountid,
            'dn': dn
        }
        k = requests.post(u, json=data, verify=False)
        j = k.json()
        if j.get('success') == 1:
            b = True

    except Exception as e:
        logger.exception(str(e))

    time.sleep(.200)

    return b

def createconfiguredsipbinding(dn, accountid, sippassword):
    b = False

    try:
        u = geturltyped('api/configuredsipbinding')
        data = {
            'name': accountid,
            'sipusername': dn,
            'sippassword': sippassword
        }
        k = requests.post(u, json=data, verify=False)
        j = k.json()
        if j.get('success') == 1:
            b = True

    except Exception as e:
        logger.exception(str(e))

    time.sleep(.200)

    return b

def createpbx(dn, accountid, name, sippassword, allowidd):
    b = False
    err = False

    try:
        # accid, num = getpbx(dn, accountid)
        # if accid is None and num is None:
        #     deletesubs(accountid, dn)

        # elif accid != accountid and num != dn:
        #     deletesubs(accountid, dn)

        # if accid == accountid and num == dn:
        #     b = True
        #     return b, err

        u = geturltyped('api/pbx')
        #u = 'http://localhost:20167/api/pbx'
        print(u)
        data = {
            'dn': dn,
            'accountid': accountid,
            'name': name,
            'sipusername': dn,
            'sippassword': sippassword,
            'allowidd': allowidd
        }
        k = requests.post(u, json=data, verify=False)
        j = k.json()
        print(data)
        if j.get('success') == 1:
            b = True

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
            select top 2000 a.m_id, a.accountid, a.directorynumber, a.sippassword, b.name, c.iddusagebar 
            from metaswitchcreatepbx a 
            inner join userdetail b on a.accountid = b.accountid 
            inner join userdetailext c on b.accountid = c.accountid 
            where a.m_status = 0 and 
            a.directorynumber not in (
                select directorynumber from metaswitchremovesubs where m_status = 0
            )
            """
        rows = db.cur.execute(q).fetchall()
        for r in rows:
            if r.sippassword is None:
                continue

            dn = r.directorynumber.strip()
            name = r.name
            accountid = r.accountid
            sippassword = r.sippassword[:15]
            allowidd = r.iddusagebar
            b, err = createpbx(dn, accountid, name, sippassword, allowidd)
            
            if b:
                l.append(r.m_id)

            if err:
                le.append(r.m_id)

        q = """
            update metaswitchcreatepbx set m_status = ? where m_id = ?
            """
        for s in l:
            db.cur.execute(q, 1, s)

        for s in le:
            db.cur.execute(q, 2, s)

        l = []
        q = """
            select top 2000 a.m_id, a.directorynumber, a.firstdn, c.accountid, c.name 
            from metaswitchcreatepbxdirectinwardcalling a 
            inner join authentication b on a.directorynumber = b.callerid 
            inner join userdetail c on b.accountid = c.accountid 
            where a.m_status = 0 and 
            a.directorynumber not in (
               select directorynumber from metaswitchremovesubs where m_status = 0
            )
            """
        rows = db.cur.execute(q).fetchall()
        for r in rows:
            dn = r.firstdn.strip()
            firstdn = r.directorynumber.strip()
            accountid = r.accountid
            name = r.name
            b = createdirectinwardcalling(dn, firstdn, name, accountid)

            if b:
                l.append(r.m_id)

        q = """
            update metaswitchcreatepbxdirectinwardcalling set m_status = 1 where m_id = ?
            """
        for s in l:
            db.cur.execute(q, s)

    except Exception as e:
        logger.exception(str(e))

    finally:
        if db is not None:
            db.dispose()

if __name__ == '__main__':
    job()
    #schedule.every(1).minutes.do(job)
    #while True:
        #schedule.run_pending()
        #time.sleep(2)
