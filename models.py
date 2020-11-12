# coding:utf-8
from src.database import db
from datetime import datetime
from src.util import ModelMixin, getScheduletime
from collections import defaultdict
import numpy as np


class Task(db.Model, ModelMixin):
    id = db.Column(db.Integer, primary_key=True)
    jobname = db.Column(db.String(255))#Jenkins Job Fullname
    release = db.Column(db.String(32))
    params = db.Column(db.Text)
    build_number = db.Column(db.Integer)
    building = db.Column(db.Boolean)
    url = db.Column(db.Text)
    username=db.Column(db.String(32))
    userid=db.Column(db.String(32))
    short_description=db.Column(db.String(32))
    result = db.Column(db.String(32))
    createtime = db.Column(db.DateTime, default=datetime.now)    
    updatetime = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    content = db.Column(db.Text)
    source = db.Column(db.Integer, default=0) # 0 xpit, 1 daily

    def createFromBuildInfo(self, jobname, buildNumber, info, paramsJSON):
        self.jobname = jobname
        self.build_number = buildNumber
        self.building = info["building"]
        self.url = info["url"]
        self.result = info["result"]
        self.username = info["username"]
        self.userid = info["userid"]
        self.release = info["release"]
        self.source = info["source"]
        self.params = paramsJSON
        db.session.add(self)
        db.session.commit()

    def updateFromBuildInfo(self, info):
        self.building = info["building"]
        # self.url = info["url"]
        self.result = info["result"]
        db.session.commit()

    def update(self):
        db.session.commit()


class TaskScheduler(db.Model, ModelMixin):
    id = db.Column(db.Integer, primary_key=True)
    enabled = db.Column(db.Boolean, default=True)
    scheduletime = db.Column(db.DateTime)
    total = db.Column(db.Integer)
    count = db.Column(db.Integer,default=0)
    weekdays = db.Column(db.Integer) # use `util.bits_from`
    jobname = db.Column(db.String(255))#Jenkins Job Fullname
    params = db.Column(db.Text)
    userid = db.Column(db.Integer, db.ForeignKey('user.id'))
    username = db.Column(db.String(32))
    release = db.Column(db.String(32))
    itcode = db.Column(db.String(32))
    source = db.Column(db.Integer, default=0) # 0 xpit, 1 daily, 2 pit
    createtime = db.Column(db.DateTime, default=datetime.now)    
    updatetime = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def createFromStartLater(self, jobname, info, paramsJSON):
        self.jobname = jobname
        self.scheduletime = info["scheduletime"]
        self.total = info["total"]
        self.weekdays = info["weekdays"]
        self.userid = info["userid"]
        self.source = info["source"]
        self.itcode = info["itcode"]
        self.username = info["username"]
        self.release = info["release"]
        self.params = paramsJSON
        db.session.add(self)
        db.session.commit()

    @classmethod
    def queryActiveSchedulers(cls):
        return db.session.query(cls).filter(cls.enabled==True, cls.scheduletime <= datetime.now(), cls.count < cls.total)

    def scheduleNext(self):
        self.count += 1
        self.scheduletime = getScheduletime(self.weekdays, dateobj=self.scheduletime)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()


class LxcaTask(db.Model, ModelMixin):
    id = db.Column(db.Integer, primary_key=True)
    params = db.Column(db.Text)
    jobuid = db.Column(db.String(32))
    status = db.Column(db.String(32))
    username=db.Column(db.String(32))
    userid=db.Column(db.String(32))
    hostuuid = db.Column(db.String(32))
    immip = db.Column(db.String(32))
    dhcp = db.Column(db.Boolean)
    createtime = db.Column(db.DateTime, default=datetime.now)
    updatetime = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    @classmethod
    def queryManagingTasks(cls):
        return db.session.query(cls).filter(cls.status.in_(("Done", "Created")))

    @classmethod
    def queryTaskHistory(cls):
        return db.session.query(cls).filter(cls.status != "Aborted").order_by(cls.updatetime.desc())

    @classmethod
    def isImmipCanManage(cls, immip):
        count = db.session.query(cls).filter(cls.immip==immip, cls.status.in_(("Running", "Created"))).count()
        return count == 0

    def createFromManage(self, jobuid, status, info, immip, dhcp, paramsJSON):
        self.params = paramsJSON
        self.jobuid = jobuid
        self.immip = immip
        self.dhcp = dhcp
        self.username = info["username"]
        self.userid = info["userid"]
        self.status = status
        db.session.add(self)
        db.session.commit()

    def createFromDeployOSImage(self, jobuid, info, paramsJSON):
        self.params = paramsJSON
        self.jobuid = jobuid
        self.username = info["username"]
        self.userid = info["userid"]
        self.status = "Running"
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

class StressTask(db.Model, ModelMixin):
    id = db.Column(db.Integer(), primary_key=True)
    build_number = db.Column(db.Integer)
    system = db.Column(db.String(32))
    release = db.Column(db.String(32))
    immip = db.Column(db.String(32))
    info = db.Column(db.Text())
    createtime = db.Column(db.DateTime, default=datetime.now)

    def create(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k,v)
        db.session.add(self)
        db.session.commit()

class StressWatchProcs(db.Model, ModelMixin):
    id = db.Column(db.Integer(), primary_key=True)
    up_secs = db.Column(db.Integer())
    pid = db.Column(db.Integer())
    rss_anon = db.Column(db.Integer())
    heap = db.Column(db.Integer())
    rss_anon_d = db.Column(db.Integer())
    heap_d = db.Column(db.Integer())
    process_name = db.Column(db.String(32))
    taskid = db.Column(db.Integer, db.ForeignKey('stress_task.id'))
    entry_taskid = db.Column(db.Integer, db.ForeignKey("task.id"))
    createtime = db.Column(db.DateTime, default=datetime.now)

    @classmethod
    def createFromRecords(cls, records):
        for r in records:
            db.session.add(cls(**r))
        db.session.commit()

    @classmethod
    def queryLastRecordByTaskId(cls, taskid):
        return db.session.query(cls).join(
            StressTask, StressTask.id==cls.taskid).filter(
            StressTask.id==taskid).order_by(cls.id.desc()).limit(1).first()
    
    @classmethod
    def getLastTaskId(cls):
        result = cls.query.join(Task).order_by(cls.id.desc()).first()
        return result.entry_taskid

    @classmethod
    def queryProcessGroup(cls, entry_taskid=None):
        if entry_taskid is None:
            entry_taskid = cls.getLastTaskId()
        res = defaultdict(list)
        for pid, pname, rss_anon in db.session.query(cls.pid, cls.process_name, cls.rss_anon).filter(cls.entry_taskid==int(entry_taskid)).distinct(cls.pid):
            res["%s-%s" % (pname,pid)].append(rss_anon)
        keys=list(res)
        keys.sort(key=lambda k: np.array(res[k]).std(), reverse=True)
        return keys
