import sys
if __name__ == '__main__':
	print('Please run main.py to start the program!')
	sys.exit()

import os
import shutil
import platform
import traceback
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font
import tkinter.messagebox
import tkinter.filedialog

try: temp_path = sys._MEIPASS

except AttributeError: temp_path = os.getcwd()

# main modules
import re
import json
import time
import random
import importlib
import threading
import webbrowser
import configparser
import pkg_resources
import urllib.request
from jsonhandler import JSONHandler

name = 'QuizProg-GUI'

username = 'gamingwithevets'
repo_name = 'quizprog-gui'

version = '1.1.1'
internal_version = 'v1.1.1'
prerelease = False

license = 'MIT'

g = None

def fmt_oserror(exc):
	if os.name == 'nt':
		if exc.winerror: errno = f'WE{exc.winerror}'
		else: errno = exc.errno
	else: errno = exc.errno
	return f'[{type(exc).__name__}] {exc.filename}{", "+exc.filename2 if exc.filename2 else ""}: {exc.strerror} ({errno})'

@staticmethod
def report_error(e, val, tb, fatal = False):
	err_text = '\n'.join(traceback.format_exception(e, val, tb)) + f'\nIf this error persists, please report it here:\nhttps://github.com/{username}/{repo_name}/issues'

	exc = val

	print(f'{"Fatal exception" if fatal else "Exception"} raised:\n\n' + err_text)
	if issubclass(type(exc), OSError): message = fmt_oserror(exc)
	else: message = f'[{type(exc).__name__}] {exc}'
	g.set_message_force(message)
	g.window.update()
	return 'Oops! A fatal error has occured.\n\n' + err_text

tk.Tk.report_callback_exception = report_error

class GUI:
	def __init__(self, savepath, player_mode = False):
		self.version = version

		self.window = tk.Tk()

		self.temp_path = temp_path

		self.display_w = 500
		self.display_h = 500

		self.updater_win_open = False

		tk_font = tk.font.nametofont('TkDefaultFont')

		self.bold_font = tk_font.copy()
		self.bold_font.config(weight = 'bold')
		self.italic_font = tk_font.copy()
		self.italic_font.config(slant = 'italic')

		self.init_window()

		# quizprog-gui settings
		self.message = 'Loaded template quiz.'
		self.message_force = None
		self.datafile = {'title': 'My Quiz', 'questions': [{'question': 'Question', 'a': 'Answer A', 'b': 'Answer B', 'c': 'Answer C', 'd': 'Answer D', 'correct': 'a'}]}
		self.datafile_mode = 'json'

		self.savepath = savepath
		self.allowsave = True

		self.modified = False

		self.player_mode = player_mode

		self.auto_check_updates = tk.BooleanVar(); self.auto_check_updates.set(True)
		self.check_prerelease_version = tk.BooleanVar(); self.check_prerelease_version.set(False)

		self.updates_checked = player_mode

		self.debug = False

		if os.name == 'nt': self.appdata_folder = f'{os.getenv("LOCALAPPDATA")}\\{name}'
		elif platform.system() == 'Darwin': self.appdata_folder = os.path.expanduser(f'~/Library/Application Support/{name}')
		else: self.appdata_folder = os.path.expanduser(f'~/.config/{name}')

		self.save_to_cwd = False
		self.ini = configparser.ConfigParser()
		self.parse_settings()

		self.input_string_text = ''
		self.input_string_skip = False

		self.jsonhandler = JSONHandler(self, report_error, fmt_oserror)
		self.compile_exe = CompileEXE(self)
		self.quiz_player = QuizPlayer(self)
		self.quizconf = QuizConf(self)
		self.question_viewer = QuestionViewer(self)
		self.updater_gui = UpdaterGUI(self)

		self.unsupported_tcl = False
		if sys.version_info < (3, 7, 6):
			if tk.messagebox.askyesno('Warning', f'It looks like you are running Python {platform.python_version()}, which has a version of Tcl/Tk that doesn\'t support some Unicode characters.\n\nDo you want to continue?', icon = 'warning'): self.unsupported_tcl = True
			else: self.quit()

	def set_message_force(self, msg):
		self.message_force = msg
		self.config_msg()

	def start_main(self):
		if not self.updates_checked:
			if self.auto_check_updates.get(): threading.Thread(target = self.auto_update).start()
			else: self.updates_checked = True

		if self.savepath and not self.savepath.isspace():
			if not self.savepath.endswith('.json') and not self.savepath.endswith('.qpg'): tk.messagebox.showwarning('Warning', f"Your quiz's extension is of a file type unsupported by {name}. You'll still be able to load the file normally, but it is recommended to fix this issue in the future.")
			self.savepath = os.path.abspath(self.savepath)
			success, message = self.jsonhandler.check_json(self.savepath)
			if success:
				self.message = message
				self.open_file_ex()
			else:
				self.message_force = message
				self.savepath = self.jsonhandler.savepath = ''

		self.window.after(0, self.quiz_player.main if self.player_mode else self.main)
		self.window.mainloop()

	def auto_update(self):
		self.update_thread = ThreadWithResult(target = self.updater_gui.updater.check_updates, args = (True,))
		self.update_thread.start()
		i = 0
		j = 0
		mult = 2500
		while self.update_thread.is_alive():
			if i == mult*4:
				i += 1
				j = 1
			else: i = i-1 if j else i+1
			if i == 0: j = 0
			print(' '*(int(i/mult)) + '.' + ' '*(5-int(i/mult)), end = '\r')
		print('\r     ', end = '\r')
		update_info = self.update_thread.result
		if update_info['newupdate']: self.updater_gui.init_window(True, (update_info['title'], update_info['tag'], update_info['prerelease'], update_info['body']))
		self.updates_checked = True

	def parse_settings(self):
		# load override settings
		if os.path.exists(os.path.join(os.getcwd(), 'settings.ini')):
			self.ini.read('settings.ini')
			self.save_to_cwd = True
		# load normal settings
		else: self.ini.read(os.path.join(self.appdata_folder, 'settings.ini'))

		sects = self.ini.sections()
		if sects:
			if 'updater' in sects:
				try: self.auto_check_updates.set(self.ini.getboolean('updater', 'auto_check_updates'))
				except: pass
				try: self.check_prerelease_version.set(self.ini.getboolean('updater', 'check_prerelease_version'))
				except: pass

			if 'dont_touch_this_area_unless_you_know_what_youre_doing' in sects:
				try: self.debug = self.ini.getboolean('dont_touch_this_area_unless_you_know_what_youre_doing', 'debug')
				except: pass

		self.save_settings()

	def save_settings(self):
		sects = self.ini.sections()

		# settings are set individually to retain compatibility between versions

		if 'settings' not in sects: self.ini['settings'] = {}

		if 'updater' not in sects: self.ini['updater'] = {}
		self.ini['updater']['auto_check_updates'] = str(self.auto_check_updates.get())
		self.ini['updater']['check_prerelease_version'] = str(self.check_prerelease_version.get())

		if 'dont_touch_this_area_unless_you_know_what_youre_doing' not in sects: self.ini['dont_touch_this_area_unless_you_know_what_youre_doing'] = {}
		self.ini['dont_touch_this_area_unless_you_know_what_youre_doing']['debug'] = str(self.debug)

		if self.save_to_cwd:
			with open(os.path.join(os.getcwd(), 'settings.ini'), 'w') as f: self.ini.write(f)

		if not os.path.exists(self.appdata_folder): os.makedirs(self.appdata_folder)
		with open(os.path.join(self.appdata_folder, 'settings.ini'), 'w') as f: self.ini.write(f)

	def n_a(self): tk.messagebox.showinfo('Not implemented', f'This feature is not yet implemented into {name}.\nSorry!')

	def refresh(self, load_func = False, custom_func = None, menubar = True):
		for w in self.window.winfo_children(): w.destroy()
		
		self.rebind()
		if menubar: self.menubar()
		self.set_title()

		if load_func:
			if custom_func == None: self.main()
			else: custom_func()


	def quit(self):
		cancel = self.prompt_save_changes()
		if cancel: return

		if not any([
			self.updater_win_open,
			]): sys.exit()

	def set_title(self):
		try:
			title = f'{name} {version} - {self.datafile["title"]}'
			if self.savepath: title += f' - {os.path.basename(self.savepath)}'
			if self.modified: title += '*'
			self.window.title(title)
		except: self.window.title(f'{name} {version}')

	# no tab! (sorry keyboard users...)
	@staticmethod
	def disable_all_widgets():
		def set_takefocus_false(widget_class):
			orig_init = widget_class.__init__
			def new_init(self, *args, **kwargs):
				orig_init(self, *args, **kwargs)
				try: self.config(takefocus = False)
				except: pass
			widget_class.__init__ = new_init

		set_takefocus_false(tk.Widget)
		set_takefocus_false(ttk.Widget)

	def main_focus(self, event):
		if event.widget == self.window: self.window.focus()

	def init_window(self):
		self.window.geometry(f'{self.display_w}x{self.display_h}')
		self.window.resizable(False, False)
		self.rebind()
		self.window.option_add('*tearOff', False)
		self.window.protocol('WM_DELETE_WINDOW', self.quit)
		
		self.disable_all_widgets()

		self.set_title()
		icon = 'ico' if os.name == 'nt' else 'xbm'
		try: self.window.iconbitmap(f'{self.temp_path}\\icon.{icon}')
		except tk.TclError:
			err_text = f'Whoops! The icon file "icon.{icon}" is required.\nCan you make sure the file is in "{self.temp_path}"?\n\n{traceback.format_exc()}\nIf this problem persists, please report it here:\nhttps://github.com/{username}/{repo_name}/issues'
			print(err_text)
			tk.messagebox.showerror('Hmmm?', err_text)
			sys.exit()

	def rebind(self):
		for e in self.window.bind(): self.window.unbind(e)
		self.window.bind('<F12>', self.version_details)
		self.window.bind('<1>', self.main_focus)

	def unicode_filter(self, string): return ''.join(['□' if ord(c) > 0xFFFF else c for c in string]) if self.unsupported_tcl else string

	def prompt_save_changes(self):
		if self.modified:
			prompt = tk.messagebox.askyesnocancel('Unsaved changes!', 'Do you want to save changes to the current quiz?', icon = 'warning')
			if prompt == None: return True
			elif prompt: return not self.save_file()

	def new_quiz(self):
		cancel = self.prompt_save_changes()
		if cancel: return

		self.jsonhandler.new_quiz()
		self.datafile = self.jsonhandler.datafile
		self.savepath = self.jsonhandler.savepath
		self.modified = False
		self.message = 'New quiz created!'
		self.config_msg()

	def open_file(self):
		cancel = self.prompt_save_changes()
		if cancel: return

		ok = self.jsonhandler.open_file()
		if ok:
			self.open_file_ex()
			self.refresh(True)

	def open_file_ex(self):
		self.savepath = self.jsonhandler.savepath
		if os.path.splitext(self.savepath)[1].casefold() == '.json': self.datafile_mode = 'json'
		#else: self.datafile_mode = 'qpg'
		else: self.datafile_mode = 'json'
		self.datafile = self.jsonhandler.datafile
		self.modified = False

	def save_file(self):
		if self.savepath:
			with open(self.savepath, 'w', encoding = 'utf-8') as f: f.write(json.dumps(self.datafile, ensure_ascii = False, indent = 4))
			self.message = 'Quiz saved!'
			self.modified = False
			self.config_msg()
			return True
		else:
			self.savepath = ''
			return self.save_file_as()

	def save_file_as(self):
		ok = self.jsonhandler.save_file(self.datafile_mode == 'json')
		if ok:
			self.savepath = self.jsonhandler.savepath
			self.modified = False
		
		self.config_msg()
		return ok

	def reload(self):
		if self.modified:
			confirm = tk.messagebox.askyesno('Reload changes?', 'Are you sure you want to reload this quiz and lose the changes you made in QuizProg-GUI?\n\nThis will take you back to the menu.', icon = 'warning')
			if confirm and self.savepath:
					self.jsonhandler.reload()
					self.modified = False
					self.message = 'Quiz reloaded.'
					self.config_msg()
					self.refresh(True)
			else: return

	def about_menu(self):
		nl = '\n' # workaround for prohibition of backslashes in f-string expression
		tk.messagebox.showinfo(f'About {name}', f'''\
{name} - {version} ({'64' if sys.maxsize > 2**31-1 else '32'}-bit) - Running on {platform.system()} x{'64' if platform.machine().endswith('64') else '86'}
Project page: https://github.com/{username}/{repo_name}
{nl+'WARNING: This is a pre-release version, therefore it may have bugs and/or glitches.'+nl if prerelease else ''}
Licensed under the {license} license

Copyright (c) 2022-2024 GamingWithEvets Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy \
of this software and associated documentation files (the "Software"), to deal \
in the Software without restriction, including without limitation the rights \
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell \
copies of the Software, and to permit persons to whom the Software is \
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all \
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR \
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, \
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE \
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER \
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, \
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE \
SOFTWARE.\
''')

	def version_details(self, event = None):
		if self.debug:
			dnl = '\n\n'
			tk.messagebox.showinfo(f'{name} version details', f'''\
{name} {version}{" (prerelease)" if prerelease else ""}
Internal version: {internal_version}

Python version information:
Python {platform.python_version()} ({'64' if sys.maxsize > 2**31-1 else '32'}-bit)
Tkinter (Tcl/Tk) version {self.window.tk.call('info', 'patchlevel')}{" (most Unicode chars not supported)" if self.unsupported_tcl else ""}

Operating system information:
{platform.system()} {platform.release()}
{'NT version: ' if os.name == 'nt' else ''}{platform.version()}
Architecture: {platform.machine()}{dnl+"Settings file is saved to working directory" if self.save_to_cwd else ""}\
''')

	def disable_debug(self):
		if tk.messagebox.askyesno('Warning', 'To re-enable debug mode you must set the debug flag to True in settings.ini.\nContinue?', icon = 'warning'):
			self.debug = False
			self.save_settings()
			self.menubar() # update the menubar


	def menubar(self):
		menubar = tk.Menu(self.window)

		file_menu = tk.Menu(menubar)
		if not self.player_mode:
			file_menu.add_command(label = 'New quiz', command = self.new_quiz, accelerator = 'Ctrl+N')
			file_menu.add_command(label = 'Open...', command = self.open_file, accelerator = 'Ctrl+O')
			file_menu.add_command(label = 'Save', command = self.save_file, accelerator = 'Ctrl+S')
			self.window.bind('<Control-n>', lambda x: self.new_quiz())
			self.window.bind('<Control-o>', lambda x: self.open_file())
			self.window.bind('<Control-s>', lambda x: self.save_file())
		if (self.player_mode and self.debug) or not self.player_mode:
			file_menu.add_command(label = 'Save as...', command = self.save_file_as, accelerator = 'Ctrl+Shift+S')
			file_menu.add_separator()
			self.window.bind('<Control-Shift-S>', lambda x: self.save_file_as())
		if not self.player_mode:
			file_menu.add_command(label = 'Compile EXE file', command = self.compile_exe.main)
			file_menu.add_separator()
		file_menu.add_command(label = 'Exit', command = self.quit)
		menubar.add_cascade(label = 'File', menu = file_menu)

		if not self.player_mode:
			edit_menu = tk.Menu(menubar)
			edit_menu.add_command(label = 'Reload', command = self.reload)
			menubar.add_cascade(label = 'Edit', menu = edit_menu)

		if not self.player_mode:
			settings_menu = tk.Menu(menubar)
			updater_settings_menu = tk.Menu(settings_menu)
			updater_settings_menu.add_checkbutton(label = 'Check for updates on startup', variable = self.auto_check_updates, command = self.save_settings)
			updater_settings_menu.add_checkbutton(label = 'Check for pre-release versions', variable = self.check_prerelease_version, command = self.save_settings)
			settings_menu.add_cascade(label = 'Updates', menu = updater_settings_menu)

		if self.debug:
			debug_menu = tk.Menu(None if self.player_mode else settings_menu)
			debug_menu.add_command(label = 'Version details', command = self.version_details, accelerator = 'F12')
			debug_menu.add_separator()
			debug_menu.add_command(label = 'Updater test', command = lambda: self.updater_gui.init_window(debug = True))
			debug_menu.add_separator()
			debug_menu.add_command(label = 'Disable debug mode', command = self.disable_debug)
			if self.player_mode: menubar.add_cascade(label = 'Debug', menu = debug_menu)
			else:
				settings_menu.add_separator()
				settings_menu.add_cascade(label = 'Debug', menu = debug_menu)

		if not self.player_mode: menubar.add_cascade(label = 'Settings', menu = settings_menu)

		help_menu = tk.Menu(menubar)
		if not self.player_mode: help_menu.add_command(label = 'Check for updates', command = self.updater_gui.init_window)
		help_menu.add_command(label = f'{"Powered by" if self.player_mode else "About"} {name}', command = self.about_menu)
		menubar.add_cascade(label = 'Help', menu = help_menu)

		self.window.config(menu = menubar)
		
	def config_msg(self):
		if self.msg_label.winfo_exists():
			if self.message_force: self.msg_label.config(text = self.message_force, background = 'red')
			elif self.message: self.msg_label.config(text = self.message, background = 'green')
			else: self.msg_label.config(text = f'QuizProg - GUI edition. Version {version}. © 2024 GamingWithEvets Inc.', background = 'black')
			self.message = self.message_force = None
			Tooltip(self.msg_label, self.msg_label['text'])

	def print_msg(self):
		self.msg_label = ttk.Label(foreground = 'white', anchor = 'center', width = self.display_w)
		self.msg_label.pack()
		self.config_msg()

	"""--------- BEGIN MENUS ---------"""

	def main(self):
		self.set_title()

		self.refresh()
		self.print_msg()

		ttk.Label(text = self.datafile['title'], font = self.bold_font).pack()
		ttk.Label(text = f'--- {len(self.datafile["questions"])} question(s) ---', font = self.bold_font).pack()
		ttk.Label(text = f'Quiz format: {self.datafile_mode.upper()}').pack()
		if self.jsonhandler.check_element('description', rel = False):
			if self.datafile['description']: desc = self.datafile['description']
			else: desc = '(no description)'
		else: desc = '(no description)'
		ttk.Label(text = desc, justify = 'center', font = self.italic_font).pack()

		ttk.Button(text = 'Quiz settings', command = self.quizconf.main).pack(side = 'bottom')
		ttk.Button(text = 'Quiz questions', command = self.question_viewer.main).pack(side = 'bottom')
		ttk.Label().pack(side = 'bottom')
		ttk.Button(text = 'Edit quiz description', command = self.quiz_desc).pack(side = 'bottom')
		ttk.Button(text = 'Rename quiz', command = self.quiz_name).pack(side = 'bottom')
		ttk.Label().pack(side = 'bottom')
		ttk.Button(text = 'Preview quiz', command = self.quiz_player.main).pack(side = 'bottom')

	def format_text(self, text):
		if len(text) > 0:
			text = re.sub(r'\n+', '\n', text)
			if text[-1] == '\n': text = text[:-1]

		return text

	def input_string(self, name, post_func, og = '', allow_blank = True, multiline = True, name2 = None):
		def save(event = None):
			if multiline: text = self.format_text(entry.get('1.0', 'end-1c'))
			else: text = entry.get()
			if text and not text.isspace():
				if text != og:
					self.modified = True
					self.input_string_text = text
				else: self.input_string_skip = True
				post_func()
			else:
				if allow_blank:
					if text != og:
						self.modified = True
						self.input_string_text = text
					else: self.input_string_skip = True
					post_func()
				else: tk.messagebox.showerror('Error', f'{name} cannot be blank!')

		def discard():
			if tk.messagebox.askyesno('Discard', 'Discard changes?', icon = 'warning'):
				self.input_string_skip = True
				post_func()

		self.input_string_text = og
		self.input_string_skip = False

		self.refresh(menubar = False)
		if not name2: name2 = name.lower()
		ttk.Label(text = f'Type your {name2}.').pack()
		ttk.Button(text = 'OK', command = save).pack(side = 'bottom', anchor = 's')
		ttk.Button(text = 'Discard', command = discard).pack(side = 'bottom', anchor = 's')
		
		if multiline:
			scroll = ttk.Scrollbar(orient = 'vertical')
			entry = tk.Text(width = self.display_w, yscrollcommand = scroll.set, wrap = 'word')
			entry.insert('end', og)
			scroll.config(command = entry.yview)
			scroll.pack(side = 'right', fill = 'y')
			entry.focus()
			entry.pack(side = 'left')
		else:
			scroll = ttk.Scrollbar(orient = 'horizontal')
			entry = ttk.Entry(width = self.display_w, xscrollcommand = scroll.set)
			entry.insert(0, og)
			entry.bind('<Return>', save)
			entry.focus()
			entry.pack()
			scroll.config(command = entry.xview)
			scroll.pack(fill = 'x')

	def quiz_name(self):
		def post():
			self.datafile['title'] = self.input_string_text
			if not self.input_string_skip: self.message = 'Quiz name saved!'
			self.main()

		self.input_string('Quiz name', post, self.datafile['title'], False, multiline = False)

	def quiz_desc(self):
		if not self.jsonhandler.check_element('description'): self.datafile['description'] = ''
	
		def post():
			self.datafile['description'] = self.input_string_text
			if not self.input_string_skip: self.message = 'Quiz description saved!'
			self.main()

		self.input_string('Quiz description', post, self.datafile['description'])

	"""----------- END MENUS ---------"""

class CompileEXE:
	def __init__(self, gui):
		self.gui = gui
		self.pyinstaller = None
		self.text = ''

	def compile_exe_head(self):
		self.gui.refresh()
		self.gui.print_msg()

		ttk.Label(text = 'Compile EXE file', font = self.gui.bold_font).pack()
		ttk.Label(text = '''
IMPORTANT!
Due to the nature of PyInstaller, the resulting EXE will only work on your operating system
version onwards.
This is an issue with PyInstaller itself so we cannot do anything about it.
We apologize for any inconvenience caused by this issue.
''', justify = 'center').pack()

	def main(self):
		if hasattr(sys, '_MEIPASS'):
			tk.messagebox.showerror('Error', f'As of this time the Compile EXE feature does not work on binary versions of {name}. We are sorry for this inconvenience.')
			return

		try: self.pyinstaller = importlib.import_module('PyInstaller.__main__')
		except ImportError:
			tk.messagebox.showerror('PyInstaller required', 'The Compile EXE feature needs PyInstaller to function. Please run\n\npip install pyinstaller\n\nin a terminal before using this feature.')
			return

		if self.gui.prompt_save_changes(): return

		self.compile_exe_head()
		self.compile_button = ttk.Button(text = 'Compile', command = self.compile)
		self.compile_button.pack()
		self.quit_button = ttk.Button(text = 'Quit', command = lambda: self.gui.refresh(True))
		self.quit_button.pack(side = 'bottom')

	def compile(self):
		savefilename = tk.filedialog.askdirectory(title = 'Select resulting EXE location', initialdir = os.getcwd())
		if not savefilename: return

		self.compile_button['state'] = 'disabled'
		self.quit_button['state'] = 'disabled'

		progressbar = ttk.Progressbar(mode = 'indeterminate')
		progressbar.pack()
		label = ttk.Label(justify = 'center')
		label.pack()
		
		thread = ThreadWithResult(target = self.compile_thread, args = (savefilename,))
		thread.start()
		while thread.is_alive():
			self.gui.window.update_idletasks()
			label['text'] = self.text
		thread.join()

		progressbar.destroy()
		label.destroy()
		self.compile_button['state'] = 'normal'
		self.quit_button['state'] = 'normal'

		if hasattr(thread, 'result'):
			fname = thread.result
			if type(fname) == tuple: self.gui.window.report_callback_exception(*fname)
			elif fname is not None:
				bs = '\\'
				self.gui.message = f'Compile successful! EXE saved to {fname}'
				self.gui.config_msg()
			else: self.gui.set_message_force('Compilation failed!')
		else: self.gui.set_message_force('Compilation failed!')

	def compile_thread(self, dname):
		pyi_mode = hasattr(sys, '_MEIPASS')
		fname = dname.replace('/', '\\')
		exe_name = f'{self.gui.datafile["title"]}{".exe" if os.name == "nt" else ""}'
		fname += os.sep + exe_name
		tmpdir = f'{self.gui.appdata_folder}/tmp{random.randint(0, 99999):05}'
		qfile = f'quiz.{self.gui.datafile_mode}'

		try:
			self.text = 'Copying necessary files'
			os.makedirs(tmpdir)
			shutil.copy(f'{self.gui.temp_path}/gui.py', tmpdir)
			shutil.copy(f'{self.gui.temp_path}/jsonhandler.py', tmpdir)
			with open(f'{tmpdir}/{qfile}', 'w', encoding = 'utf-8') as f:
				f.write(json.dumps(self.gui.datafile, ensure_ascii = False, indent = 4))
				f.close()
			with open(f'{tmpdir}/main.py', 'w') as f:
				f.write(f'''\
import sys
import tkinter.messagebox
import gui
g = gui.GUI(sys._MEIPASS + '/{qfile}', True)
gui.g = g
try: g.start_main()
except Exception: tk.messagebox.showerror('Error', gui.report_error(*sys.exc_info(), True))
''')
				f.close()
			self.text = 'Invoking PyInstaller\nThis may take a while'
			params = [
			f'{tmpdir}/main.py',
			'-ywFn', self.gui.datafile['title'],
			'--distpath', dname,
			'--workpath', tmpdir,
			'--specpath', tmpdir,
			'--add-data', f'{tmpdir}/{qfile}{";" if os.name == "nt" else ":"}.',
			'--add-data', f'{self.gui.temp_path}/icon{".ico;" if os.name == "nt" else ".xbm:"}.',
			]
			if os.name == 'nt' or platform.system == 'Darwin': params.extend(['-i', f'{self.gui.temp_path}/icon.ico'])
			#if pyi_mode:
			#	retdir = os.getcwd()
			#	os.chdir(sys._MEIPASS)
			try: self.pyinstaller.run(params)
			except SystemExit: pass
			#if pyi_mode: os.chdir(retdir)
			self.text = 'Cleaning up'
			shutil.rmtree(tmpdir)
			if os.path.exists(fname): return fname

		except Exception:
			self.text = 'Cleaning up'
			shutil.rmtree(tmpdir)
			return sys.exc_info()

class QuizPlayer:
	def __init__(self, gui):
		self.gui = gui
		self.question_player = QuestionPlayer(self)

	def main(self):
		if not self.gui.player_mode and self.gui.prompt_save_changes(): return
		self.datafile = self.gui.datafile
		self.menu()

	def menu(self):
		self.gui.refresh()
		self.gui.window.title(self.gui.datafile['title'])

		ttk.Label(text = 'Welcome to').pack()
		ttk.Label(text = self.datafile['title'], font = self.gui.bold_font).pack()
		if self.gui.jsonhandler.check_element('description', rel = False) and self.datafile['description']: ttk.Label(text = self.datafile['description'], justify = 'center').pack()
		
		ttk.Label(text = f'\nPowered by {name} {version}', font = self.gui.italic_font).pack(side = 'bottom')
		ttk.Button(text = 'Quit', command = self.end).pack(side = 'bottom')
		ttk.Button(text = 'Start quiz', command = self.question_player.main).pack(side = 'bottom')

	def end(self):
		if self.gui.player_mode: sys.exit()
		else: self.gui.refresh(True)

class QuestionPlayer:
	def __init__(self, quiz_player):
		self.quiz_player = quiz_player
		self.gui = quiz_player.gui

	def main(self):
		self.datafile = self.gui.datafile
		self.qnum = -1
		self.lives = self.datafile['lives'] if self.gui.jsonhandler.check_element('lives', int) else None
		self.questions = self.datafile['questions'].copy()
		if self.gui.jsonhandler.check_element('randomize', bool) and self.datafile['randomize']: random.shuffle(self.questions)

		self.next_question()

	def next_question(self):
		self.qnum += 1
		if self.qnum == len(self.questions): self.finish()
		else:
			self.question = self.questions[self.qnum]
			self.wrongmsg = ''
			self.display_question()

	def display_question_head(self):
		showcount = self.gui.jsonhandler.check_element('showcount', bool) and self.datafile['showcount']

		self.gui.window.title(f"{self.gui.datafile['title']} - Question {self.qnum+1}{' / '+len(self.questions) if showcount else ''}")
		ttk.Label(text = f'Question {self.qnum + 1}{" / "+len(self.questions) if showcount else ""}', font = self.gui.bold_font).pack()
		if self.lives is not None: ttk.Label(text = f'{self.lives} lives left').pack()

	def display_question(self):
		self.gui.refresh()
		self.display_question_head()

		ttk.Button(text = 'Quit', command = self.end).pack(side = 'bottom')
		ttk.Label().pack(side = 'bottom')

		cd_frame = tk.Frame()
		TooltipButton(cd_frame, text = self.question['c'], width = 41, command = lambda: self.choose_choice('c')).pack(side = 'left')
		TooltipButton(cd_frame, text = self.question['d'], width = 41, command = lambda: self.choose_choice('d')).pack(side = 'right')
		cd_frame.pack(side = 'bottom', fill = 'x')
		ttk.Label(text = 'Hover over a button for full answer', font = self.gui.italic_font).pack(side = 'bottom')

		ab_frame = tk.Frame()
		TooltipButton(ab_frame, text = self.question['a'], width = 41, command = lambda: self.choose_choice('a')).pack(side = 'left')
		TooltipButton(ab_frame, text = self.question['b'], width = 41, command = lambda: self.choose_choice('b')).pack(side = 'right')
		ab_frame.pack(side = 'bottom', fill = 'x')
		ttk.Label().pack(side = 'bottom')
		ttk.Label(text = self.wrongmsg).pack(side = 'bottom')
		ttk.Label().pack(side = 'bottom')

		frame = VerticalScrolledFrame(self.gui.window)
		frame.canvas.config(bg = 'white')
		frame.interior.config(bg = 'white')
		frame.pack(fill = 'both', expand = True)

		question = ttk.Label(frame.interior, text = self.question['question'], background = 'white', justify = 'center')
		question.bind('<Configure>', lambda e: e.widget.config(wraplength=e.widget.winfo_width()))
		question.pack()
		ttk.Label(frame.interior, background = 'white').pack()

	def choice_correct(self, choice):
		if self.question['correct'] == 'all': return True
		else: return self.question['correct'] == choice

	def choose_choice(self, choice):
		if self.choice_correct(choice): self.correct()
		else:
			if self.gui.jsonhandler.check_question_element('wrongmsg', self.qnum, dict) and choice in self.question['wrongmsg']: self.wrongmsg = self.question['wrongmsg'][choice]
			elif self.gui.jsonhandler.check_element('wrongmsg', list): self.wrongmsg = random.choice(self.datafile['wrongmsg'])
			else: self.wrongmsg = f'Choice {choice.upper()} is incorrect!{" You lost a life!" if self.lives is not None else ""}'
			if self.lives is not None:
				self.lives -= 1
				if not self.lives: self.fail()
				else: self.display_question()
			else: self.display_question()

	def correct(self):
		if self.gui.jsonhandler.check_question_element('explanation', self.qnum, str):
			self.gui.refresh()
			self.display_question_head()

			ttk.Button(text = 'Next', command = self.next_question).pack(side = 'bottom')
			ttk.Label().pack(side = 'bottom')

			ttk.Label(text = '\nCorrect!', justify = 'center', font = self.gui.italic_font).pack()

			frame = VerticalScrolledFrame(self.gui.window)
			frame.canvas.config(bg = 'white')
			frame.interior.config(bg = 'white')
			frame.pack(fill = 'both', expand = True)

			question = ttk.Label(frame.interior, text = self.question['explanation'], background = 'white', justify = 'center')
			question.bind('<Configure>', lambda e: e.widget.config(wraplength=e.widget.winfo_width()))
			question.pack()
			ttk.Label(frame.interior, background = 'white').pack()
		else: self.next_question()

	def finish(self):
		self.gui.refresh()
		self.gui.window.title(self.gui.datafile['title'])

		ttk.Button(text = 'Return to menu', command = self.quiz_player.menu).pack(side = 'bottom')
		ttk.Label().pack(side = 'bottom')

		ttk.Label(text = 'Quiz completed!', justify = 'center', font = self.gui.bold_font).pack()

		if self.gui.jsonhandler.check_element('finish', str):
			frame = VerticalScrolledFrame(self.gui.window)
			frame.canvas.config(bg = 'white')
			frame.interior.config(bg = 'white')
			frame.pack(fill = 'both', expand = True)

			question = ttk.Label(frame.interior, text = self.datafile['finish'], background = 'white', justify = 'center')
			question.bind('<Configure>', lambda e: e.widget.config(wraplength=e.widget.winfo_width()))
			question.pack()
			ttk.Label(frame.interior, background = 'white').pack()

	def fail(self):
		self.gui.refresh()

		ttk.Button(text = 'Return to menu', command = self.quiz_player.menu).pack(side = 'bottom')
		ttk.Button(text = 'Try again!', command = self.main).pack(side = 'bottom')
		ttk.Label().pack(side = 'bottom')

		ttk.Label(text = 'Game Over', justify = 'center', font = self.gui.bold_font).pack()

		if self.gui.jsonhandler.check_element('fail', str):
			frame = VerticalScrolledFrame(self.gui.window)
			frame.canvas.config(bg = 'white')
			frame.interior.config(bg = 'white')
			frame.pack(fill = 'both', expand = True)

			question = ttk.Label(frame.interior, text = self.datafile['fail'], background = 'white', justify = 'center')
			question.bind('<Configure>', lambda e: e.widget.config(wraplength=e.widget.winfo_width()))
			question.pack()
			ttk.Label(frame.interior, background = 'white').pack()

	def end(self):
		if tk.messagebox.askyesno('Quit the quiz?', 'Are you sure you want to quit this quiz?', icon = 'warning'): self.quiz_player.menu()

class QuizConf:
	def __init__(self, gui):
		self.gui = gui
		self.wrongmsg_editor = WrongMsgEditor(self)

		self.is_editing = False

	def main(self):
		self.datafile = self.gui.datafile

		if not self.gui.jsonhandler.check_element('lives', int): self.datafile['lives'] = 0
		if not self.gui.jsonhandler.check_element('randomize', bool): self.datafile['randomize'] = False
		if not self.gui.jsonhandler.check_element('showcount', bool): self.datafile['showcount'] = True
		if not self.gui.jsonhandler.check_element('wrongmsg', list): self.datafile['wrongmsg'] = []
		if not self.gui.jsonhandler.check_element('fail'): self.datafile['fail'] = ''
		if not self.gui.jsonhandler.check_element('finish'): self.datafile['finish'] = ''

		self.wrongmsg_list = self.datafile['wrongmsg']
		self.fail_text = self.datafile['fail']
		self.finish_text = self.datafile['finish']

		self.menu()

	def menu(self):
		self.is_editing = False
		
		self.gui.refresh()
		self.gui.print_msg()

		ttk.Label(text = 'Quiz settings', font = self.gui.bold_font).pack()
		ttk.Button(text = 'OK', command = self.end).pack(side = 'bottom')
		ttk.Button(text = 'Reset to defaults', command = self.reset).pack(side = 'bottom')

		life_check = self.gui.window.register(self.check_lives)

		life_frame = FocusFrame()
		ttk.Label(life_frame, text = f'Lives (0 = disabled)').pack(side = 'left')
		self.life_entry = ttk.Entry(life_frame, width = 10, justify = 'right', validate = 'all', validatecommand = (life_check, '%s', '%P', '%V'))
		self.life_entry.insert(0, str(self.datafile['lives']))
		self.life_entry.pack(side = 'right')
		life_frame.pack(fill = 'x')

		rand_frame = FocusFrame()
		ttk.Label(rand_frame, text = f'Randomize question order').pack(side = 'left')
		self.rand_value = tk.BooleanVar()
		self.rand_value.set(self.datafile['randomize'])
		rand_checkbox = ttk.Checkbutton(rand_frame, variable = self.rand_value, command = self.autosave)
		rand_checkbox.pack(side = 'right')
		rand_frame.pack(fill = 'x')

		showcount_frame = FocusFrame()
		ttk.Label(showcount_frame, text = f'Show question count').pack(side = 'left')
		self.showcount_value = tk.BooleanVar()
		self.showcount_value.set(self.datafile['showcount'])
		showcount_checkbox = ttk.Checkbutton(showcount_frame, variable = self.showcount_value, command = self.autosave)
		showcount_checkbox.pack(side = 'right')
		showcount_frame.pack(fill = 'x')

		wrongmsg_frame = FocusFrame()
		ttk.Label(wrongmsg_frame, text = f'Global wrong answer comments').pack(side = 'left')
		ttk.Button(wrongmsg_frame, text = 'Edit', command = self.wrongmsg_editor.main).pack(side = 'right')
		if len(self.datafile['wrongmsg']) == 0: ttk.Label(text = 'None  ', master = wrongmsg_frame).pack(side = 'right')
		else: ttk.Label(text = f'{len(self.datafile["wrongmsg"])} comment{"s" if len(self.datafile["wrongmsg"]) > 1 else ""}  ', master = wrongmsg_frame).pack(side = 'right')
		wrongmsg_frame.pack(fill = 'x')

		fail_frame = FocusFrame()
		ttk.Label(fail_frame, text = f'Game over comment (requires lives enabled)').pack(side = 'left')
		ttk.Button(fail_frame, text = 'Edit', command = self.fail_edit).pack(side = 'right')
		fail_frame.pack(fill = 'x')

		win_frame = FocusFrame()
		ttk.Label(win_frame, text = f'Quiz completion comment').pack(side = 'left')
		ttk.Button(win_frame, text = 'Edit', command = self.finish_edit).pack(side = 'right')
		win_frame.pack(fill = 'x')

		self.is_editing = True

	def fail_edit(self):
		def post():
			self.fail_text = self.gui.input_string_text
			if not self.gui.input_string_skip: self.gui.message = 'Game over comment saved!'
			self.menu()

		self.gui.input_string('quiz game over comment', post, self.fail_text)

	def finish_edit(self):
		def post():
			self.finish_text = self.gui.input_string_text
			if not self.gui.input_string_skip: self.gui.message = 'Completion comment saved!'
			self.menu()

		self.gui.input_string('quiz completion comment', post, self.finish_text)

	def check_lives(self, old_input, new_input, validate_type):
		if validate_type == 'key':
			if new_input.isnumeric(): return True
			else:
				if not new_input: return True
				else: return False
		elif validate_type == 'focusout':
			if not old_input: self.life_entry.insert(0, '0')
			if self.is_editing: self.autosave()
			return True
		else: return True

	def autosave(self):
		self.datafile['lives'] = int(self.life_entry.get())
		self.gui.modified = True

		randval = self.rand_value.get()
		if randval != self.datafile['randomize']:
			self.datafile['randomize'] = randval
			self.gui.modified = True

		scval = self.showcount_value.get()
		if scval != self.datafile['showcount']:
			self.datafile['showcount'] = scval
			self.gui.modified = True
		
		self.gui.set_title()

	def reset(self):
		del self.datafile['lives']
		del self.datafile['randomize']
		del self.datafile['showcount']
		del self.datafile['wrongmsg']
		del self.datafile['fail']
		del self.datafile['finish']
		self.main()

	def end(self):
		if self.datafile['lives'] == 0: del self.datafile['lives']
		if not self.datafile['randomize']: del self.datafile['randomize']
		if self.datafile['showcount']: del self.datafile['showcount']
		if self.datafile['wrongmsg'] == []: del self.datafile['wrongmsg']
		if self.datafile['fail'] == '': del self.datafile['fail']
		if self.datafile['finish'] == '': del self.datafile['finish']

		self.gui.datafile = self.datafile
		self.gui.refresh(True)

class WrongMsgEditor:
	def __init__(self, quizconf):
		self.quizconf = quizconf
		self.gui = quizconf.gui

	def main(self):
		self.wrongmsg = self.quizconf.wrongmsg_list
		self.index = 0

		self.menu()

	def navigation_prev(self, e = None):
		if self.index > 0:
			self.index -= 1
			self.menu()
	def navigation_next(self, e = None):
		if self.index < len(self.wrongmsg) - 1:
			self.index += 1
			self.menu()

	def navigation_prev_jmp(self):
		self.index = 0
		self.menu()
	def navigation_next_jmp(self):
		self.index = len(self.wrongmsg) - 1
		self.menu()

	def menu(self):
		self.gui.refresh()
		self.gui.print_msg()

		self.gui.window.bind('<Left>', self.navigation_prev)
		self.gui.window.bind('<Right>', self.navigation_next)

		ttk.Label(text = 'Global wrong answer comments', font = self.gui.bold_font).pack()
		ttk.Button(text = 'Back', command = self.end).pack(side = 'bottom')
		ttk.Label().pack(side = 'bottom')

		delbutton = ttk.Button(text = 'Delete comment', command = self.delete); delbutton.pack(side = 'bottom')
		editbutton = ttk.Button(text = 'Edit comment', command = self.edit); editbutton.pack(side = 'bottom')
		ttk.Button(text = 'Create new comment', command = self.new).pack(side = 'bottom')
		if len(self.wrongmsg) == 0:
			ttk.Label(text = 'No global wrong answer comments!').pack()
			editbutton.config(state = 'disabled')
			delbutton.config(state = 'disabled')
		else:
			ttk.Label(text = f'{self.index + 1} / {len(self.wrongmsg)}').pack()
			ttk.Label().pack(side = 'bottom')
			nav_frame = FocusFrame()
			nav_frame.pack(side = 'bottom', fill = 'x')
			prev_jmp_bt = ttk.Button(nav_frame, text = '<<', width = 3, command = self.navigation_prev_jmp)
			prev_bt = ttk.Button(nav_frame, text = '< Previous', command = self.navigation_prev)
			next_bt = ttk.Button(nav_frame, text = 'Next >', command = self.navigation_next)
			next_jmp_bt = ttk.Button(nav_frame, text = '>>', width = 3, command = self.navigation_next_jmp)
			if len(self.wrongmsg) > 1:
				if self.index == 0:
					prev_bt.config(state = 'disabled')
					prev_jmp_bt.config(state = 'disabled')
				elif self.index == len(self.wrongmsg) - 1:
					next_bt.config(state = 'disabled')
					next_jmp_bt.config(state = 'disabled')
			else:
				prev_jmp_bt.config(state = 'disabled')
				prev_bt.config(state = 'disabled')
				next_bt.config(state = 'disabled')
				next_jmp_bt.config(state = 'disabled')
			prev_jmp_bt.pack(side = 'left'); prev_bt.pack(side = 'left')
			next_jmp_bt.pack(side = 'right'); next_bt.pack(side = 'right')

			scroll = ttk.Scrollbar(orient = 'vertical')
			text = tk.Text(width = self.gui.display_w, yscrollcommand = scroll.set, wrap = 'word')
			text.insert('end', self.wrongmsg[self.index])
			text.bind('<Key>', self.romsg)
			scroll.config(command = text.yview)
			scroll.pack(side = 'right', fill = 'y')
			text.pack(side = 'left')

	def romsg(self, event = None):
		tk.messagebox.showinfo('Text read-only', 'To edit this text, click "Edit comment".\nThank you!')
		return 'break'

	def new(self):
		def post():
			if not self.gui.input_string_skip: 
				self.wrongmsg.append(self.gui.input_string_text)
				self.index = len(self.wrongmsg) - 1
				self.gui.message = 'Global wrong answer comment created!'
			self.menu()

		self.gui.input_string('Global wrong answer comment', post, allow_blank = False)

	def edit(self):
		def post():
			if not self.gui.input_string_skip: 
				self.wrongmsg[self.index] = self.gui.input_string_text
				self.gui.message = 'Global wrong answer comment saved!'
			self.menu()

		self.gui.input_string('global wrong answer comment', post, self.wrongmsg[self.index])

	def delete(self):
		if tk.messagebox.askyesno('Delete this comment?', 'Are you sure you want to delete this comment?', icon = 'warning'):
			del self.wrongmsg[self.index]
			if len(self.wrongmsg) > 0:
				if self.index > 0: self.index -= 1
			else: self.index = 0
			self.gui.modified = True
			self.gui.message = 'Global wrong answer comment deleted.'
			self.menu()

	def end(self):
		self.quizconf.wrongmsg_list = self.wrongmsg
		self.quizconf.menu()

class QuestionViewer:
	def __init__(self, gui):
		self.gui = gui
		self.qeditor = QuestionEditor(self)

	def main(self):
		self.gui.refresh()
		self.gui.print_msg()
		ttk.Label(text = 'Questions', font = self.gui.bold_font).pack()
		ttk.Label(text = 'Please wait... this may take a while for large quizzes.').pack()
		self.gui.window.update()

		self.questions = self.gui.datafile['questions']
		self.index = 0
		
		self.menu()

	def navigation_prev(self, e = None):
		if self.index > 0:
			self.index -= 1
			self.menu()
	def navigation_next(self, e = None):
		if self.index < len(self.questions) - 1: 
			self.index += 1
			self.menu()

	def navigation_prev_jmp(self):
		self.index = 0
		self.menu()
	def navigation_next_jmp(self):
		self.index = len(self.questions) - 1
		self.menu()

	def menu(self):
		self.gui.refresh()
		self.gui.print_msg()

		self.gui.window.bind('<Left>', self.navigation_prev)
		self.gui.window.bind('<Right>', self.navigation_next)

		ttk.Label(text = 'Questions', font = self.gui.bold_font).pack()
		ttk.Button(text = 'Back', command = self.end).pack(side = 'bottom')
		ttk.Label().pack(side = 'bottom')

		ttk.Label(text = f'{self.index + 1} / {len(self.questions)}').pack()
		ttk.Button(text = 'Delete question', command = self.delete, state = 'normal' if len(self.questions) > 1 else 'disabled').pack(side = 'bottom')
		ttk.Button(text = 'Edit question', command = self.qeditor.main).pack(side = 'bottom')
		ttk.Button(text = 'Create new question', command = self.new).pack(side = 'bottom')
		ttk.Label().pack(side = 'bottom')
		nav_frame = FocusFrame()
		nav_frame.pack(side = 'bottom', fill = 'x')
		prev_jmp_bt = ttk.Button(nav_frame, text = '<<', width = 3, command = self.navigation_prev_jmp)
		prev_bt = ttk.Button(nav_frame, text = '< Previous', command = self.navigation_prev)
		next_bt = ttk.Button(nav_frame, text = 'Next >', command = self.navigation_next)
		next_jmp_bt = ttk.Button(nav_frame, text = '>>', width = 3, command = self.navigation_next_jmp)
		if len(self.questions) > 1:
			if self.index == 0:
				prev_bt.config(state = 'disabled')
				prev_jmp_bt.config(state = 'disabled')
			elif self.index == len(self.questions) - 1:
				next_bt.config(state = 'disabled')
				next_jmp_bt.config(state = 'disabled')
		else:
			prev_jmp_bt.config(state = 'disabled')
			prev_bt.config(state = 'disabled')
			next_bt.config(state = 'disabled')
			next_jmp_bt.config(state = 'disabled')
		prev_jmp_bt.pack(side = 'left'); prev_bt.pack(side = 'left')
		next_jmp_bt.pack(side = 'right'); next_bt.pack(side = 'right')


		frame = VerticalScrolledFrame(self.gui.window)
		frame.canvas.config(bg = 'white')
		frame.interior.config(bg = 'white')
		frame.pack(fill = 'both', expand = True)

		question = ttk.Label(frame.interior, text = self.questions[self.index]['question'], background = 'white', justify = 'center')
		question.bind('<Configure>', lambda e: e.widget.config(wraplength=e.widget.winfo_width()))
		question.pack()
		ttk.Label(frame.interior, background = 'white').pack()
		for opt in ('a', 'b', 'c', 'd'):
			opt_frame = FocusFrame(frame.interior, bg = 'white'); opt_frame.pack()
			ttk.Label(opt_frame, text = f'[{opt.upper()}]', font = self.gui.bold_font if self.questions[self.index]['correct'] in [opt, 'all'] else None, background = 'white').pack(side = 'left')
			opt_txt = ttk.Label(opt_frame, text = self.questions[self.index][opt], background = 'white')
			opt_txt.bind('<Configure>', lambda e: e.widget.config(wraplength=e.widget.winfo_width()))
			opt_txt.pack(side = 'right')

	def new(self):
		self.questions.append({'question': 'Question', 'a': 'Answer A', 'b': 'Answer B', 'c': 'Answer C', 'd': 'Answer D', 'correct': 'a'})
		self.gui.modified = True
		self.index = len(self.questions) - 1
		self.gui.message = 'Question created!'
		self.menu()

	def delete(self):
		if tk.messagebox.askyesno('Delete this question?', 'Are you sure you want to delete this question?', icon = 'warning'):
			del self.questions[self.index]
			if len(self.questions) > 0:
				if self.index > 0: self.index -= 1
			else: self.index = 0
			self.gui.modified = True
			self.gui.message = 'Question deleted.'
			self.menu()

	def end(self):
		self.gui.datafile['questions'] = self.questions
		self.gui.refresh(True)

class QuestionEditor:
	def __init__(self, qviewer):
		self.qviewer = qviewer
		self.gui = qviewer.gui
		self.qwrongmsg_editor = QWrongMsgEditor(self)

	def main(self):
		self.qno = self.qviewer.index
		self.question = self.qviewer.questions[self.qno]
		self.qlen = len(self.qviewer.questions)

		self.correct_svar = tk.StringVar(); self.correct_svar.set(self.question['correct'].upper())
		if self.correct_svar.get() == 'ALL': self.correct_svar.set('All answers')

		if not self.gui.jsonhandler.check_question_element('wrongmsg', self.qno, dict): self.question['wrongmsg'] = {}
		if not self.gui.jsonhandler.check_question_element('explanation', self.qno): self.question['explanation'] = ''

		self.menu()

	def menu(self):
		self.gui.refresh()
		self.gui.print_msg()

		editing_text = FocusFrame(); editing_text.pack()
		ttk.Label(editing_text, text = f'Editing', font = self.gui.bold_font).pack(side = 'left')
		ttk.Label(editing_text, text = f'Question {self.qno + 1}/{self.qlen}').pack(side = 'right')
		ttk.Button(text = 'OK', command = self.end).pack(side = 'bottom')

		question_frame = FocusFrame()
		ttk.Label(question_frame, text = 'Question').pack(side = 'left')
		test = ttk.Button(question_frame, text = 'Edit', command = self.ques).pack(side = 'right')
		question_frame.pack(fill = 'x')

		a_frame = FocusFrame()
		ttk.Label(a_frame, text = 'Answer A').pack(side = 'left')
		ttk.Button(a_frame, text = 'Edit', command = self.ans_a).pack(side = 'right')
		a_frame.pack(fill = 'x')

		b_frame = FocusFrame()
		ttk.Label(b_frame, text = 'Answer B').pack(side = 'left')
		ttk.Button(b_frame, text = 'Edit', command = self.ans_b).pack(side = 'right')
		b_frame.pack(fill = 'x')

		c_frame = FocusFrame()
		ttk.Label(c_frame, text = 'Answer C').pack(side = 'left')
		ttk.Button(c_frame, text = 'Edit', command = self.ans_c).pack(side = 'right')
		c_frame.pack(fill = 'x')

		d_frame = FocusFrame()
		ttk.Label(d_frame, text = 'Answer D').pack(side = 'left')
		ttk.Button(d_frame, text = 'Edit', command = self.ans_d).pack(side = 'right')
		d_frame.pack(fill = 'x')

		correct_frame = FocusFrame()
		ttk.Label(correct_frame, text = 'Correct answer').pack(side = 'left')
		correct_cbox = ttk.Combobox(correct_frame, textvariable = self.correct_svar, values = ('A', 'B', 'C', 'D', 'All answers'))
		correct_cbox.bind('<<ComboboxSelected>>', self.process_correct)
		correct_cbox.pack(side = 'right')
		correct_frame.pack(fill = 'x')

		wrongmsg_frame = FocusFrame()
		ttk.Label(wrongmsg_frame, text = 'Wrong answer comments').pack(side = 'left')
		ttk.Button(wrongmsg_frame, text = 'Edit', command = self.qwrongmsg_editor.main).pack(side = 'right')
		wrongmsg_frame.pack(fill = 'x')

		explanation_frame = FocusFrame()
		ttk.Label(explanation_frame, text = 'Explanation').pack(side = 'left')
		ttk.Button(explanation_frame, text = 'Edit', command = self.explanation).pack(side = 'right')
		explanation_frame.pack(fill = 'x')
	
	def ques(self):
		def post():
			self.question['question'] = self.gui.input_string_text
			if not self.gui.input_string_skip: self.gui.message = 'Question saved!'
			self.menu()

		self.gui.input_string('question', post, self.question['question'], False)

	def ans_a(self):
		def post():
			self.question['a'] = self.gui.input_string_text
			if not self.gui.input_string_skip: self.gui.message = 'Answer A saved!'
			self.menu()

		self.gui.input_string('answer to choice A', post, self.question['a'], False)

	def ans_b(self):
		def post():
			self.question['b'] = self.gui.input_string_text
			if not self.gui.input_string_skip: self.gui.message = 'Answer B saved!'
			self.menu()

		self.gui.input_string('answer to choice B', post, self.question['b'], False)

	def ans_c(self):
		def post():
			self.question['c'] = self.gui.input_string_text
			if not self.gui.input_string_skip: self.gui.message = 'Answer C saved!'
			self.menu()

		self.gui.input_string('answer to choice C', post, self.question['c'], False)

	def ans_d(self):
		def post():
			self.question['d'] = self.gui.input_string_text
			if not self.gui.input_string_skip: self.gui.message = 'Answer D saved!'
			self.menu()

		self.gui.input_string('answer to choice D', post, self.question['d'], False)

	def process_correct(self, event = None):
		correct_old = self.question['correct']

		if self.correct_svar.get() == 'All answers': self.question['correct'] = 'all'
		else: self.question['correct'] = self.correct_svar.get().lower()

		if self.question['correct'] != correct_old:
			self.gui.modified = True
			self.gui.set_title()

	def explanation(self):
		def post():
			self.question['explanation'] = self.gui.input_string_text
			if not self.gui.input_string_skip: self.gui.message = 'Explanation saved!'
			self.menu()

		self.gui.input_string('question explanation', post, self.question['explanation'])

	def end(self):
		if not self.question['wrongmsg']: del self.question['wrongmsg']
		if not self.question['explanation']: del self.question['explanation']

		self.qviewer.questions[self.qviewer.index] = self.question
		self.qviewer.menu()

class QWrongMsgEditor:
	def __init__(self, qeditor):
		self.qeditor = qeditor
		self.gui = qeditor.gui

		self.index_letters = ('a', 'b', 'c', 'd')

	def main(self):
		self.wrongmsg = self.qeditor.question['wrongmsg']
		self.index = 0

		self.menu()

	def navigation_prev(self, e = None):
		while self.index > 0:
			self.index -= 1
			if self.index_letters[self.index] in self.wrongmsg: break
		self.menu()
	def navigation_next(self, e = None):
		while self.index < 3:
			self.index += 1
			if self.index_letters[self.index] in self.wrongmsg: break
		self.menu()

	def menu(self):
		self.gui.refresh()
		self.gui.print_msg()

		self.gui.window.bind('<Left>', self.navigation_prev)
		self.gui.window.bind('<Right>', self.navigation_next)

		editing_text = FocusFrame(); editing_text.pack()
		ttk.Label(editing_text, text = f'Wrong answer comments ', font = self.gui.bold_font).pack(side = 'left')
		ttk.Label(editing_text, text = f' Question {self.qeditor.qno + 1}/{self.qeditor.qlen}').pack(side = 'right')
		ttk.Button(text = 'Back', command = self.end).pack(side = 'bottom')
		ttk.Label().pack(side = 'bottom')

		delbutton = ttk.Button(text = 'Delete comment', command = self.delete); delbutton.pack(side = 'bottom')
		editbutton = ttk.Button(text = 'Edit comment', command = self.edit); editbutton.pack(side = 'bottom')
		createbutton = ttk.Button(text = 'Create new comment', command = self.new, state = 'disabled' if len(self.wrongmsg) > 3 else 'normal').pack(side = 'bottom')
		if len(self.wrongmsg) == 0:
			ttk.Label(text = 'No wrong answer comments!').pack()
			editbutton.config(state = 'disabled')
			delbutton.config(state = 'disabled')
		else:
			while True:
				if self.index_letters[self.index] in self.wrongmsg: break
				else: self.index += 1

			self.choice_letter = self.index_letters[self.index]
			ttk.Label(text = f'Message for choice {self.choice_letter.upper()}').pack()
			ttk.Label().pack(side = 'bottom')
			nav_frame = FocusFrame()
			nav_frame.pack(side = 'bottom', fill = 'x')
			prev_bt = ttk.Button(nav_frame, text = '< Previous', command = self.navigation_prev)
			next_bt = ttk.Button(nav_frame, text = 'Next >', command = self.navigation_next)
			if len(self.wrongmsg) > 1:
				keys = tuple(self.wrongmsg.keys())
				if self.index == self.index_letters.index(keys[0]): prev_bt.config(state = 'disabled')
				elif self.index == self.index_letters.index(keys[-1]): next_bt.config(state = 'disabled')
			else: prev_bt.config(state = 'disabled'); next_bt.config(state = 'disabled')
			prev_bt.pack(side = 'left'); next_bt.pack(side = 'right')

			scroll = ttk.Scrollbar(orient = 'vertical')
			text = tk.Text(width = self.gui.display_w, yscrollcommand = scroll.set, wrap = 'word')
			text.insert('end', self.wrongmsg[self.choice_letter])
			text.bind('<Key>', self.romsg)
			scroll.config(command = text.yview)
			scroll.pack(side = 'right', fill = 'y')
			text.pack(side = 'left')

	def romsg(self, event = None):
		tk.messagebox.showinfo('Text read-only', 'To edit this text, click "Edit comment".\nThank you!')
		return 'break'

	def new(self):
		c = ''

		def post():
			if not self.gui.input_string_skip: 
				self.wrongmsg[c] = self.gui.input_string_text
				self.index = self.index_letters.index(c)
				self.gui.message = f'Choice {c.upper()} wrong answer comment created!'
			self.menu()

		def create(choice):
			nonlocal c
			c = choice
			string = f'rong answer comment for choice {c.upper()}'
			self.gui.input_string(f'W{string}', post, allow_blank = False, name2 = f'w{string}')

		self.gui.refresh()
		self.gui.print_msg()

		ttk.Label(text = 'Create new comment', font = self.gui.bold_font).pack()
		ttk.Label(text = 'Please choose a choice letter:').pack()
		ttk.Button(text = 'Back', command = self.menu).pack(side = 'bottom')

		letters = FocusFrame(); letters.pack()
		ttk.Button(letters, text = 'A', command = lambda: create('a'), state = 'disabled' if 'a' in self.wrongmsg else 'normal').pack()
		ttk.Button(letters, text = 'B', command = lambda: create('b'), state = 'disabled' if 'b' in self.wrongmsg else 'normal').pack()
		ttk.Button(letters, text = 'C', command = lambda: create('c'), state = 'disabled' if 'c' in self.wrongmsg else 'normal').pack()
		ttk.Button(letters, text = 'D', command = lambda: create('d'), state = 'disabled' if 'd' in self.wrongmsg else 'normal').pack()

	def edit(self):
		def post():
			if not self.gui.input_string_skip: 
				self.wrongmsg[self.choice_letter] = self.gui.input_string_text
				self.gui.message = f'Choice {self.choice_letter.upper()} wrong answer comment saved!'
			self.menu()

		string = f'rong answer comment for choice {self.choice_letter.upper()}'
		self.gui.input_string(f'W{string}', post, self.wrongmsg[self.choice_letter], False, name2 = f'w{string}')

	def delete(self):
		if tk.messagebox.askyesno('Delete this comment?', 'Are you sure you want to delete this comment?', icon = 'warning'):
			del self.wrongmsg[self.choice_letter]
			if len(self.wrongmsg) > 0:
				if self.index > self.index_letters.index(tuple(self.wrongmsg.keys())[0]):
					while True:
						self.index -= 1
						if self.index_letters[self.index] in self.wrongmsg: break
			else: self.index = 0
			self.gui.modified = True
			self.gui.message = 'Wrong answer comment deleted.'
			self.menu()

	def end(self):
		self.qeditor.question['wrongmsg'] = self.wrongmsg
		self.qeditor.menu()

class UpdaterGUI:
	def __init__(self, gui):
		self.gui = gui

		self.auto = False
		self.after_ms = 100

		self.updater = Updater()

	def init_window(self, auto = False, auto_download_options = None, debug = False):
		if not self.gui.updater_win_open:
			self.gui.updater_win_open = True

			self.auto = auto
			self.debug = debug

			self.win = tk.Toplevel(self.gui.window)

			self.win.geometry('400x400')
			self.win.resizable(False, False)
			self.win.protocol('WM_DELETE_WINDOW', self.quit)
			self.win.title('Updater')

			icon = 'ico' if os.name == 'nt' else 'xbm'
			try: self.win.iconbitmap(f'{self.gui.temp_path}\\icon.{icon}')
			except tk.TclError:
				err_text = f'Whoops! The icon file "icon.{icon}" is required.\nCan you make sure the file is in "{self.gui.temp_path}"?\n\n{traceback.format_exc()}\nIf this problem persists, please report it here:\nhttps://github.com/{username}/{repo_name}/issues'
				print(err_text)
				tk.messagebox.showerror('Hmmm?', err_text)
				self.quit()

			self.win.focus()
			self.win.grab_set()
			if self.debug: self.debug_menu()
			elif self.auto:
				self.win.after(0, lambda: self.draw_download_msg(*auto_download_options))
			else: self.main()

	def quit(self):
		self.win.grab_release()
		self.win.destroy()
		self.auto = False
		self.gui.updater_win_open = False
		if self.auto:
			self.auto = False
			self.gui.main()

	def main(self):
		self.update_thread = ThreadWithResult(target = self.updater.check_updates, args = (self.gui.check_prerelease_version.get(),))

		self.draw_check()
		self.win.after(1, self.start_thread)
		self.win.mainloop()

	def debug_menu(self):
		ttk.Button(self.win, text = 'Check updates', command = self.main).pack()
		ttk.Button(self.win, text = 'Message test', command = lambda: self.draw_msg('Updater message test.\nLine 2\nLine 3\nLine 4')).pack()
		ttk.Button(self.win, text = 'New update screen test', command = lambda: self.draw_download_msg('testbuild69', None, False, '''\
Hello! **This is a *test* of the updater\'s Markdown viewer**, made possible with the [Markdown](https://pypi.org/project/Markdown/), [`mdformat`](https://pypi.org/project/mdformat/), and [TkinterWeb](https://pypi.org/project/tkinterweb/) modules.

By the way, [here\'s the GitHub repository](../../) if you want to check it out. And here\'s [TkTemplate](../../../tktemplate) which is a Tkinter template based on RBEditor.

While you\'re here, why don\'t you check out my [Discord server](//gamingwithevets.github.io/redirector/discord)? It\'s pretty empty here, and I\'d really appreciate it if you could join.\
''')).pack()
		ttk.Button(self.win, text = 'Quit', command = self.quit).pack(side = 'bottom')

	def start_thread(self):
		self.update_thread.start()
		while self.update_thread.is_alive():
			self.win.update_idletasks()
			self.progressbar['value'] = self.updater.progress
		self.progressbar['value'] = 100
		self.update_thread.join()
		update_info = self.update_thread.result

		if update_info['error']:
			if update_info['exceeded']: self.draw_msg('GitHub API rate limit exceeded! Please try again later.')
			elif update_info['nowifi']: self.draw_msg('Unable to connect to the internet. Please try again\nwhen you have a stable internet connection.')
			else: self.draw_msg('Unable to check for updates! Please try again later.')
		elif update_info['newupdate']: self.draw_download_msg(update_info['title'], update_info['tag'], update_info['prerelease'], update_info['body'])
		else: self.draw_msg('You are already using the latest version.')

	def draw_check(self):
		for w in self.win.winfo_children(): w.destroy()

		ttk.Label(self.win, text = 'Checking for updates...').pack()
		self.progressbar = ttk.Progressbar(self.win, orient = 'horizontal', length = 100, mode = 'determinate')
		self.progressbar.pack()
		ttk.Label(self.win, text = 'DO NOT close the program\nwhile checking for updates', font = self.gui.bold_font).pack(side = 'bottom')

	def draw_msg(self, msg):
		if self.auto:
			self.gui.set_title()
			self.quit()
		else:
			for w in self.win.winfo_children(): w.destroy()
			ttk.Label(self.win, text = msg, justify = 'center').pack()
			ttk.Button(self.win, text = 'Back', command = self.quit).pack(side = 'bottom')

	@staticmethod
	def package_installed(package):
		try: pkg_resources.get_distribution(package)
		except pkg_resources.DistributionNotFound: return False

		return True

	def draw_download_msg(self, title, tag, prever, body):
		if self.auto:
			self.win.deiconify()
			self.gui.set_title()
		for w in self.win.winfo_children(): w.destroy()
		ttk.Label(self.win, text = f'''\
An update is available!
Current version: {self.gui.version}{' (prerelease)' if prerelease else ''}
New version: {title}{' (prerelease)' if prerelease else ''}\
''', justify = 'center').pack()
		ttk.Button(self.win, text = 'Cancel', command = self.quit).pack(side = 'bottom')
		ttk.Button(self.win, text = 'Visit download page', command = lambda: self.open_download(tag), state = 'disabled' if tag is None else 'normal').pack(side = 'bottom')
		
		ttk.Label(self.win).pack()

		packages_missing = []
		for package in ('markdown', 'mdformat-gfm', 'tkinterweb'):
			if not self.package_installed(package): packages_missing.append(package)

		if packages_missing: ttk.Label(self.win, text = f'Missing package(s): {", ".join(packages_missing[:2])}{" and " + str(len(packages_missing) - 2) + " others" if len(packages_missing) > 2 else ""}', font = self.gui.bold_font).pack()
		else:
			import markdown
			import mdformat
			import tkinterweb

			html = tkinterweb.HtmlFrame(self.win, messages_enabled = False)
			formatted_body = body
			formatted_body = formatted_body.replace('(../..', f'(https://github.com/{username}/{repo_name}')
			formatted_body = formatted_body.replace('(../../..', f'(https://github.com/{username}')
			formatted_body = formatted_body.replace('(//', f'(https://')

			html.load_html(markdown.markdown(formatted_body))
			html.on_link_click(webbrowser.open_new_tab)
			html.pack()

		if self.auto: self.win.deiconify()

	def open_download(self, tag):
		webbrowser.open_new_tab(f'https://github.com/{username}/{repo_name}/releases/tag/{tag}')
		self.quit()

class Updater:
	def __init__(self):
		self.username, self.reponame = username, repo_name
		self.request_limit = 5

		self.progress = 0
		self.progress_inc = 25

	def check_internet(self):
		try:
			urllib.request.urlopen('https://github.com')
			return True
		except: return False

	def request(self, url):
		success = False
		for i in range(self.request_limit):
			try:
				r = urllib.request.urlopen(url)
				success = True
				break
			except:
				if not self.check_internet(): return
		if success:
			d = r.read().decode()
			return json.loads(d)

	def check_updates(self, prerelease):
		self.progress = 0

		if not self.check_internet():
			return {
			'newupdate': False,
			'error': True,
			'exceeded': False,
			'nowifi': True
			}
		try:
			versions = []
			if not self.check_internet(): return {'newupdate': False, 'error': True, 'exceeded': False, 'nowifi': True}
			
			response = self.request(f'https://api.github.com/repos/{self.username}/{self.reponame}/releases')
			if response is None: return {'newupdate': False, 'error': True, 'exceeded': False, 'nowifi': True}

			for info in response: versions.append(info['tag_name'])

			# UPDATE POINT 1
			self.progress += self.progress_inc

			if internal_version not in versions:
				try:
					testvar = response['message']
					if 'API rate limit exceeded for' in testvar:
						return {
						'newupdate': False,
						'error': True,
						'exceeded': True
						}
					else: return {'newupdate': False, 'error': False}
				except: return {'newupdate': False, 'error': False}
			if not self.check_internet(): return {'newupdate': False, 'error': True, 'exceeded': False, 'nowifi': True}

			# UPDATE POINT 2
			self.progress += self.progress_inc

			response = self.request(f'https://api.github.com/repos/{self.username}/{self.reponame}/releases/tags/{internal_version}')
			if response is None: return {'newupdate': False, 'error': True, 'exceeded': False, 'nowifi': True}\

			try:
				testvar = response['message']
				if 'API rate limit exceeded for' in testvar:
					return {
					'newupdate': False,
					'error': True,
					'exceeded': True
					}
				else: return {'newupdate': False, 'error': False}
			except: pass

			currvertime = response['published_at']

			# UPDATE POINT 3
			self.progress += self.progress_inc

			if not prerelease:
				if not self.check_internet(): return {'newupdate': False, 'error': True, 'exceeded': False, 'nowifi': True}

				response = self.request(f'https://api.github.com/repos/{self.username}/{self.reponame}/releases/latest')
				if response is None: return {'newupdate': False, 'error': True, 'exceeded': False, 'nowifi': True}
				try:
					testvar = response['message']
					if 'API rate limit exceeded for' in testvar:
						return {
						'newupdate': False,
						'error': True,
						'exceeded': True
						}
					else: return {'newupdate': False, 'error': False}
				except: pass
				if response['tag_name'] != internal_version and response['published_at'] > currvertime:
					return {
					'newupdate': True,
					'prerelease': False,
					'error': False,
					'title': response['name'],
					'tag': response['tag_name'],
					'body': response['body']
					}
				else:
					return {
					'newupdate': False,
					'unofficial': False,
					'error': False
					}
			else:
				if not self.check_internet(): return {'newupdate': False, 'error': True, 'exceeded': False, 'nowifi': True}

				response = self.request(f'https://api.github.com/repos/{self.username}/{self.reponame}/releases/tags/{versions[0]}')
				if response is None: return {'newupdate': False, 'error': True, 'exceeded': False, 'nowifi': True}
				try:
					testvar = response['message']
					if 'API rate limit exceeded for' in testvar:
						return {
						'newupdate': False,
						'error': True,
						'exceeded': True
						}
					else: return {'newupdate': False, 'error': True, 'exceeded': False, 'nowifi': False}
				except: pass
				if currvertime < response['published_at']:
					return {
					'newupdate': True,
					'prerelease': response['prerelease'],
					'error': False,
					'title': response['name'],
					'tag': response['tag_name'],
					'body': response['body']
					}
				else:
					return {
					'newupdate': False,
					'unofficial': False,
					'error': False
					}
		except:
			return {
			'newupdate': False,
			'error': True,
			'exceeded': False,
			'nowifi': False
			}

# https://stackoverflow.com/a/24072653
class FocusFrame(tk.Frame):
	def __init__(self, *args, **kwargs):
		tk.Frame.__init__(self, *args, **kwargs)
		self.bind('<1>', lambda event: self.focus_set())

# https://stackoverflow.com/a/16198198 (modified)
class VerticalScrolledFrame(tk.Frame):
	def __init__(self, parent, *args, **kw):
		tk.Frame.__init__(self, parent, *args, **kw)

		vscrollbar = tk.Scrollbar(self, orient = 'vertical')
		vscrollbar.pack(fill = 'y', side = 'right')
		self.canvas = tk.Canvas(self, bd = 0, highlightthickness = 0, yscrollcommand = vscrollbar.set)
		self.canvas.pack(side = 'left', fill = 'both', expand = True)
		vscrollbar.config(command = self.canvas.yview)

		self.canvas.xview_moveto(0)
		self.canvas.yview_moveto(0)

		self.interior = interior = tk.Frame(self.canvas)
		interior_id = self.canvas.create_window(0, 0, window = interior, anchor = 'nw')

		def _configure_interior(event):
			size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
			self.canvas.config(scrollregion = '0 0 %s %s' % size)
			if interior.winfo_reqwidth() != self.canvas.winfo_width():
				self.canvas.config(width=interior.winfo_reqwidth())
		interior.bind('<Configure>', _configure_interior)

		def _configure_canvas(event):
			if interior.winfo_reqwidth() != self.canvas.winfo_width():
				self.canvas.itemconfigure(interior_id, width=self.canvas.winfo_width())
		self.canvas.bind('<Configure>', _configure_canvas)

# https://stackoverflow.com/a/36221216
class Tooltip:
	"""
	create a tooltip for a given widget
	"""
	def __init__(self, widget, text='widget info'):
		self.waittime = 500     #miliseconds
		self.wraplength = 180   #pixels
		self.widget = widget
		self.text = text
		self.widget.bind("<Enter>", self.enter)
		self.widget.bind("<Leave>", self.leave)
		self.widget.bind("<ButtonPress>", self.leave)
		self.id = None
		self.tw = None

	def enter(self, event=None):
		self.schedule()

	def leave(self, event=None):
		self.unschedule()
		self.hidetip()

	def schedule(self):
		self.unschedule()
		self.id = self.widget.after(self.waittime, self.showtip)

	def unschedule(self):
		id = self.id
		self.id = None
		if id:
			self.widget.after_cancel(id)

	def showtip(self, event=None):
		x = y = 0
		x, y, cx, cy = self.widget.bbox("insert")
		x += self.widget.winfo_rootx() + 25
		y += self.widget.winfo_rooty() + 20
		# creates a toplevel window
		self.tw = tk.Toplevel(self.widget)
		# Leaves only the label and removes the app window
		self.tw.wm_overrideredirect(True)
		self.tw.wm_geometry("+%d+%d" % (x, y))
		label = tk.Label(self.tw, text=self.text, justify='left',
					   background="#ffffff", relief='solid', borderwidth=1,
					   wraplength = self.wraplength)
		label.pack(ipadx=1)

	def hidetip(self):
		tw = self.tw
		self.tw= None
		if tw:
			tw.destroy()

class TooltipButton(ttk.Button):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.tooltip = Tooltip(self, self['text'])

# https://stackoverflow.com/a/65447493
class ThreadWithResult(threading.Thread):
	def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, *, daemon=False):
		def function(): self.result = target(*args, **kwargs)
		super().__init__(group=group, target=function, name=name, daemon=daemon)
