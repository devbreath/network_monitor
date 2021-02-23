from peewee import *

# db_name = "/home/speed_api/speed.db"
db_name = "speed.db"
database = SqliteDatabase(db_name)


class BaseModel(Model):
    class Meta:
        database = database
        only_save_dirty = True


class Measurements(BaseModel):
    source = FixedCharField(32, unique=False)
    date = DateField()
    time = TimeField()
    send = FloatField()
    receive = FloatField()
    localCPU = FloatField()
    remoteCPU = FloatField()

    class Meta:
        primary_key = CompositeKey('source', 'date', 'time')


class Latency(BaseModel):
    source = FixedCharField(32, unique=False)
    ip = CharField(15)
    dnsname = CharField(128)
    date = DateField()
    time = TimeField()
    minrtt = IntegerField()
    maxrtt = IntegerField()
    avgrtt = IntegerField()

    class Meta:
        primary_key = CompositeKey('source', 'ip', 'date', 'time')

    @staticmethod
    def fix_datestamp():
        # -- корректировка поля с датой и временем
        with database as d:
            d.execute_sql("update latency set date = substr(date,1,4) || '-' || substr(date,-4,2) || '-' || substr(date,-2,2) where length(date) = 8;")
            d.execute_sql("update latency set time = '00' || ':' || substr(time,-4,2) || ':' || substr(time,-2,2) where length(time) = 4;")
            d.execute_sql("update latency set time = '0' || substr(time,1,1) || ':' || substr(time,-4,2) || ':' || substr(time,-2,2) where length(time) = 5;")
            d.execute_sql("update latency set time = substr(time,1,2) || ':' || substr(time,-4,2) || ':' || substr(time,-2,2) where length(time) = 6;")


class LatencyView(BaseModel):
    class Meta:
        db_table = 'v_latency'
        primary_key = False

    @staticmethod
    def create_view_latency():
        # -- Считаем Jitter
        database.execute_sql('DROP VIEW IF EXISTS v_latency;')
        database.execute_sql("""
 CREATE VIEW v_latency AS
 select source, dnsname, date, time, avgrtt, ((abs(minrtt - avgrtt) + abs(maxrtt - avgrtt)) / 2) as jitter
   from latency
   group by source, dnsname, date, time;
    """)


    @staticmethod
    def create_view_latency_day():
        # -- Считаем Jitter за день
        database.execute_sql('DROP VIEW if exists v_latency_day;')
        database.execute_sql("""
 CREATE VIEW v_latency_day as
 select source, ip, dnsname, date, round(avg(avgrtt),2) as avgrtt, round(avg((abs(minrtt - avgrtt) + abs(maxrtt - avgrtt)) / 2),2) as jitter
   from latency
   group by source, dnsname, date;
""")


    @staticmethod
    def create_view_latency_anomality():
        # -- Смотрим аномалии в jitter'е
        database.execute_sql('drop view if exists v_latency_anomality;')
        database.execute_sql("""
 create view v_latency_anomality as
 select lnow.source as source, lnow.ip as ip, lnow.dnsname as dnsname,
   lnow.rtt as now_rtt, lweek.rtt as week_rtt, lmonth.rtt as month_rtt, lyear.rtt as year_rtt,
   lnow.jitter as now_jitter, lweek.jitter as week_jitter, lmonth.jitter as month_jitter, lyear.jitter as year_jitter
 from (select source, dnsname, ip, round(avg(avgrtt),2) as rtt, round(avg(jitter),2) as jitter from v_latency_day group by source, dnsname having max(date) ) as lnow
 join (select source, ip, round(avg(avgrtt),2) as rtt, round(avg(jitter),2) as jitter from v_latency_day WHERE date BETWEEN date('now', '-6 days') AND date('now', 'localtime') group by source, dnsname ) as lweek on lweek.source = lnow.source and lweek.ip = lnow.ip
 join (select source, ip, round(avg(avgrtt),2) as rtt, round(avg(jitter),2) as jitter from v_latency_day WHERE date BETWEEN date('now', '-31 days') AND date('now', 'localtime') group by source, dnsname ) as lmonth on lmonth.source = lnow.source and lmonth.ip = lnow.ip
 join (select source, ip, round(avg(avgrtt),2) as rtt, round(avg(jitter),2) as jitter from v_latency_day WHERE date BETWEEN date('now', '-31 days') AND date('now', 'localtime') group by source, dnsname ) as lyear on lyear.source = lnow.source and lyear.ip = lnow.ip
 group by lnow.source, lnow.dnsname;
""")


class Wireless(BaseModel):
    source = FixedCharField(32, unique=False)
    date = DateField()
    time = TimeField()
    ap = CharField(100)
    mac = CharField(18)
    lastip = FixedCharField(15)
    dnsname = CharField(128)
    rx = CharField(100)
    tx = CharField(100)
    uptime = CharField(20)
    lastact = CharField(11)
    signalstrength = CharField(100)
    snr = CharField(10)
    ccq = IntegerField()
    throughput = IntegerField()

    class Meta:
        primary_key = CompositeKey('source', 'ap', 'mac', 'date', 'time')
