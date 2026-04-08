import os
import sys

python_requirement = (3, 6, 0, 'alpha', 4)  # 3.6.0a4

import platform
if sys.version_info < python_requirement:
	print('Oops! Your Python version is too old.\nRequirement: Python {}'.format('.'.join(map(str, python_requirement))) + '\nYou have   : Python {}'.format(platform.python_version()))
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
	
import traceback

import tkinter.messagebox

if __name__ == '__main__':
	try: import gui
	except ImportError:
		err_text = f'Whoops! An error occured when attempting to import "gui.py".'
		print(err_text)
		tk.messagebox.showerror('Hmmm?', err_text)
		sys.exit()

	g = gui.GUI(sys.argv[1] if len(sys.argv) > 1 else '')
	gui.g = g
	try: g.start_main()
	except Exception: tk.messagebox.showerror('Error', gui.report_error.__func__(*sys.exc_info(), True))
