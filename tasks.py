from celery import Task as CeleryTask
from datetime import datetime, timedelta
from jenkins_backend import getServer
import logging
import sys
import os
import json
curdir = os.path.dirname(__file__)
sys.path.append(os.path.join(curdir, "../../"))
from src.xpit.models import Task, LxcaTask, TaskScheduler
from src.admin.models import Message
from src.service import cache
from src.service.lxca import get_lxca, LXCAMixin
from src.xpit.celery_app import celery


LOG = logging.getLogger(__name__) 

class BugsTask(CeleryTask):
    def on_success(self, retvalArr, task_id, args, kwargs):
        for retval in retvalArr:
            dp_id = retval['duplicated_id']
            mgdb.save_bugs_point(retval['bugs_data']) 
            if dp_id:
                mgdb.delete_bugs_point(dp_id)
        return super(BugsTask, self).on_success(retval, task_id, args, kwargs)
    #def on_failure(self, exc, task_id, args, kwargs, einfo):
    #    print 'task fail, reason: {0}'.format(exc)
    #    return super(MyTask, self).on_failure(exc, task_id, args, kwargs, einfo)


@celery.task
def poll_task_state():
    from src.main import app as current_app
    server = getServer()
    with current_app.app_context():
        for task in Task.query.filter_by(building=True):
            try:
                info = server.get_build_info(task.jobname, task.build_number)
            except Exception:
                continue
            if not info["building"]: task.updateFromBuildInfo(info)
        for tser in TaskScheduler.queryActiveSchedulers():
            jobname, params = tser.jobname, {k:v for k, v in json.loads(tser.params)}
            buildNumber, msg = server.buildJob(jobname, params)
            if buildNumber < 0:
                res = {"success": False, "error": msg}
                LOG.error("------------------%s" % res)
            else:

                buildInfo = server.get_build_info(jobname, buildNumber)
                buildInfo['username'] = tser.username
                buildInfo['userid'] = tser.itcode
                buildInfo["release"] = tser.release
                buildInfo["source"] = tser.source

                Task().createFromBuildInfo(jobname, buildNumber, buildInfo, tser.params)

                msg = {"userid": tser.userid,
                        "event": "Trigger Task: %s(#%s)" % (jobname, buildNumber),
                        "result":"SUCCESS"}
                LOG.info("---------------------%s" % msg)
                Message().create(msg)
                tser.scheduleNext()



@celery.task
def sync_jenkins_jobs():
    # fecth & transform job info
    server = getServer()
    jobs={}
    pit_jobs=jobs["pit"]=[]
    xpit_jobs=jobs["xpit"]=[]
    daily_jobs=jobs["daily"]=[]
    stress_jobs=jobs["stress"]=[]
    for job in server.get_all_jobs():
        jname = job["name"].lower()
        if jname.endswith('entry'):
            if jname.startswith("xpit"):
                xpit_jobs.append(job)
            elif jname.startswith("pit"):
                pit_jobs.append(job)
        elif jname.endswith('daily'):
            daily_jobs.append(job)
        elif jname.endswith("mem"): #memory stress
            stress_jobs.append(job)

    def handle_jobs(jobs):
        for job in jobs:
            job_info = server.get_job_info(job['fullname'])
            params=[]
            # transvers across array: property&actions
            for action in job_info["actions"]:
                if "parameterDefinitions" in action:
                    params.extend(action["parameterDefinitions"])
            for prop in job_info["property"]:
                if "parameterDefinitions" in prop:
                    params.extend(prop["parameterDefinitions"])

            job["params"] = params
    handle_jobs(pit_jobs)
    handle_jobs(xpit_jobs)
    handle_jobs(daily_jobs)
    handle_jobs(stress_jobs)
    # set cache
    cache.set_pivot("jobs", jobs)



    # {u'url': u'http://qq.com:8080/jenkins/job/xPITCustomization/job/xpit_m1_sr950_128/', 
    # u'color': u'blue', u'fullname': u'xPITCustomization/xpit_m1_sr950_128', 
    # u'_class': u'org.jenkinsci.plugins.workflow.job.WorkflowJob', u'name': u'xpit_m1_sr950_128'}

@celery.task
def poll_manage_status(taskid):
    from src.main import app as current_app
    import time
    with current_app.app_context():
        task = LxcaTask.query.get(taskid)
        if not task:
            LOG.error("Invalid taskid")
            return
        if task.status != "Created":
            LOG.error("task.status is not 'Created':%s" % task.status)
            return 
        if not task.jobuid:
            return
        with get_lxca(task.dhcp) as api:
            while True:
                try:
                    res = api.do_manage({"job": task.jobuid})
                except Exception as e:
                    LOG.error(e.message)
                    break
                LOG.info("----------------------status:%s,progress:%s" % (res["status"], res["progress"]))
                if "DONE" in res["status"].upper():# Created, Incomplete,Done,Done_Warnimg
                    task.status = "Done"
                    task.update()
                    LOG.info("manage status:%s, taskid:%s" % (task.status, taskid))
                    break
                else:
                    time.sleep(3)
@celery.task
def poll_deploy_status():
    # if managing host action is done and deploy status is ready, then trigger the deploy os task
    # `task.status` changed from 'Created' -> 'Done' -> 'Running'
    # `Created` means tasks have been just created, hosts should be under managing
    # `Done` means management finished
    # `Running` means host is under deploying os

    def process(task, api):
        util = LXCAMixin(api)
        hostPlatforms = api.get_hostPlatforms()
        params = json.loads(task.params)
        host = None
        for item in hostPlatforms['items']:
            if item["immIpAddress"] == params["immip"]:
                host = item
                break
        if host is None:
            task.status = "Cancelled"
            task.update()
            return
        if not task.dhcp:
            initres = api.initHostSettings(host["uuid"], params["immip"])
            LOG.info("-----------------%s %s" % (params, initres))

        isready = util.isDeployStatusReady(params["immip"], task.dhcp)
        LOG.info("---------------------------%s" % isready)
        if isready:
            LOG.info("start lxca deploy_os_image:%s" % params)
            flag = False
            for aImage in host["availableImages"]:
                if params["image"] in {aImage["label"], aImage["value"]}:
                    flag=True
                    break
            if not flag:
                task.status = "ImageNotSupport"
                task.update()
                return
            res = api.delopy_os_image(
                host["uuid"], params["image"], params["os_ip"], params["gateway"], params["subnetMask"])
            if "error" in res:
                task.status = "StoppedWithError"
                task.update()
            elif "jobId" in res:
                task.jobuid = res["jobId"]
                task.hostuuid = host["uuid"]
                task.status = "Running"
                task.update()
            LOG.info('------------%s %s' % (res, task.status))
    from src.main import app as current_app
    try:
        with get_lxca() as api_static:
            with get_lxca(dhcp=True) as api_dhcp:
                # flash "osImages" Cache by the way
                cache.set_pivot("osImages", api_static.get_hostPlatforms()["availableImages"])
                with current_app.app_context():
                    for task in LxcaTask.query.filter_by(status="Done"):
                        process(task, api_dhcp if task.dhcp else api_static)
    finally:
        try:
            LOG.info("--------------finally do cleaning!")
            api_static.con.disconnect()
            api_dhcp.con.disconnect()
        except:
            pass
