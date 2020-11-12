from flask import render_template, url_for, jsonify, request, session, Blueprint, abort
from flask_login import login_required, current_user
from flask import current_app
from src.util import access_required
from flask.views import MethodView
from jenkins_backend import getServer
from werkzeug.utils import secure_filename
from src.rpc import client as rpc_clt
from src.xpit.models import Task, LxcaTask, TaskScheduler, StressTask, StressWatchProcs
from src.xpit.tasks import poll_manage_status
from src.admin.models import Message, Group
from src.service.lxca import get_lxca, LXCAMixin
from datetime import timedelta
import json
import src.util as util
import requests
import logging
import config
import re
import collections
import pandas as pd


app = Blueprint("xpit", __name__)

def echo_message(event, result="SUCCESS"):
    Message().create({"userid": current_user.id, "event": event, "result":result})

class UtilMixin(object):
    def get_entry_url(self, jobname, buildno):
        if r"/" in jobname:
            folder, subjobname = jobname.split("/")
            url = config.JENKINS_URL + \
                "/blue/rest/organizations/jenkins/pipelines/{folder}/pipelines/{subjobname}/runs/{buildno}/nodes/?limit=10000".format(**locals())
        else:
            url = config.JENKINS_URL + \
                "/blue/rest/organizations/jenkins/pipelines/{jobname}/runs/{buildno}/nodes/?limit=10000".format(**locals())
        return url

    def getParamsFromJSON(self, jsonstr, jobname):
        p, release, suffix = jobname.split('/')[-1].split('_', 2)
        if not jsonstr:return []
        res = collections.OrderedDict()
        res["product"] = p
        res["release"] = release
        jd = collections.OrderedDict(json.loads(jsonstr))
        systemNames=[]
        systems = []
        testItems = [] 
        res["sender"] = jd["SENDER"]
        res["receiver"] = jd["RECEIVER"]
        if suffix == "daily" or p =='pit':
            res["source"] = 'pit' if p == 'pit' else 'daily'
            for k, v in jd.items():
                if (k.endswith("_XTEST") or k.endswith("_UTEST"))and v:
                    testItems.append(k[:~5])
                elif k.endswith("_SYS") and v:
                    systemNames.append(k[:~3])
        elif suffix == "mem":
            res["source"] = "stress"
            for k, v in jd.items():
                if k.endswith("_MEM") and v:
                    testItems.append(k[:~3])
                elif k.endswith("_SYS") and v:
                    systemNames.append(k[:~3])
        else:
            res["source"] = "xpit"
            for k, v in jd.items():
                if k.endswith("_LOOP") and int(v) > 0:
                    if "loop" not in res: res["loop"] = v
                    testItems.append(k[:~4])
                elif k.endswith("_SYS") and v:
                    systemNames.append(k[:~3])
        if testItems: res["testItems"] = testItems
        configdict = {}
        if "BUILD_CFG" in jd:
            configdict = json.loads(jd["BUILD_CFG"])
        for name in systemNames:
            systems.append({"name":name, "builds": configdict.get(name, [])})
        if systems: res["systems"] = systems
        return res


    def setExternalTaskscheduler(self, taskdict):
        taskdict["weekdays"] = [ {"id": wid, "text": config.weekdays[wid]} for wid in util.get_weekdays_from_bits(taskdict["weekdays"])]
        taskdict["clock"] = "%02d:%02d" % (taskdict["scheduletime"].hour,taskdict["scheduletime"].minute)


class ApiXpitJobs(MethodView):

    def get(self):
        jobs = rpc_clt.get_cache_by_key("jobs")["xpit"]
        # xpit_19a_constantine_207_entry
        options = {'releaseOptions':[], "p": "xpit"}
        for job in jobs:
            release = job['name'].split('_', 2)[1]
            sysOpts=[]
            testItems=[]
            for param in job['params']:
                if param['name'].endswith('_SYS'):
                    sysOpts.append(param['name'][:~3])
                elif param['name'].endswith('_LOOP'):
                    testItems.append(param['name'][:~4])
            options["releaseOptions"].append({"text": release, "id": release, "systemOptions": sysOpts, "testItems": testItems})
        # sorting
        # alph first sort by asc
        # digit second sort by desc
        digs=[]
        alps=[]
        for opt in options['releaseOptions']:
            if opt['id'][0].isdigit():
                digs.append(opt)
            else:
                alps.append(opt)
        options['releaseOptions'] = sorted(alps)+ sorted(digs, reverse=True)
        return jsonify(options)
    # job = server.get_job("FW_WebUI_test")
    # return jsonify([x for x in job.get_params()])


class ApiDailyJobs(MethodView):

    def get(self):
        jobs = rpc_clt.get_cache_by_key("jobs")["daily"]
        # xpit_19a_constantine_207_entry
        options = {'releaseOptions':[]}
        for job in jobs:
            product, release = job['name'].split('_', 2)[:2]
            xtestItems=[]
            utestItems=[]
            sysOpts=[]
            prefix = job["name"][:~5]
            for param in job['params']:
                if param['name'].endswith('_XTEST'):
                    xtestItems.append(param['name'][:~5])
                elif param['name'].endswith('_UTEST'):
                    utestItems.append(param['name'][:~5])
                elif param['name'].endswith('_SYS'):
                    sysOpts.append(param['name'][:~3])

            options["releaseOptions"].append({
                "text": prefix, "id": prefix,
                "testItems": {'xcc': xtestItems, 'uefi': utestItems},
                "systemOptions": sysOpts
            })
        # sorting
        # alph first sort by asc
        # digit second sort by desc
        digs=[]
        alps=[]
        for opt in options['releaseOptions']:
            if opt['id'][0].isdigit():
                digs.append(opt)
            else:
                alps.append(opt)
        options['releaseOptions'] = sorted(alps)+ sorted(digs, reverse=True)
        return jsonify(options)
    # job = server.get_job("FW_WebUI_test")
    # return jsonify([x for x in job.get_params()])


class ApiPitJobs(MethodView):

    def get(self):
        jobs = rpc_clt.get_cache_by_key("jobs")["pit"]
        # xpit_19a_constantine_207_entry
        options = {'releaseOptions':[]}
        for job in jobs:
            product, release = job['name'].split('_', 2)[:2]
            xtestItems=[]
            utestItems=[]
            sysOpts=[]
            prefix = job["name"][:~5]
            for param in job['params']:
                if param['name'].endswith('_XTEST'):
                    xtestItems.append(param['name'][:~5])
                elif param['name'].endswith('_UTEST'):
                    utestItems.append(param['name'][:~5])
                elif param['name'].endswith('_SYS'):
                    sysOpts.append(param['name'][:~3])

            options["releaseOptions"].append({
                "text": prefix, "id": prefix,
                "testItems": {'xcc': xtestItems, 'uefi': utestItems},
                "systemOptions": sysOpts
            })
        # sorting
        # alph first sort by asc
        # digit second sort by desc
        digs=[]
        alps=[]
        for opt in options['releaseOptions']:
            if opt['id'][0].isdigit():
                digs.append(opt)
            else:
                alps.append(opt)
        options['releaseOptions'] = sorted(alps)+ sorted(digs, reverse=True)
        return jsonify(options)
    # job = server.get_job("FW_WebUI_test")
    # return jsonify([x for x in job.get_params()])


class ApiStressJobs(MethodView):

    def get(self):
        jobs = rpc_clt.get_cache_by_key("jobs")["stress"]
        options = {'releaseOptions':[]}
        for job in jobs:
            product, release = job['name'].split('_', 2)[:2]
            xtestItems=[]
            utestItems=[]
            stressItems=[]
            sysOpts=[]
            prefix = job["name"][:~3]
            for param in job['params']:
                if param['name'].endswith('_XTEST'):
                    xtestItems.append(param['name'][:~5])
                elif param['name'].endswith('_UTEST'):
                    utestItems.append(param['name'][:~5])
                elif param['name'].endswith('_SYS'):
                    sysOpts.append(param['name'][:~3])
                elif param["name"].endswith("_MEM"):
                    stressItems.append(param["name"][:~3])

            options["releaseOptions"].append({
                "text": prefix, "id": prefix,
                "testItems": stressItems,
                "systemOptions": sysOpts
            })
        # sorting
        # alph first sort by asc
        # digit second sort by desc
        digs=[]
        alps=[]
        for opt in options['releaseOptions']:
            if opt['id'][0].isdigit():
                digs.append(opt)
            else:
                alps.append(opt)
        options['releaseOptions'] = sorted(alps)+ sorted(digs, reverse=True)
        return jsonify(options)
    # job = server.get_job("FW_WebUI_test")
    # return jsonify([x for x in job.get_params()])


def allowed_file(filename):
    ALLOWED_EXTENSIONS = set(['uxz', 'upd', 'xml'])
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=["POST"])
def upload_file():
    params = {
    "release": util.args_get("release", required=True),
    "system": util.args_get("system", required=True),
    "product": util.args_get("product", required=True),
    }
    # check if the post request has the file part
    if 'file' not in request.files:
        abort(404)
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '': abort(404)
    res={"success": False}
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        resp=requests.get("http://%s/p/cf/item/common" % request.headers["Host"])
        nexusInfo = resp.json()["nexus"]
        params['filename']=filename
        params["ip"] = nexusInfo["ip"]
        url = (
            "http://{ip}/repository/xpit_temp_build/"
            "{release}/{system}/{product}/{filename}"
            ).format(**params)
        # raise Exception(url)
        resp=requests.put(url, data=file, auth=(nexusInfo["username"], nexusInfo["password"]))
        if resp.status_code == 201:
            res={"success": True, "url": url, "status": resp.status_code}
    return jsonify(res)


class ApiTaskTrigger(MethodView):
    decorators = [login_required]
    def post(self):
        jd = request.get_json()
        self.source = int(jd.get("source", 0))
        if not jd:
            jd = json.loads(request.get_data())
        jobname = self.get_job_fullname(jd)
        # post data={}
        if self.source == 0:
            params = self.handle_xpit_params(jd)
        elif self.source == 1:
            params = self.handle_daily_params(jd)
        elif self.source == 2:
            params = self.handle_pit_params(jd)
        elif self.source == 3:
            params = self.handle_stress_params(jd)
        else:
            abort(404)
        res = {"success": True}
        commoninfo = {}
        commoninfo['username'] = session["displayName"]
        commoninfo['userid'] = session["mail"].split('@')[0]
        commoninfo["release"] = jd["release"]
        commoninfo["source"] = self.source

        if jd.get("schedule"):
            scheduleData = jd["schedule"]
            # fields: clock 11:11, total 1, weekdays[{"id":0, "text": "Sun"}]
            weekdays = util.weekdaysToInteger(w["id"] for w in scheduleData["weekdays"])
            tser = TaskScheduler()
            info = {}
            info["weekdays"] = weekdays
            info["scheduletime"] = util.getScheduletime(weekdays, scheduleData["clock"])
            info["total"] = scheduleData["total"]
            info["userid"] = current_user.id
            info["itcode"] = commoninfo["userid"]
            info["username"] = commoninfo["username"]
            info["source"] = commoninfo["source"]
            info["release"] = commoninfo["release"]
            tser.createFromStartLater(jobname, info, json.dumps(params.items()))
            echo_message("Created Task Scheduler: %s" % jobname)
        else:
            server=getServer()
            buildNumber, msg = server.buildJob(jobname, params)
            if buildNumber < 0:
                res = {"success": False, "error": msg}
            else:
                buildInfo = server.get_build_info(jobname, buildNumber)
                buildInfo.update(commoninfo)
                task = Task()
                task.createFromBuildInfo(jobname, buildNumber, buildInfo, json.dumps(params.items()))
                echo_message("Trigger Task: %s(#%s)" % (jobname, buildNumber))
        return jsonify(res)

    def get_job_fullname(self, jd):
        key = {0:"xpit", 1:"daily", 2: "pit", 3: "stress"}[self.source]
        jobs = rpc_clt.get_cache_by_key("jobs")[key]
        for job in jobs:
            if self.source == 0 and job['name']=="{p}_{release}_entry".format(**jd):
                return job['fullname']
            if self.source == 1 and job['name']=="{release}_daily".format(**jd):
                return job['fullname']
            if self.source == 2 and job['name']=="{release}_entry".format(**jd):
                return job['fullname']
            if self.source == 3 and job['name']=="{release}_mem".format(**jd):
                return job['fullname']

    def getValidBuild(self, system):
        # oss, daily, files
        res=[]
        for b in system["builds"]:
            if b["buildtype"] == "oss" and b["ossid"].strip():
                res.append(b)
            elif b["buildtype"] == "daily":
                res.append(b)
            elif b["buildtype"] == "files" and b["files"]:
                res.append(b)
        return res

    def get_group_receivers(self, group):
        sender = session["mail"]
        if not group:return sender
        mail_pattern = re.compile(r'[0-9a-zA-z]+@qq.com')
        mails = mail_pattern.findall(group.members)
        return ','.join(set([sender] + mails))

    def handle_pit_params(self, jd):
        res=collections.OrderedDict()
        params=jd["params"]
        jobs = rpc_clt.get_cache_by_key("jobs")["pit"]
        # handle systems
        buildInfo = {}
        for system in params['systems']:
            res['%s_SYS' % system['name']]=True
            vbuilds = self.getValidBuild(system)
            if vbuilds:
                buildInfo[system["name"]] = vbuilds

        if buildInfo:
            res["BUILD_CFG"] = json.dumps(buildInfo)


        group = Group.query.get_or_404(jd["groupId"])
        res['RECEIVER'] = self.get_group_receivers(group)
        res['SENDER'] = session["mail"]

        # handle testItems
        xccTestItemSet = set(params["testItems"]['xcc'])
        uefiTestItemSet = set(params["testItems"]['uefi'])
        # uefi test endswith 'UTEST'
        # xcc test endswith 'XTEST'
        # xpit_19a_constantine_207_entry
        target=None
        for job in jobs:
            if job['name'].endswith('_entry') and job["name"].startswith("pit") and job['name'][:~5] == jd["release"]:
                target=job
                break
        for param in target['params']:
            pname = param['name']
            nameset = { system['name'] for system in params['systems']}
            if pname.endswith("_SYS") and pname[:~3] not in nameset:
                res[pname] = False
            if pname.endswith("_UTEST"):
                res[pname] = pname[:~5] in uefiTestItemSet
            elif pname.endswith("_XTEST"):
                res[pname] = pname[:~5] in xccTestItemSet
            if pname[:~5].endswith("Loops"):
                # PowerCycleLoops_XTEST
                k=pname[:~5]
                if k in params["loops"]:
                    res[pname] = int(params["loops"][k])
                else:
                    res.pop(pname)
        return res

    def handle_daily_params(self, jd):
        res=collections.OrderedDict()
        params=jd["params"]
        jobs = rpc_clt.get_cache_by_key("jobs")["daily"]
        # handle systems
        buildInfo = {}
        for system in params['systems']:
            res['%s_SYS' % system['name']]=True
            vbuilds = self.getValidBuild(system)
            if vbuilds:
                buildInfo[system["name"]] = vbuilds

        if buildInfo:
            res["BUILD_CFG"] = json.dumps(buildInfo)


        group = Group.query.get_or_404(jd["groupId"])
        res['RECEIVER'] = self.get_group_receivers(group)
        res['SENDER'] = session["mail"]

        # handle testItems
        xccTestItemSet = set(params["testItems"]['xcc'])
        uefiTestItemSet = set(params["testItems"]['uefi'])
        # uefi test endswith 'UTEST'
        # xcc test endswith 'XTEST'
        # xpit_19a_constantine_207_entry
        target=None
        for job in jobs:
            if job['name'].endswith('_daily') and job['name'][:~5] == jd["release"]:
                target=job
                break
        for param in target['params']:
            pname = param['name']
            nameset = { system['name'] for system in params['systems']}
            if pname.endswith("_SYS") and pname[:~3] not in nameset:
                res[pname] = False
            if pname.endswith("_UTEST"):
                res[pname] = pname[:~5] in uefiTestItemSet
            elif pname.endswith("_XTEST"):
                res[pname] = pname[:~5] in xccTestItemSet
        return res

    def handle_xpit_params(self, jd):
        res=collections.OrderedDict()
        params=jd["params"]
        jobs = rpc_clt.get_cache_by_key("jobs")["xpit"]
        # handle systems
        buildInfo = {}
        for system in params['systems']:
            res['%s_SYS' % system['name']]=True
            vbuilds = self.getValidBuild(system)
            if vbuilds:
                buildInfo[system["name"]] = vbuilds

        if buildInfo:
            res["BUILD_CFG"] = json.dumps(buildInfo)
        # todo: upload, oss
        #
        group = Group.query.get_or_404(jd["groupId"])
        res['RECEIVER'] = self.get_group_receivers(group)
        res['SENDER'] = session["mail"]
        # raise Exception(res)
        #
        if "loop" in params:
            testItemSet = set(params["testItems"])
            # xpit_19a_constantine_207_entry
            target=None
            for job in jobs:
                product, release, _ = job['name'].split('_', 2)
                if release == jd['release'] and product == jd['p']:
                    target=job
                    break
            for param in target['params']:
                pname = param['name']
                nameset = { system['name'] for system in params['systems']}
                if pname.endswith("_SYS") and pname[:~3] not in nameset:
                    res[pname] = False
                if(pname.endswith("_LOOP")):
                    res[pname] = params['loop'] if pname[:~4] in testItemSet else 0
        return res

    def handle_stress_params(self, jd):
        res=collections.OrderedDict()
        params=jd["params"]
        jobs = rpc_clt.get_cache_by_key("jobs")["stress"]
        # handle systems
        buildInfo = {}
        for system in params['systems']:
            res['%s_SYS' % system['name']]=True
            vbuilds = self.getValidBuild(system)
            if vbuilds:
                buildInfo[system["name"]] = vbuilds

        if buildInfo:
            res["BUILD_CFG"] = json.dumps(buildInfo)
        # todo: upload, oss
        #
        group = Group.query.get_or_404(jd["groupId"])
        res['RECEIVER'] = self.get_group_receivers(group)
        res['SENDER'] = session["mail"]
        # raise Exception(res)
        res["Hours"] = params["hours"]
        # if "loop" in params:
        testItemSet = set(params["testItems"])
        # xpit_19a_constantine_207_entry
        target=None
        for job in jobs:
            release, product = job['name'].rsplit('_', 1)
            if release == jd['release'] and product == "mem":
                target=job
                break
        for param in target['params']:
            pname = param['name']
            nameset = { system['name'] for system in params['systems']}
            if pname.endswith("_SYS") and pname[:~3] not in nameset:
                res[pname] = False
            if pname.endswith("_MEM"):
                res[pname] = pname[:~3] in testItemSet
        return res

class ApiTaskDetail(MethodView, UtilMixin):
    decorators = [login_required]

    def getDetailUrl(self, task, params):
        # /blue/rest/organizations/jenkins/pipelines/xPITCustomization/pipelines/xpit_m1_sr950_128/runs/76/
        # /blue/rest/organizations/jenkins/pipelines/xcc_19b_daily/runs/518/
        systems = params.get("systems", [])
        resp = requests.get(self.get_entry_url(task.jobname, task.build_number))
        res = {}
        # if task.source == 0:
        for node in resp.json():
            actions = node["actions"]
            if actions:
                href = actions[0]["link"]["href"]
                frag = [x for x in href.split('/') if x.strip()]
                folder = frag[~4 if href.count("pipelines") == 2 else ~2]
                subjobname, buildno = frag[~2], frag[~0]
                full_jobname = "{folder}%2F{subjobname}".format(**locals())
                nodename = 'n/a'
                for syst in systems:
                    if node["displayName"].endswith(syst['name'].lower()) or \
                        node["displayName"].lower() == syst['name'].lower():
                        nodename = syst['name']
                        break
                res[nodename] = config.JENKINS_URL + "/blue/organizations/jenkins/{full_jobname}/detail/{subjobname}/{buildno}/pipeline".format(**locals())
        # else:
        #     full_jobname, subjobname, buildno = task.jobname, task.jobname, task.build_number
        #     res["daily"] = config.JENKINS_URL + "/blue/organizations/jenkins/{full_jobname}/detail/{subjobname}/{buildno}/pipeline".format(**locals())
        return res

    def get(self, id):

        task = Task.query.get(id)

        res = {"success": False}
        if task:
            duration = task.updatetime - task.createtime
            taskdict = task.to_dict()
            taskdict["duration"] = duration.seconds
            taskdict["params"] = self.getParamsFromJSON(taskdict["params"], task.jobname)
            taskdict["urls"] = self.getDetailUrl(task, taskdict["params"])
            res = {"success": True, "task": taskdict}
        return jsonify(res)

    def post(self, id):
        task = Task.query.get(id)
        res = {"success": False}
        if task:
            jd = request.get_json()
            if jd["action"] == "stop":
                jobname,buildNumber=task.jobname, task.build_number
                server = getServer()
                server.stop_build(jobname, buildNumber)
                task.updateFromBuildInfo(dict(building=False, result="ABORTED"))
                echo_message("Stop Task: %s(#%s)" % (jobname, buildNumber))
                res={"success": True}
        return jsonify(res)


class ApiTask(MethodView, UtilMixin):

    # decorators=[util.request_remote]

    def get_systems(self, task):
        res=[]
        if task["params"]:
            jd = collections.OrderedDict(json.loads(task["params"]))
            for k in jd:
                if k.endswith('_SYS') and jd[k]:
                    res.append(k[:~3])
        return res

    def get(self):
        # task history arrange by release 
        # group by release
        source = util.args_get("source", 0)
        tasklist=[]
        for task in Task.query.filter_by(source=source).order_by(Task.updatetime.desc()):
            duration = task.updatetime - task.createtime
            taskdict = task.to_dict()
            taskdict["duration"] = duration.seconds
            tasklist.append(taskdict)
        temp=collections.OrderedDict()
        for t in tasklist:
            t['systems']=self.get_systems(t)
            t["params"]=self.getParamsFromJSON(t["params"],t["jobname"])
            # if t['systems']: t['building']=True
            t_release = t["release"]
            t.pop("content")
            if t_release in temp:
                temp[t_release].append(t)
            else:
                temp[t_release] = [t]
        data = []
        for release, tasks in temp.items():
            one = {"release": release, "tasks": tasks}
            data.append(one)
        return jsonify(data)


class ApiTaskStages(MethodView, UtilMixin):
    def get(self):
        '''
        How to Get Build Stages Info?
        Use API Blueocean Provided
        steps:
        1. concat url
        http://qq.com:8080/jenkins/blue/rest/organizations/jenkins/pipelines/xPITCustomization/pipelines/xpit_m1_sr950_128/runs/76/
        '''
        # blue/rest/organizations/jenkins/pipelines/xPITCustomization/pipelines/xpit_customization_entry/runs/80/nodes/?limit=10000
        jobname = util.args_get("jobname", required=True)
        buildno = util.args_get("buildno", required=True)
        source = util.args_get("source", 0, type=int)
        # source = 0
        resp = requests.get(self.get_entry_url(jobname, buildno))
        res = []
        task = Task.query.filter_by(jobname=jobname, build_number=buildno).first()
        if task:
            params = self.getParamsFromJSON(task.params, task.jobname)
            systems = params.get("systems", [])
            for node in resp.json():
                actions = node["actions"]
                if actions:
                    act = actions[0]
                    resp = requests.get(config.JENKINS_URL + act["link"]["href"] + 'nodes')
                    nodename = 'n/a'
                    for syst in systems:
                        if node["displayName"].endswith(syst['name'].lower()) or \
                            node["displayName"].lower() == syst['name'].lower():
                            nodename = syst['name']
                            break
                    res.append({"displayName": nodename, "nodes": resp.json()})
        return jsonify(res)


class ApiTaskReport(MethodView):
    def post(self):
        jd = request.get_json()
        task = Task.query.filter_by(jobname=jd["jobname"], build_number=jd["buildno"]).first()
        res = {"success": False}
        if task and not task.content:
            task.content = jd["content"]
            task.update()
            res = {"success": True}
        return jsonify(res)

    def get(self):
        task = Task.query.get(util.args_get("id", required=True))
        if not task or not task.content:return ''
        return task.content


class ApiTaskschedulerList(MethodView, UtilMixin):

    def get(self):
        source = util.args_get("source", type=int)
        res = []
        for task in TaskScheduler.query.filter_by(source=source):
            taskdict = task.to_dict()
            taskdict["params"] = self.getParamsFromJSON(taskdict["params"], task.jobname)
            self.setExternalTaskscheduler(taskdict)
            res.append(taskdict)
        return jsonify(res)

class ApiTaskscheduler(MethodView, UtilMixin):
    decorators = [login_required]

    def get(self, sid):
        task = TaskScheduler.query.get_or_404(sid)
        taskdict = task.to_dict()
        taskdict["params"] = self.getParamsFromJSON(taskdict["params"], task.jobname)
        self.setExternalTaskscheduler(taskdict)
        return jsonify(taskdict)

    def delete(self, sid):
        task=TaskScheduler.query.get_or_404(sid)
        task.delete()
        echo_message("Deleted Task Scheduler: %s(#%s)" % (task.jobname, sid))
        res = {"success": True}
        return jsonify(res)

    def patch(self, sid):
        task = TaskScheduler.query.get_or_404(sid)
        # properties of scheduler can be modified includes:
        # enabled, total, clock -> scheduletime, weekdays
        scheduleData = request.get_json()
        weekdays = util.weekdaysToInteger(w["id"] for w in scheduleData["weekdays"])
        if weekdays == 0:
            abort(404)
        task.weekdays = weekdays
        task.enabled = scheduleData.get("enabled", task.enabled)
        if scheduleData.get("total", -1) < task.count:
            abort(403)
        task.total = scheduleData["total"]
        task.scheduletime = util.getScheduletime(weekdays, scheduleData["clock"])
        task.update()
        echo_message("Updated Task Scheduler: %s(#%s)" % (task.jobname, task.id))

        taskdict = task.to_dict()
        taskdict["params"] = self.getParamsFromJSON(taskdict["params"], task.jobname)
        self.setExternalTaskscheduler(taskdict)

        return jsonify(taskdict)


class ApiLxcaOptions(MethodView):

    def get(self):
        return 


class ApiLxcaDeployOSImage(MethodView):
    decorators = [login_required]

    def post(self):
        jd = request.get_json()
        res = {}
        if 'ip' not in jd or 'user' not in jd or 'pw' not in jd:
            abort(404)
        if not LxcaTask.isImmipCanManage(jd["ip"]):
            res["warning"] = "Host of ip %s is now under managing by lxca." % jd["ip"]
            return jsonify(res)
        manage_handler = dict(jd, force=True)
        with get_lxca(jd.get("dhcp")) as api:
            hostPlatforms = api.get_hostPlatforms()
            host = None
            # readyCheck:accessState 
            # The access state must be online "Online" or "unSupported" 
            # to deploy an operating system on the host platform
            for item in hostPlatforms['items']:
                if item["immIpAddress"] == jd["ip"]:
                    host = item
                    break
            status, jobuid = "Done", None
            if host is None or host["readyCheck"]["accessState"] not in {"Online","unSupported"}:
                # host is not managed
                try:
                    res["jobId"] = api.do_manage(manage_handler)
                except Exception as e:
                    res['error'] = e.message
                    return jsonify(res)
                else:
                    status, jobuid = "Created", res["jobId"]
            # else:
            #     res["warning"] = "Host of ip %s Already Managed by lxca" % jd["ip"]
            # res = api.delopy_os_image(jd["uuid"], jd["image"], jd["os_ip"], jd["gateway"], jd["subnetMask"])
            # if "jobId" in res:
            # jobId = res["jobId"]
            # res2 = api.get_set_tasks({"jobUID": jobId})
            data={"immip": jd["ip"]}
            for k in ["image", "os_ip", "gateway", "subnetMask"]:
                if k not in jd:
                    return jsonify({"error": "missing key: %s" % k})
                data[k] = jd[k]

            info = {}
            info['username'] = session["displayName"]
            info['userid'] = session["mail"].split('@')[0]
            task = LxcaTask()
            task.createFromManage(jobuid, status, info, jd["ip"], jd.get("dhcp", False), json.dumps(data))
            # task.createFromDeployOSImage(jobId, info, json.dumps(jd))
            if jobuid:
                poll_manage_status.apply_async(args=[task.id], queue='manage')
            echo_message("Trigger Task: LXCA Deploy OSImage(#%s)" % task.id)

        return jsonify({"success": True, "taskid": task.id})

class ApiLxcaTasksCancel(MethodView):
    decorators = [login_required]

    def post(self, jobId):
        task = LxcaTask.query.filter_by(jobuid=jobId).first()
        res = {"success": True}
        if task and task.status == "Running":
            with get_lxca(task.dhcp) as api:
                api.cancel_task(jobId)
                task.status = "Cancelled"
                task.update()
                echo_message("Stop Task: LXCA Deploy OSImage(#%s)" % jobId)
        return jsonify(res)


class ApiLxcaTaskProgress(MethodView):
    decorators = [login_required]

    def post(self, taskid):
        task = LxcaTask.query.get_or_404(taskid)
        with get_lxca(task.dhcp) as api:
            res = api.get_set_tasks({"jobUID": task.jobuid})
            for itask in res["TaskList"]:
                if itask["jobUID"] == task.jobuid:
                    task.status = itask["status"]
                    task.update()
        return jsonify(res)

class ApiLxcaTasksRunning(MethodView):
    def get(self):
        # return running lxca deploy osimage tasks
        # tasks under managing, status == 'Created'
        managingTasks = []
        for t in LxcaTask.queryManagingTasks():
            tdict = t.to_dict()
            if tdict["params"] is not None:
                tdict["params"] = json.loads(tdict["params"])
            managingTasks.append(tdict)

        deployingTasks = []
        for t in LxcaTask.query.filter_by(status="Running"):
            tdict = t.to_dict()
            tdict["params"] = json.loads(tdict["params"])
            deployingTasks.append(tdict)
        ret={"managingTasks": managingTasks, "deployingTasks": deployingTasks}
        return jsonify(ret)


class ApiLxcaTasksHistory(MethodView):
    def get(self):
        # history arrange by ip address
        tasklist=[]
        for task in LxcaTask.queryTaskHistory():
            duration = task.updatetime - task.createtime
            taskdict = task.to_dict()
            taskdict["duration"] = duration.seconds
            taskdict["params"] = json.loads(taskdict["params"])
            tasklist.append(taskdict)
        temp = {}
        iplist = []
        for t in tasklist:
            k = t["params"].get("immip", "unknown")
            if k in temp:
                temp[k].append(t)
            else:
                iplist.append(k)
                temp[k] = [t]
        data = []
        for ipAddress in iplist:
            one = {"ipAddress": ipAddress, "tasks": temp[ipAddress]}
            data.append(one)
        return jsonify(data)

class ApiLxcaHost(MethodView):

    def checkReady(self, hostinfo):
        default = {
            "accessState": "Online",
            "isAuthorized": True,
            "remotePresenceMode": "Enabled",
            "uefiMode": "Enabled",
            "validMac": "ok",
            "vlanAutoMac": "ok"
        }
        if hostinfo["deployStatusID"] == 1:
            readyCheck = hostinfo["readyCheck"]
            for k, v in default.items():
                if readyCheck[k] != v:
                    return 1
            return 0
        elif hostinfo["deployStatusID"] != 0:
            return 1
        return 0

    def get(self):
        ip = util.args_get("ip", required=True)

        with get_lxca() as api:
            hostPlatforms = api.get_hostPlatforms()
        res = {}
        for item in hostPlatforms['items']:
            if item["immIpAddress"] == ip:
                res = item
                break
        if "deployStatusID" in res:
            res["deployStatusID"] = self.checkReady(res)
        res.pop("bootOrder", None)
        res.pop("networkSettings", None)
        return jsonify(res)

class ApiLxcaTaskManageCancel(MethodView):
    decorators = [login_required]
    
    def post(self, taskid):
        task = LxcaTask.query.get_or_404(taskid)
        if task.status == "Done":
            task.status = "Cancelled"
            task.update()
            echo_message("Cancel Task Manage: #%s" % task.id)
        return jsonify({"success": True})

class ApiLxcaManage(MethodView):
    def post(self):
        jd = request.get_json()

        res = {}
        if 'ip' not in jd or 'user' not in jd or 'pw' not in jd:
            abort(404)
        if not LxcaTask.isImmipCanManage(jd["ip"]):
            res["warning"] = "Host of ip %s is now under managing by lxca." % jd["ip"]
            return jsonify(res)
        manage_handler = dict(jd, force=True)
        with get_lxca() as api:
            hostPlatforms = api.get_hostPlatforms()
            host = None
            # readyCheck:accessState 
            # The access state must be online "Online" or "unSupported" 
            # to deploy an operating system on the host platform
            for item in hostPlatforms['items']:
                if item["immIpAddress"] == jd["ip"]:
                    host = item
                    break
            status, jobuid = "Done", None
            if host is None or host["readyCheck"]["accessState"] not in {"Online","unSupported"}:
                # host is not managed
                try:
                    res["jobId"] = api.do_manage(manage_handler)
                except Exception as e:
                    res['error'] = e.message
                    return jsonify(res)
                else:
                    status, jobuid = "Created", res["jobId"]
            else:
                res["warning"] = "Host of ip %s Already Managed by lxca" % jd["ip"]
            # res = api.delopy_os_image(jd["uuid"], jd["image"], jd["os_ip"], jd["gateway"], jd["subnetMask"])
            # if "jobId" in res:
            # jobId = res["jobId"]
            # res2 = api.get_set_tasks({"jobUID": jobId})
            info = {}
            info['username'] = session["displayName"]
            info['userid'] = session["mail"].split('@')[0]
            task = LxcaTask()
            task.createFromManage(jobuid, status, info, jd["ip"], json.dumps({"immip": jd["ip"]}))
            # task.createFromDeployOSImage(jobId, info, json.dumps(jd))
            poll_manage_status.apply_async(args=[task.id], queue='manage')
            echo_message("Trigger Task: LXCA Deploy OSImage(#%s)" % task.id)

        return jsonify(res)


class ApiLxcaManageRequest(MethodView, LXCAMixin):
    def get(self, taskid):
        task = LxcaTask.query.get_or_404(taskid)
        res = {
            "progress": 100,
            "result": 100,
            "status": "Done"
        }
        if task.status == 'Created':
            with get_lxca(task.dhcp) as api:
                try:
                    res = api.do_manage({"job": task.jobuid})
                except Exception as e:
                    res['error'] = e.message
                    return jsonify(res)
        params = json.loads(task.params)
        if not self.isDeployStatusReady(params["immip"], task.dhcp):
            fakeData = {
                "progress": 99,
                "result": 99,
                "status": "Incomplete"            
            }
            if task.status == "Created":
                # actually do manageing host, and response from lxca backend shows "Done"
                # but the depoly status of host is not ready
                # so fake the response for frontend to wait for 
                if res["status"] == "Done":
                    res.update(fakeData)
            else:
                # actually not do managing host, just return the fake data
                res = fakeData

        return jsonify(res)


class ApiLxcaOSImages(MethodView):
    def get(self):
        data = rpc_clt.get_cache_by_key("osImages")
        return jsonify(data)


class ApiStressArchive(MethodView):
    decorators = [util.token_required("ARCHIVE_TOKEN")]
    def post(self):
        """

        """
        jd = request.get_json()
        infodata = jd["info"]
        # Check if the stress task already started, if not, create a new `StressTask` instance
        task = StressTask.query.filter_by(build_number=int(infodata["BUILD_ID"]), 
            system=infodata["SYSTEM"], release=infodata["RELEASE"]).limit(1).first()
        if not task:
            task = StressTask()
            task.create(build_number=infodata["BUILD_ID"], system=infodata["SYSTEM"], 
                release=infodata["RELEASE"], immip=infodata["IMMIP"], info=json.dumps(infodata))
        # Due to the duplicated records, need to filter out the repeated ones
        # Check if the task has any records, if yes, 
        # use the last record to search through the new-input records, 
        # and find the position where no-duplicated records started

        # Bind records with entry_task
        entry_task = Task.query.filter_by(jobname=jd["jobname"], build_number=int(jd["buildno"])).first()

        if jd.get("type",0)==0:
            lastrow = StressWatchProcs.queryLastRecordByTaskId(task.id)
            if lastrow:
                lastrowdict = lastrow.to_dict()
                fields=["up_secs","pid","rss_anon","heap","rss_anon_d","heap_d","process_name"]
                for i,r in enumerate(jd["records"]):
                    if r[fields[-1]]==lastrowdict[fields[-1]]:
                        if all(int(r[f]) == lastrowdict[f] for f in fields[:-1]):
                            jd["records"] = jd["records"][i+1:]
                            break
            if jd["records"]:
                df = pd.DataFrame(jd["records"])
                df["taskid"] = pd.Series(task.id, index=df.index)
                if entry_task:
                    df["entry_taskid"] = pd.Series(entry_task.id, index=df.index)
                StressWatchProcs.createFromRecords(df.to_dict("records"))
        return jsonify({"success": True, "countNewRecords": len(jd["records"])})


class ApiStressChartOptions(MethodView):
    def get(self):
        process_group = StressWatchProcs.queryProcessGroup(util.args_get("id"))
        processNameList = [{"id": p, "name":p} for p in process_group]
        res={"processNameList": processNameList}
        return jsonify(res)

class ApiStressChart(MethodView):
    def get(self):

        res = {}
        # 0: watch-procs
        processNamelist = request.args.getlist("processName")
        taskid = util.args_get("id")
        if not taskid:
            taskid = StressWatchProcs.getLastTaskId()
        res = {"watchProcs":[]}
        for processName in processNamelist:
            res["watchProcs"].append(self.get_watch_procs_chart_data(processName, taskid))
        return jsonify(res)

    def get_watch_procs_chart_data(self, process_name, taskid):
        process, pid = process_name.rsplit('-', 1)
        seriesKeys = [
        "rss_anon",
        "heap",
        ]
        ret = {"series":{key: [] for key in seriesKeys}, "xAxis": [], "name": process_name, "legend": seriesKeys}
        series = ret["series"]
        xAxis = ret["xAxis"]
        i = 0
        for s in StressWatchProcs.query.filter_by(pid=pid, process_name=process, entry_taskid=taskid):
            series["rss_anon"].append(s.rss_anon)
            series["heap"].append(s.heap)
            # starttime = s.createtime - timedelta(seconds=s.up_secs)
            xAxis.append(s.createtime.strftime("%m/%d %H:%M"))
            i+=1
        return ret

app.add_url_rule('/task', view_func=ApiTask.as_view('api.task'))
app.add_url_rule('/task/<int:id>', view_func=ApiTaskDetail.as_view('api.task_detail'))
app.add_url_rule('/task/stages', view_func=ApiTaskStages.as_view('api.task.stages'))
app.add_url_rule('/task/report', view_func=ApiTaskReport.as_view('api.task.report'))
app.add_url_rule('/task/trigger', view_func=ApiTaskTrigger.as_view('api.task_trigger'))
app.add_url_rule('/taskScheduler', view_func=ApiTaskschedulerList.as_view('api.taskSchedulerList'))
app.add_url_rule('/taskScheduler/<int:sid>', view_func=ApiTaskscheduler.as_view('api.taskScheduler'))
app.add_url_rule('/xpit/jobs', view_func=ApiXpitJobs.as_view('api.xpit_jobs'))
app.add_url_rule('/daily/jobs', view_func=ApiDailyJobs.as_view('api.daily_jobs'))
app.add_url_rule('/pit/jobs', view_func=ApiPitJobs.as_view('api.pit_jobs'))
app.add_url_rule('/stress/jobs', view_func=ApiStressJobs.as_view('api.stress_jobs'))
app.add_url_rule('/lxca/manage', view_func=ApiLxcaManage.as_view('api.lxca_manage'))
app.add_url_rule('/lxca/task/<int:taskid>/manageCancel', view_func=ApiLxcaTaskManageCancel.as_view('api.lxca_task_manageCancel'))
app.add_url_rule('/lxca/manageRequest/<taskid>', view_func=ApiLxcaManageRequest.as_view('api.lxca_manage_request'))
app.add_url_rule('/lxca/host', view_func=ApiLxcaHost.as_view('api.lxca_host'))
app.add_url_rule('/lxca/deploy/osimage', view_func=ApiLxcaDeployOSImage.as_view('api.lxca_deploy_osimage'))
app.add_url_rule('/lxca/task/<int:taskid>/progress', view_func=ApiLxcaTaskProgress.as_view('api.lxca_task_progress'))
app.add_url_rule('/lxca/tasks/running', view_func=ApiLxcaTasksRunning.as_view('api.lxca_tasks_running'))
app.add_url_rule('/lxca/tasks/history', view_func=ApiLxcaTasksHistory.as_view('api.lxca_tasks_history'))
app.add_url_rule('/lxca/tasks/cancel/<jobId>', view_func=ApiLxcaTasksCancel.as_view('api.lxca_tasks_cancel'))
app.add_url_rule('/lxca/osImages', view_func=ApiLxcaOSImages.as_view('api.lxca_osimages'))
app.add_url_rule('/stress/archive', view_func=ApiStressArchive.as_view('api.stress_archive'))
app.add_url_rule('/stress/chart/options', view_func=ApiStressChartOptions.as_view('api.stress_chart.options'))
app.add_url_rule('/stress/chart', view_func=ApiStressChart.as_view('api.stress_chart'))