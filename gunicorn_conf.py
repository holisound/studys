from multiprocessing import cpu_count
import os

curdir = os.path.dirname(__file__)

logsdir = os.path.join(curdir, "logs")
if not os.path.isdir(logsdir):
    os.makedirs(logsdir)

timeout=60*3

workers = 2

accesslog = os.path.join(logsdir, "access.log") 
errorlog = os.path.join(logsdir, "error.log")
bind="127.0.0.1:5028"
