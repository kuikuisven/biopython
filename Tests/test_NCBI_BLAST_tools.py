# Copyright 2009 by Peter Cock.  All rights reserved.
# This code is part of the Biopython distribution and governed by its
# license.  Please see the LICENSE file that should have been included
# as part of this package.
#
# This unit test attempts to locate the blastall executable and the nr
# database, and if it finds them then do some standalone blast searches
# using Bio.Blast.NCBIStandalone to call the command line tool.

import os, sys
import subprocess
import unittest

from Bio import MissingExternalDependencyError
from Bio.Blast import Applications

# TODO - On windows, can we use the ncbi.ini file?
wanted = ["blastx", "blastp", "blastn", "tblastn", "tblastx",
          "rpsblast", "rpstblastn", "psiblast"]
exe_names = {}

if sys.platform=="win32":
    #The Windows 32 bit BLAST 2.2.22+ installer does add itself to the path,
    #and by default installs to C:\Program Files\NCBI\BLAST-2.2.22+\bin
    #To keep things simple, assume BLAST+ is on the path on Windows.
    #
    #On Windows the environment variable name isn't case senstive,
    #but must split on ";" not ":"
    likely_dirs = os.environ.get("PATH", "").split(";")
else :
    likely_dirs = os.environ.get("PATH", "").split(":")

for folder in likely_dirs:
    if not os.path.isdir(folder): continue
    for name in wanted :
        if sys.platform=="win32":
            exe_name = os.path.join(folder, name+".exe")
        else:
            exe_name = os.path.join(folder, name)
        if not os.path.isfile(exe_name):
            continue
        #To tell the old and new rpsblast apart (since I have both on
        #my path and the old blast has priority), try -h as a parameter:
        child = subprocess.Popen(exe_name + " -h",
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=(sys.platform!="win32"))
        output, error = child.communicate()
        if child.returncode==0 and "ERROR: Invalid argument: -h" not in output:
            exe_names[name] = exe_name
        #else :
        #    print "Rejecting", exe_name
        del exe_name, name

if len(exe_names) < len(wanted) :
    raise MissingExternalDependencyError("Install the NCBI BLAST+ command line "
                                         "tools if you want to use the "
                                         "Bio.Blast.Applications wrapper.")
        
class CheckCompleteArgList(unittest.TestCase):
    def check(self, exe_name, wrapper) :
        global exe_names
        exe = exe_names[exe_name]
        cline = wrapper(exe, h=True)

        names = set(parameter.names[0] \
                    for parameter in cline.parameters)
        
        child = subprocess.Popen(str(cline),
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=(sys.platform!="win32"))
        stdoutdata, stderrdata = child.communicate()
        self.assertEqual(stderrdata, "",
                         "%s\n%s" % (str(cline), stderrdata))
        names_in_tool = set()
        while stdoutdata :
            index = stdoutdata.find("[")
            if index == -1 : break
            stdoutdata = stdoutdata[index+1:]
            index = stdoutdata.find("]")
            assert index != -1
            name = stdoutdata[:index]
            if " " in name : name = name.split(None,1)[0]
            names_in_tool.add(name)
            stdoutdata = stdoutdata[index+1:]
                
        extra = names.difference(names_in_tool)
        missing = names_in_tool.difference(names)
        if "-soft_masking" in missing :
            #Known issue, need to establish how this option works
            missing.remove("-soft_masking")
        if "-use_index" in missing :
            #Known issue, need to establish how this option works
            missing.remove("-use_index")

        if extra or missing :
            print "Extra: " + ",".join(sorted(extra))
            print "Missing: " + ",".join(sorted(missing))

        self.assertEqual(len(extra), 0, \
                         "Wrapper has extra: " + ", ".join(sorted(extra)))
        self.assertEqual(len(missing), 0, \
                         "Wrapper is missing: " + ", ".join(sorted(missing)))

    def test_blastx(self):
        """Check all blastx arguments are supported"""
        self.check("blastx", Applications.NcbiblastxCommandline)
        
    def test_blastp(self):
        """Check all blastp arguments are supported"""
        self.check("blastp", Applications.NcbiblastpCommandline)

    def test_blastn(self):
        """Check all blastn arguments are supported"""
        self.check("blastn", Applications.NcbiblastnCommandline)

    def test_tblastx(self):
        """Check all tblastx arguments are supported"""
        self.check("tblastx", Applications.NcbitblastxCommandline)
        
    def test_tblastn(self):
        """Check all tblastn arguments are supported"""
        self.check("tblastn", Applications.NcbitblastnCommandline)
        
    def test_psiblast(self):
        """Check all psiblast arguments are supported"""
        self.check("psiblast", Applications.NcbipsiblastCommandline)

    def test_rpsblast(self):
        """Check all rpsblast arguments are supported"""
        self.check("rpsblast", Applications.NcbirpsblastCommandline)

    def test_rpstblastn(self):
        """Check all rpstblastn arguments are supported"""
        self.check("rpstblastn", Applications.NcbirpstblastnCommandline)


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity = 2)
    unittest.main(testRunner=runner)
