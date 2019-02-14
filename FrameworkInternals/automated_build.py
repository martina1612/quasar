#!/usr/bin/env python
# encoding: utf-8
'''
automated_build.py

@author:     Damian Abalo Miron <damian.abalo@cern.ch>
@author:     Piotr Nikiel <piotr@nikiel.info>

@copyright:  2015 CERN

@license:
Copyright (c) 2015, CERN, Universidad de Oviedo.
All rights reserved.
Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

@contact:    quasar-developers@cern.ch
'''

import os
import platform
import subprocess
import re
from generateCmake import generateCmake
from externalToolCheck import subprocessWithImprovedErrors
from commandMap import getCommand
from quasarExceptions import WrongArguments

def findFileRecursively( topdir, target ):
	for dirpath, dirnames, files in os.walk(topdir):
		for name in files:
			if name == target:
				return True;
	return False;

def read_build_config_selector():
        f = open(os.path.join('FrameworkInternals','build_config_selector.cmake'))
        # here continue with parsing the file
        # it should be exactly two lines
        text = f.read()
        regex = re.compile(r"#(.)*\ninclude\((?P<file>.*)\)\n")
        match = regex.match(text)
        if match is None:
                raise Exception( 'The build config file is in wrong format. Please run the command with an argument to the build config to overwrite the selection' )
        else:
                return match.group('file')


def write_build_config_selector(build_config_file):
        if os.path.isabs(build_config_file):
            print """WARNING: You seem to have specified an absolute path.
                This will be a problem if you run your build automatically in another location, 
                and especially if you do Yocto builds."""
        f = open(os.path.join('FrameworkInternals','build_config_selector.cmake'), 'w')
        f.write("# This file has been generated by quasar. Don't edit.\n")
        f.write("include({0})\n".format(build_config_file))
        f.close()
        if os.path.isfile('CMakeCache.txt'):
                print "I'm clearing your CMakeCache now because the build config changed"
                os.remove('CMakeCache.txt')
        print 'New build config has been set'

def build_config():
        """
        Prints the currently chosen build configuration file.
        """
        if os.path.isfile( os.path.join('FrameworkInternals','build_config_selector.cmake')):
                fn = read_build_config_selector()
                print 'Currently chosen build config is: '+fn
        else:
                print 'Build config is not chosen yet. Please run "quasar.py set_build_config <path_to_the_build_config>"'

def set_build_config(build_config):
        if build_config is None:
                raise WrongArguments ('Please provide the argument')
        else:
                write_build_config_selector(build_config)

def automatedBuild(context, buildType="Release"):
	"""Method that generates the cmake headers, and after that calls make/vis-studio to compile your server.

	Keyword arguments:
	buildType -- Optional parameter to specify Debug or Release build. If it is not specified it will default to Release.
	"""
        if not buildType in ["Release","Debug"]:
                raise Exception ("Only Release or Debug is accepted as the parameter. "
                                 "If you are used to passing build config through here, note this version of quasar has separate command to do that: build_config")
	generateCmake(context, buildType)

	print("Calling build, type ["+buildType+"]...")
	if platform.system() == "Windows":
		try:
			subprocessWithImprovedErrors( "cmake --build . --target ALL_BUILD --config "+buildType, 'visual studio build')
		except Exception, e:
			print("Build process error. Exception: [" + str(e) + "]")
	elif platform.system() == "Linux":
		print('make -j$(nproc)')
		process = subprocess.Popen(["nproc"], stdout=subprocess.PIPE)
		out, err = process.communicate()
		subprocessWithImprovedErrors([getCommand("make"), "-j" + str(int(out))], getCommand("make"))#the conversion from string to int and back to string is to remove all whitespaces and ensure that we have an integer
