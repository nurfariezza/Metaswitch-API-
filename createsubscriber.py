import requests, logging, time, schedule
from logging.config import fileConfig
from dbhelper import initdb
from utils import geturluntyped

fileConfig('logging_createsubscriber.conf')

logger = logging.getLogger(__name__)
requests.packages.urllib3.disable_warnings()

def deletepbx(dn):
    b = False

    try:
        print("==pbx==" + dn)
        u = geturluntyped('api/pbx/{0}'.format(dn))
        k = requests.delete(u, verify=False)
        j = k.json()
        if j.get('success') == 1:
            b = True

    except Exception as e:
        logger.exception(str(e))

    #time.sleep(2)

    return b

def deletedirectinwardcalling(dn, firstdn):
    b = False

    try:
        print("==did==" + dn)
        u = geturluntyped('api/directinwardcalling')
        data = {
            'dn': dn,
            'firstdn': firstdn,
        }
        k = requests.post(u, json=data, verify=False)
        j = k.json()
        if j.get('success') == 1:
            b = True

    except Exception as e:
        logger.exception(str(e))

    #time.sleep(2)

    return b

def createsubs(dic):
    stat = 0

    try:
        #deletepbx(dic['dn'])
        #deletedirectinwardcalling(dic['dn'], '01548740057')
        u = 'https://billing.redtone.com/metaswitchapi1/api/subs'
        #u = 'http://localhost:20167/api/subs'
        data = {
            'dn': dic['dn'],
            'accountid': dic['accountid'],
            'name': dic['name'],
            'sippassword': dic['sippassword'],
            'callingpartynumber': dic['callingpartynumber'],
            'lcc3': dic['lcc3'],
            'allowidd': dic['allowidd']
        }
        
        k = requests.post(u, json=data, verify=False)
        j = k.json()
        print(j)
        if j.get('success') == 1:
            stat = 1

        elif j.get('error') == 2:
            stat = 2

        else:
            stat = 0

    except Exception as e:
        print(e)

    time.sleep(.200)

    return stat

def job():
    db = None

    try:
        db = initdb(autocommit=True)
        l = []
        lx = []
        q = """
            select top 2000 a.m_id, a.accountid, a.directorynumber, a.title, a.template, a.sippassword, a.name, a.lcc3, 
            a.callingparty, b.iddusagebar 
            from MetaSwitchCreateSubs a 
            inner join userdetailext b on a.accountid = b.accountid 
            where a.m_status = 0
            order by a.m_id desc
            """
        rows = db.cur.execute(q).fetchall()
        for r in rows:
            dic = {
                'dn': r.directorynumber,
                'accountid': r.accountid,
                'name': r.name,
                'sippassword': r.sippassword,
                'callingpartynumber': r.callingparty,
                'lcc3': r.lcc3,
                'allowidd': r.iddusagebar
            }
            print(dic)
            if r.sippassword is None:
                q = """
                    update MetaSwitchCreateSubs set m_status = 4 where m_id = ?
                    """
                db.cur.execute(q, r.m_id)
                continue

            dic['name'] = dic['name'][:32]
            dic['sippassword'] = dic['sippassword'][:15]

            stat = createsubs(dic)
            if stat == 2:
                print('{0} - {1}'.format(r.accountid, r.directorynumber))
                lx.append(r.m_id)

            elif stat == 1:
                l.append(r.m_id)

            q = """
                update MetaSwitchCreateSubs set m_status = 2 where m_id = ?
                """
            for s in l:
                db.cur.execute(q, s)

            q = """
                update MetaSwitchCreateSubs set m_status = 4 where m_id = ?
                """
            for s in lx:
                db.cur.execute(q, s)

    except Exception as e:
        print(e)

    finally:
        if db is not None:
            db.dispose()

if __name__ == '__main__':
    job()
    #schedule.every(1).minutes.do(job)
    #while True:
        #schedule.run_pending()
        #time.sleep(2)
