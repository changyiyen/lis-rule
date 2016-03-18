#!/usr/bin/python3
# -*- coding: utf-8 -*-

import tkinter as tk
#import Tkinter as tk
from tkinter import filedialog as tkFileDialog
#import tkFileDialog
import sys
import ast
import itertools
import re
import os
import subprocess

class Application(tk.Frame):
	"""
	Simple GUI for lisanalyze.py for those unwilling or unable to
	use the command line. ;)

	Currently known to work on Python 3.4.3, but shouldn't be too hard
	to backport to Python 2, since only a few package names have changed.
	That said, the subprocess.check_output() function call used herein
	failed on Python 2.7.8 (which is outdated) while the exact same call
	worked on Python 3.4.3.
	"""
	def __init__(self, master=None):
		"""
		Initialize our app.
		"""
		tk.Frame.__init__(self, master)
		self.grid()
		self.createWidgets()

	def createWidgets(self):
		self.topFrame = tk.Frame(padx=10, pady=10)
		self.topFrame.grid()

		# Variables required by widgets go here
		self.entryText = tk.StringVar()
		self.resultsText = tk.StringVar()
		self.messageText = tk.StringVar()
		self.fileOpt = {}
		self.fileListVar = tk.StringVar()

		# Left half: messages, buttons, filename list
		self.lFrame = tk.Frame(self.topFrame)
		self.lFrame.grid(column=0)
		
		# Messages
		self.messageBox = tk.Label(self.lFrame,
			textvariable=self.messageText
		)
		self.messageBox.grid(row=1, column=0)
		
		# Buttons
		self.buttonFrame = tk.Frame(self.lFrame)
		self.buttonFrame.grid(row=2, column=0)
		
		self.addButton = tk.Button(self.buttonFrame,
			command=self.addFiles, text="Add files"
		)
		self.addButton.grid(row=0, column=0)

		self.removeButton = tk.Button(self.buttonFrame,
			command=self.removeFiles, text="Remove files"
		)
		self.removeButton.grid(row=0, column=1)
		
		self.runButton = tk.Button(self.buttonFrame,
			command=self.runAnalyzer, text="Run")
		self.runButton.grid(row=0, column=2)
		
		self.quitButton = tk.Button(self.buttonFrame,
			command=self.quit, text="Quit"
		)
		self.quitButton.grid(row=0, column=3)
		
		# List of files
		self.fileList = tk.Listbox(self.lFrame,
			listvariable=self.fileListVar, width=50,
			selectmode=tk.MULTIPLE
		)
		self.fileList.grid(row=3, column=0)

		# Right half: results box
		self.rFrame = tk.LabelFrame(self.topFrame, text="Results")
		self.rFrame.grid(row=0, column=1)
		self.resultsBox = tk.Label(self.rFrame,
			textvariable=self.resultsText,
			justify=tk.LEFT,
			wraplength=300,
			height=20, width=60
		)
		self.resultsBox.grid()

	# additional functions go here
	def addFiles(self):
		filenames = tkFileDialog.askopenfilenames(**self.fileOpt)
		# using a loop below, otherwise multiple items (if selected at once)
		# will end up on the same line
		for i in filenames:
                        # For Windows compatability
			j = os.path.normpath(i)
			self.fileList.insert(tk.END, j)
		return True
	def removeFiles(self):
		"""
		Removes files from file list in lower lefthand corner. Spaces
		in filenames are a PITA, especially combined with Tk's use of
		spaces as list item separators.
		"""
		filename_indexes = self.fileList.curselection() # indexes are strings
		#pathRegex = "[\w." + os.sep + "]+"
		#print("Before:" + self.fileListVar.get())
		#print("Escape:" + self.fileListVar.get().replace(' ', '\ ')) # escape the spaces first
		pathRegex = "'.+?'"
		filenameList = re.findall(pathRegex, self.fileListVar.get().replace(' ', '\ '))
		#print("FNL:", filenameList)
		for i in filename_indexes:
			print(int(i), filenameList[int(i)])
			del filenameList[int(i)]
		self.fileListVar.set(' '.join(filenameList))
		#print("Join:" + ' '.join(filenameList))
		#print("After:" + self.fileListVar.get())
		return True
	def runAnalyzer(self):
		"""
		Calls lisanalyze.py. The runAnalyzer function is actually
		pretty generic, just a wrapper around a creation of a
		subprocess. Might block due to the subprocess call.
		"""
		filenames = ' '.join(ast.literal_eval(self.fileListVar.get()))
		if (filenames[0] == filenames[-1]) and filenames[0] in ("'", '"'):
			filenames = filenames[1:-1] # unquote filenames if necessary

		lisanalyzePath = "./lisanalyze.py"
		self.messageText.set("Current path to lisanalyze.py: " + lisanalyzePath)
		#print(filenames)
		self.resultsText.set(
			str(
				subprocess.check_output(
					["python3", lisanalyzePath, "-f", filenames],
					universal_newlines=True
				)
			)
		)
		return True

app = Application()
app.master.title('lisanalyze_gui 0.1 "Heat haze"')
app.mainloop()
