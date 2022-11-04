import sys

python_requirement = '3.7.0'

import platform
if platform.python_version() < python_requirement:
	if platform.python_version() < '3.10.0':
		print('Oops! Your Python version is too old.\n')
		print(f'Requirement: Python {python_requirement}+\nYou have   : Python {platform.python_version()}')
		print('\nGet a newer version!')
		sys.exit()

try: import tkinter as tk
except ImportError:
	print('''Oooh no you don\'t have Tkinter.
You have 2 options:

1. Install Tkinter (do it yourself, there are lots of guides online)
2. Use the console version of QuizProg

Now scram!''')
	sys.exit()

import os
import traceback

import tkinter.messagebox
try:
	from gui import GUI, report_error

	g = GUI(tk.Tk())

except ImportError: tk.messagebox.showerror('Hmmm?', f'Whoops! The script "gui.py" is required.\nCan you make sure the script is in "{os.getcwd()}"?')
except Exception: report_error()