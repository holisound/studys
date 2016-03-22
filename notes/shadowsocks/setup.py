from distutils.core import setup
import py2exe
includes = ["encodings", "encodings.*"]
options = {"py2exe":
         { "compressed": 1,
            "optimize": 2,
            "includes": includes,
            "bundle_files": 1,
           "dll_excludes":"w9xpopen.exe"
         }
      }
setup( 
version = "0.1.0",
description = "FreeSS",
name = "FreeSS",
options = options,
zipfile=None,
console=['winss.py']
#data_files= [('images', ['bing.ico'])],
# windows=[{"script":"test.pyw",
#           "icon_resources": [(1,"hello.ico"),(42,"bing.ico")]}]  
)