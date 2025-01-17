import requests, logging, time, schedule
from logging.config import fileConfig
from dbhelper import initdb
from utils import geturltyped, geturluntyped

fileConfig('logging_createpbx.conf')

logger = logging.getLogger(__name__)
requests.packages.urllib3.disable_warnings()



def createdirectinwardcalling(dn, firstdn, name, accountid):
    b = False
    err = False

    try:
        u = geturltyped('api/bg/directinwardcalling')
        #u = ('https://billing.redtone.com/metaswitchapi1/api/pbx/directinwardcalling')
        print("==1==")
        print(u)
        logging.info(str(u))
        data = {
            'dn': dn,
            'firstdn': firstdn,
            'rangesize': 1,
            'name': name
        }
        logging.info(str(data))
        print("==2==")
        print(data)
        k = requests.post(u, json=data, verify=False)
        j = k.json()
        
        print("==3==")
        
        print(j)
        logging.info(str(j))

        if j.get('success') == 1:
            b = True

        elif j.get('error') == 2:
            err = True

    except Exception as e:
        logger.exception(str(e))

    #time.sleep(.200)

    return b, err



def createbg(dn, accountid, name, sippassword, allowidd, lcc3):
    b = False
    err = False

    try:

        u = geturltyped('api/bg')
        # data = {
        #     'dn': dn,
        #     'accountid': accountid,
        #     'name': name,
        #     'sipusername': dn,
        #     'sippassword': sippassword,
        #     'allowidd': allowidd,
        #     'lcc3':lcc3
        # }
        # #print("==data1==")
        #print(data)

        data = {
        
            'accountid': accountid,
            'name': name,
        
        }

        k = requests.post(u, json=data, verify=False)
        j = k.json()
        #print("==data2==")
        #print(j)
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
            select top 2000 a.m_id, a.accountid, a.directorynumber, a.sippassword, b.name, c.iddusagebar, a.lcc3 
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
            lcc3 = r.lcc3
            b, err = createpbx(dn, accountid, name, sippassword, allowidd, lcc3)
            
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
    schedule.every(1).minutes.do(job)
    while True:
        schedule.run_pending()
        time.sleep(2)
