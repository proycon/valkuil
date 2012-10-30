#!/usr/bin/env python
#-*- coding:utf-8 -*-

#!/usr/bin/env python
#-*- coding:utf-8 -*-

#Valkuil harvester

import os
import glob
import time

DIR = "userdocs/"
now = time.time()

MAXAGE = 15 * 60 #15 minutes

for filepath in glob.glob(DIR + '/*.xml'):
    if now - os.path.getatime(filepath) > MAXAGE:
        os.unlink(filepath)
