import logging, time, schedule
from logging.config import fileConfig
from dbhelper import initdb

fileConfig('logging_changeallowpstnsip.conf')

logger = logging.getLogger(__name__)

def job():
    db = None

    try:
        db = initdb()
        l = []
        q = """
            select top 2000 callerid from sipchangeallowpstn
            """
        rows = db.cur.execute(q).fetchall()
        for r in rows:
            l.append(r.callerid)

        q = """
            SET NOCOUNT ON
            declare 
              @return_value int,
              @ErrorMsg varchar(500)
            exec @return_value = spp_015ChangeAllowPSTN
              @CallerID = ?,
              @AllowPSTN = ?,
              @ErrorMsg = @ErrorMsg output
            select
              @ErrorMsg as N'ErrorMsg',
              @return_value as N'Ret'
            """

        qs = """
             delete from sipchangeallowpstn where callerid = ?
             """
        try:
            for s in l:
                db.cur.execute(q, s, 0)
                r = db.cur.fetchone()
                if r.Ret != 1:
                    if 'CANNOT FIND' not in r.ErrorMsg:
                        logger.exception('Failed to execute spp_015ChangeAllowPSTN {0}, Error: {1}'.format(s, r.ErrorMsg))

                    else:
                        db.cur.execute(qs, s)

                else:
                    db.cur.execute(qs, s)

        except:
            raise

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
