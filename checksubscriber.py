import requests
from requests.auth import HTTPBasicAuth
from dbhelper import initdb

requests.packages.urllib3.disable_warnings()

def showsubs(dn):
    try:
        u = 'https://billing.redtone.com/metaswitchapi1/api/subs/{0}'.format(dn)
        k = requests.get(u, verify=False)
        j = k.json()
        if j.get('success') == 1:
            print dn

    except Exception as e:
        print e.message

if __name__ == '__main__':
    db = None

    try:
        db = initdb()
        q = """
            select directorynumber from MetaSwitchCreateSubs where m_status = 0
            """
        rows = db.cur.execute(q).fetchall()
        for r in rows:
            showsubs(r.directorynumber.strip())

    except Exception as e:
        print e.message

    finally:
        if db is not None:
            db.dispose()
