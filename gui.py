import sys
if __name__ == '__main__':
	print('Please run main.py to start the program!')
	sys.exit()

import os
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
import copy
import json
import threading
import configparser
import urllib.request

name = 'QuizProg-GUI'

username = 'gamingwithevets'
repo_name = 'quizprog-gui'

version = '0.1.0'
internal_version = 'v0.1.0'
prerelease = True

license = 'MIT'

g = None

@staticmethod
def report_error(e, val, tb, fatal = False):
	err_text = f'{traceback.format_exc()}\nIf this error persists, please report it here:\nhttps://github.com/{username}/{repo_name}/issues'

	exc = val

	print(f'{"Fatal exception" if fatal else "Exception"} raised:\n\n' + err_text)
	if issubclass(type(exc), OSError):
		if os.name == 'nt':
			if exc.winerror: errno = f'WE{exc.winerror}'
			else: errno = exc.errno
		else: errno = exc.errno
		message = f'[{type(exc).__name__}] {exc.strerror} ({errno})'
	else: message = f'[{type(exc).__name__}] {exc}'
	g.set_message_force(message)
	return 'Oops! A fatal error has occured.\n\n' + err_text

tk.Tk.report_callback_exception = report_error

class GUI:
	def __init__(self, window):
		self.version = version

		self.window = window

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
		self.init_protocols()

		# quizprog-gui settings
		self.message = 'Welcome to QuizProg-GUI! Any messages will appear here.'
		self.message_force = None
		self.datafile = {'title': 'My Quiz', 'questions': [{'question': 'Question', 'a': 'Answer A', 'b': 'Answer B', 'c': 'Answer C', 'd': 'Answer D', 'correct': 'a'}]}
		self.datafile_mode = 'json'

		self.savepath = ''
		self.allowsave = True

		self.modified = False

		self.auto_check_updates = tk.BooleanVar(); self.auto_check_updates.set(True)
		self.check_prerelease_version = tk.BooleanVar(); self.check_prerelease_version.set(False)

		self.updates_checked = False

		self.debug = False

		if os.name == 'nt': self.appdata_folder = f'{os.getenv("LOCALAPPDATA")}\\{name}'
		else:
			if platform.system() == 'Darwin': self.appdata_folder = os.path.expanduser(f'~/Library/Application Support/{name}')
			else: self.appdata_folder = os.path.expanduser(f'~/.config/{name}')

		self.save_to_cwd = False
		self.ini = configparser.ConfigParser()
		self.parse_settings()

		self.jsonhandler = JSONHandler(self)
		self.quizconf = QuizConf(self)
		self.updater_gui = UpdaterGUI(self)

		self.unsupported_tcl = False
		if sys.version_info < (3, 7, 6):
			if tk.messagebox.askyesno('Warning', f'It looks like you are running Python {platform.python_version()}, which has a version of Tcl/Tk that doesn\'t support some Unicode characters.\n\nDo you want to continue?', icon = 'warning'): self.unsupported_tcl = True
			else: self.quit()

	def set_message_force(self, msg): self.message_force = msg

	def start_main(self):
		if not self.updates_checked:
			if self.auto_check_updates.get(): threading.Thread(target = self.auto_update).start()
			else: self.updates_checked = True
		self.main()

	def auto_update(self):
		self.update_thread = ThreadWithResult(target = self.updater_gui.updater.check_updates, args = (True,))
		self.update_thread.start()
		i = 0
		j = 0
		mult = 5000
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
		
		self.window.unbind('<Control-n>')
		self.window.unbind('<Control-o>')
		self.window.unbind('<Control-s>')
		self.window.unbind('<Control-Shift-S>')
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
			]): os._exit(0)

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
		self.window.bind('<F12>', self.version_details)
		self.window.bind('<1>', self.main_focus)
		self.window.option_add('*tearOff', False)
		
		self.disable_all_widgets()

		self.set_title()
		icon = 'ico' if os.name == 'nt' else 'xbm'
		try: self.window.iconbitmap(f'{self.temp_path}\\icon.{icon}')
		except tk.TclError:
			err_text = f'Whoops! The icon file "icon.{icon}" is required.\nCan you make sure the file is in "{self.temp_path}"?\n\n{traceback.format_exc()}\nIf this problem persists, please report it here:\nhttps://github.com/{username}/{repo_name}/issues'
			print(err_text)
			tk.messagebox.showerror('Hmmm?', err_text)
			sys.exit()

	def init_protocols(self):
		self.window.protocol('WM_DELETE_WINDOW', self.quit)

	def unicode_filter(self, string): return ''.join(['□' if ord(c) > 0xFFFF else c for c in string]) if self.unsupported_tcl else string

	def prompt_save_changes(self):
		if self.modified:
			prompt = tk.messagebox.askyesnocancel('Unsaved changes!', 'Do you want to save changes to the current quiz?', icon = 'warning')
			if prompt == None: return True
			elif prompt: self.save_file()

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
			self.savepath = self.jsonhandler.savepath
			if os.path.splitext(self.savepath)[1].casefold() == '.json': self.datafile_mode = 'json'
			#else: self.datafile_mode = 'qpg'
			else: self.datafile_mode = 'json'
			self.datafile = self.jsonhandler.datafile
			self.modified = False		
		
		self.refresh(True)

	def save_file(self):
		if self.savepath and os.path.exists(self.savepath) and not os.path.isdir(self.savepath):
			with open(self.savepath, 'w+') as f: f.write(json.dumps(self.datafile, indent = 4))
			self.message = 'Quiz saved!'
			self.modified = False
			self.config_msg()
		else:
			self.savepath = ''
			self.save_file_as()

	def save_file_as(self):
		ok = self.jsonhandler.save_file(self.datafile_mode == 'json')
		if ok:
			self.savepath = self.jsonhandler.savepath
			self.modified = False
		
		self.config_msg()

	def reload(self):
		if self.modified:
			confirm = tk.messagebox.askyesno('Reload changes?', 'Are you sure you want to reload this quiz and lose the changes you made in QuizProg-GUI?', icon = 'warning')
			if not confirm: return
			else:
				self.jsonhandler.reload()
				self.modified = False
				self.config_msg()

	def about_menu(self):
		nl = '\n' # workaround for prohibition of backslashes in f-string expression
		tk.messagebox.showinfo(f'About {name}', f'''\
{name} - {version} ({'64' if sys.maxsize > 2**31-1 else '32'}-bit) - Running on {platform.system()} x{'64' if platform.machine().endswith('64') else '86'}
Project page: https://github.com/{username}/{repo_name}
{nl+'WARNING: This is a pre-release version, therefore it may have bugs and/or glitches.'+nl if prerelease else ''}
Licensed under the {license} license

Copyright (c) 2022-2023 GamingWithEvets Inc.

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
		file_menu.add_command(label = 'New quiz', command = self.new_quiz, accelerator = 'Ctrl+N')
		file_menu.add_command(label = 'Open...', command = self.open_file, accelerator = 'Ctrl+O')
		file_menu.add_command(label = 'Save', command = self.save_file, accelerator = 'Ctrl+S')
		file_menu.add_command(label = 'Save as...', command = self.save_file_as, accelerator = 'Ctrl+Shift+S')
		file_menu.add_separator()
		file_menu.add_command(label = 'Compile EXE file', command = self.n_a)
		file_menu.add_separator()
		file_menu.add_command(label = 'Exit', command = self.quit)
		menubar.add_cascade(label = 'File', menu = file_menu)

		edit_menu = tk.Menu(menubar)
		edit_menu.add_command(label = 'Reload', command = self.reload)
		menubar.add_cascade(label = 'Edit', menu = edit_menu)

		settings_menu = tk.Menu(menubar)
		updater_settings_menu = tk.Menu(settings_menu)
		updater_settings_menu.add_checkbutton(label = 'Check for updates on startup', variable = self.auto_check_updates, command = self.save_settings)
		updater_settings_menu.add_checkbutton(label = 'Check for pre-release versions', variable = self.check_prerelease_version, command = self.save_settings)
		settings_menu.add_cascade(label = 'Updates', menu = updater_settings_menu)

		if self.debug:
			settings_menu.add_separator()
			debug_menu = tk.Menu(settings_menu)
			debug_menu.add_command(label = 'Version details', command = self.version_details, accelerator = 'F12')
			debug_menu.add_separator()
			debug_menu.add_command(label = 'Updater test', command = lambda: self.updater_gui.init_window(debug = True))
			debug_menu.add_separator()
			debug_menu.add_command(label = 'Disable debug mode', command = self.disable_debug)
			settings_menu.add_cascade(label = 'Debug', menu = debug_menu)

		menubar.add_cascade(label = 'Settings', menu = settings_menu)

		help_menu = tk.Menu(menubar)
		help_menu.add_command(label = 'Check for updates', command = self.updater_gui.init_window)
		help_menu.add_command(label = f'About {name}', command = self.about_menu)
		menubar.add_cascade(label = 'Help', menu = help_menu)

		self.window.config(menu = menubar)
		
		self.window.bind('<Control-n>', lambda x: self.new_quiz())
		self.window.bind('<Control-o>', lambda x: self.open_file())
		self.window.bind('<Control-s>', lambda x: self.save_file())
		self.window.bind('<Control-Shift-S>', lambda x: self.save_file_as())

	def config_msg(self):
		if self.message_force: self.msg_label.config(text = self.message_force, background = 'red')
		elif self.message: self.msg_label.config(text = self.message, background = 'green')
		else: self.msg_label.config(text = f'QuizProg - GUI edition. Version {version}. © 2023 GamingWithEvets Inc.', background = 'black')
		self.message = self.message_force = None

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
		ttk.Label(text = f'Quiz format: {self.datafile_mode.upper()}').pack()
		if self.jsonhandler.check_element('description', rel = False):
			if self.datafile['description']: desc = self.datafile['description']
			else: desc = '(no description)'
		else: desc = '(no description)'
		ttk.Label(text = desc, justify = 'center', font = self.italic_font).pack()

		ttk.Button(text = 'Quiz settings', command = self.quiz_conf).pack(side = 'bottom')
		ttk.Button(text = 'Quiz questions', command = self.n_a).pack(side = 'bottom')
		ttk.Label().pack(side = 'bottom')
		ttk.Button(text = 'Edit quiz description', command = self.quiz_desc).pack(side = 'bottom')
		ttk.Button(text = 'Rename quiz', command = self.quiz_name).pack(side = 'bottom')

		self.window.mainloop()

	def format_text(self, text):
		if len(text) > 0:
			text = re.sub(r'\n+', '\n', text)
			if text[-1] == '\n': text = text[:-1]

		return text

	def quiz_name(self):
		def save(event = 'blah'):
			text = entry.get()
			if text:
				if text != self.datafile['title']:
					self.datafile['title'] = text
					self.modified = True
				self.refresh(True)
				self.message = 'Quiz name saved!'
			else: tk.messagebox.showerror('Error', 'Quiz name cannot be blank!')

		def discard():
			if tk.messagebox.askyesno('Discard', 'Discard changes?', icon = 'warning'): self.main()

		self.refresh(menubar = False)
		ttk.Label(text = 'Type your quiz name.').pack()
		ttk.Button(text = 'OK', command = save).pack(side = 'bottom', anchor = 's')
		ttk.Button(text = 'Discard', command = discard).pack(side = 'bottom', anchor = 's')
		
		scroll = ttk.Scrollbar(orient = 'horizontal')
		entry = ttk.Entry(width = self.display_w, xscrollcommand = scroll.set)
		entry.insert(0, self.datafile['title'])
		entry.bind('<Return>', save)
		entry.focus()
		entry.pack()
		scroll.config(command = entry.xview)
		scroll.pack(fill = 'x')

	def quiz_desc(self):
		if not self.jsonhandler.check_element('description'): self.datafile['description'] = ''

		def save():
			text = self.format_text(entry.get('1.0', 'end-1c'))
			if text != self.datafile['description']:
				self.datafile['description'] = re.sub(r'\n+', '\n', text)
				self.modified = True
				self.message = 'Quiz description saved!'
			if self.datafile['description'] == '': del self.datafile['description']
			self.refresh(True)

		self.refresh(menubar = False)
		ttk.Label(text = 'Type your quiz description.').pack()
		ttk.Button(text = 'OK', command = save).pack(side = 'bottom', anchor = 's')

		scroll = ttk.Scrollbar(orient = 'vertical')
		entry = tk.Text(width = self.display_w, yscrollcommand = scroll.set, wrap = 'word')
		entry.insert('end', self.datafile['description'])
		scroll.config(command = entry.yview)
		scroll.pack(side = 'right', fill = 'y')
		entry.focus()
		entry.pack(side = 'left')

	def quiz_conf(self): self.quizconf.main()

	"""----------- END MENUS ---------"""

class QuizConf:
	def __init__(self, gui):
		self.gui = gui
		self.wrongmsg_editor = WrongMsg_Editor(self)

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

		self.dummy = ttk.Label(text = 'Quiz settings', font = self.gui.bold_font).pack()
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
		def save():
			text = self.gui.format_text(entry.get('1.0', 'end-1c'))
			if text != self.fail_text:
				self.fail_text = text
				self.gui.modified = True
				self.gui.message = 'Game over comment saved!'
			self.menu()

		self.gui.refresh(menubar = False)
		ttk.Label(text = 'Type your quiz game over comment.').pack()
		ttk.Button(text = 'OK', command = save).pack(side = 'bottom', anchor = 's')

		scroll = ttk.Scrollbar(orient = 'vertical')
		entry = tk.Text(width = self.gui.display_w, yscrollcommand = scroll.set)
		entry.insert('end', self.fail_text)
		scroll.config(command = entry.yview)
		scroll.pack(side = 'right', fill = 'y')
		entry.pack(side = 'left')

	def finish_edit(self):
		def save():
			text = self.gui.format_text(entry.get('1.0', 'end-1c'))
			if text != self.finish_text:
				self.finish_text = text
				self.gui.modified = True
				self.gui.message = 'Quiz completion comment saved!'
			self.menu()

		self.gui.refresh(menubar = False)
		ttk.Label(text = 'Type your quiz completion comment.').pack()
		ttk.Button(text = 'OK', command = save).pack(side = 'bottom', anchor = 's')

		scroll = ttk.Scrollbar(orient = 'vertical')
		entry = tk.Text(width = self.gui.display_w, yscrollcommand = scroll.set)
		entry.insert('end', self.finish_text)
		scroll.config(command = entry.yview)
		scroll.pack(side = 'right', fill = 'y')
		entry.pack(side = 'left')

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

class WrongMsg_Editor:
	def __init__(self, quizconf):
		self.quizconf = quizconf
		self.gui = quizconf.gui

	def main(self):
		self.wrongmsg = self.quizconf.wrongmsg_list

		self.index = 0

		self.menu()

	def navigation_prev(self): self.index -= 1; self.menu()
	def navigation_next(self): self.index += 1; self.menu()

	def menu(self):
		self.gui.refresh()
		self.gui.print_msg()
		ttk.Label(text = 'Global wrong answer comments', font = self.gui.bold_font).pack()
		ttk.Button(text = 'Back', command = self.end).pack(side = 'bottom')
		ttk.Label().pack(side = 'bottom')

		if len(self.wrongmsg) == 0:
			ttk.Label(text = 'No global wrong answer comments!').pack()
			ttk.Button(text = 'Create new comment', command = self.new).pack(side = 'bottom')
		else:
			ttk.Label(text = f'{self.index + 1} / {len(self.wrongmsg)}').pack()
			ttk.Button(text = 'Delete comment', command = self.delete).pack(side = 'bottom')
			ttk.Button(text = 'Edit comment', command = self.edit).pack(side = 'bottom')
			ttk.Button(text = 'Create new comment', command = self.new).pack(side = 'bottom')
			ttk.Label().pack(side = 'bottom')
			nav_frame = FocusFrame()
			prev_bt = ttk.Button(nav_frame, text = '<', command = self.navigation_prev)
			next_bt = ttk.Button(nav_frame, text = '>', command = self.navigation_next)
			if len(self.wrongmsg) > 1:
				if self.index == 0: next_bt.pack(side = 'right')
				elif self.index == len(self.wrongmsg) - 1: prev_bt.pack(side = 'left')
				else: prev_bt.pack(side = 'left'); next_bt.pack(side = 'right')
			nav_frame.pack(side = 'bottom', fill = 'x')

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
		def save():
			text = self.gui.format_text(entry.get('1.0', 'end-1c'))
			if len(self.wrongmsg) > 0:
				for i in range(len(self.wrongmsg)):
					if text == self.wrongmsg[i]:
						tk.messagebox.showerror('Error', f'Duplicate global wrong answer comment detected!\nDuplicate of comment w/ index {i + 1} / {len(self.wrongmsg)}')
						return
			if text != '':
				self.wrongmsg.append(text)
				self.gui.modified = True
				self.index = len(self.wrongmsg) - 1
				self.gui.message = 'Global wrong answer comment created!'
			self.menu()

		def discard():
			if tk.messagebox.askyesno('Discard', 'Discard this comment?', icon = 'warning'): self.menu()

		self.gui.refresh(menubar = False)
		ttk.Label(text = 'Type your global wrong answer comment.').pack()
		ttk.Button(text = 'OK', command = save).pack(side = 'bottom', anchor = 's')
		ttk.Button(text = 'Discard', command = discard).pack(side = 'bottom', anchor = 's')

		scroll = ttk.Scrollbar(orient = 'vertical')
		entry = tk.Text(width = self.gui.display_w, yscrollcommand = scroll.set, wrap = 'word')
		scroll.config(command = entry.yview)
		scroll.pack(side = 'right', fill = 'y')
		entry.focus()
		entry.pack(side = 'left')

	def edit(self):
		def save():
			text = self.gui.format_text(entry.get('1.0', 'end-1c'))
			if len(self.wrongmsg) > 0:
				for i in range(len(self.wrongmsg)):
					if i != self.index and text == self.wrongmsg[i]:
						tk.messagebox.showerror('Error', f'Duplicate global wrong answer comment detected!\nDuplicate of comment w/ index {i + 1} / {len(self.wrongmsg)}')
						return
			if text != '':
				self.wrongmsg[self.index] = text
				self.gui.modified = True
				self.index = len(self.wrongmsg) - 1
				self.gui.message = 'Global wrong answer comment saved!'
			self.menu()

		def discard():
			text = self.gui.format_text(entry.get('1.0', 'end-1c'))
			if text != self.wrongmsg[self.index]:
				if tk.messagebox.askyesno('Discard', 'Discard changes to this comment?', icon = 'warning'): self.menu()
			else: self.menu()

		self.gui.refresh(menubar = False)
		ttk.Label(text = 'Type your global wrong answer comment.').pack()
		ttk.Button(text = 'OK', command = save).pack(side = 'bottom', anchor = 's')
		ttk.Button(text = 'Discard', command = discard).pack(side = 'bottom', anchor = 's')

		scroll = ttk.Scrollbar(orient = 'vertical')
		entry = tk.Text(width = self.gui.display_w, yscrollcommand = scroll.set, wrap = 'word')
		entry.insert('end', self.wrongmsg[self.index])
		scroll.config(command = entry.yview)
		scroll.pack(side = 'right', fill = 'y')
		entry.focus()
		entry.pack(side = 'left')

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

class JSONHandler:
	def __init__(self, gui):
		self.gui = gui

		self.datafile_new = copy.deepcopy(self.gui.datafile)
		self.new_quiz()

		self.savepath = ''
		self.savepath_tmp = ''
		self.message = None

	def reload_dtfile(self): self.datafile = self.gui.datafile

	def reload(self):
		self.reload_dtfile()
		self.datafile = copy.deepcopy(self.datafile_bak)
		self.gui.datafile = copy.deepcopy(self.datafile)

	def create_backup(self): self.datafile_bak = copy.deepcopy(self.datafile)

	def new_quiz(self):
		self.datafile = copy.deepcopy(self.datafile_new)
		self.create_backup()

	def open_file(self):
		filetypes = [('QuizProg-GUI Quiz Projects', '*.qpg'), ('QuizProg Quiz Projects', '*.json'), ('All Files', '*.*')]
		defaultextension = '.json'

		self.savepath_tmp = ''
		self.savepath_tmp = tk.filedialog.askopenfilename(initialdir = os.path.dirname(self.savepath) if self.savepath else os.getcwd(), filetypes = filetypes, defaultextension = defaultextension)
		if self.savepath_tmp:
			if os.path.splitext(self.savepath_tmp)[1].casefold() == '.json':
				pass#if not tk.messagebox.askyesno('Note for JSON files', 'The file you are trying to open is a (console) QuizProg quiz project. However, these quiz projects are limited to the features in (console) QuizProg.\nRight now you are not required to save this file as a QuizProg-GUI quiz project until you want to use new features present in QuizProg-GUI.\nDo you want to continue?'): return False
			old_path = self.savepath
			self.savepath = self.savepath_tmp
			if os.name == 'nt': self.savepath = self.savepath.replace('/', '\\')
			try:
				success = False
				for i in range(1):
					try: self.datafile = json.load(open(self.savepath, encoding = 'utf-8'))
					except (json.decoder.JSONDecodeError, UnicodeDecodeError): message = 'Invalid JSON data!'; self.savepath = old_path; break
					gerror_msg = lambda a: f'String variable \'{a}\' not found or empty!'
					if not self.check_element('title', rel = False): message = gerror_msg('title'); self.savepath = old_path; break
					if not self.check_element('questions', list, rel = False): gerror_msg('questions'); self.savepath = old_path; break
					for i in range(len(self.datafile['questions'])):
						qerror_msg = lambda a: f'String variable \'{a}\' not found or empty in question {i+1}!'
						if not self.check_question_element('question', i, rel = False): message = qerror_msg('question'); success = False; self.savepath = old_path; break
						if not self.check_question_element('a', i, rel = False): message = qerror_msg('a'); success = False; self.savepath = old_path; break
						if not self.check_question_element('b', i, rel = False): message = qerror_msg('b'); success = False; self.savepath = old_path; break
						if not self.check_question_element('c', i, rel = False): message = qerror_msg('c'); success = False; self.savepath = old_path; break
						if not self.check_question_element('d', i, rel = False): message = qerror_msg('d'); success = False; self.savepath = old_path; break
						if not self.check_question_element('correct', i, rel = False): message = qerror_msg('correct'); success = False; self.savepath = old_path; break
						success = True
					if not success: break
					self.create_backup()
					message = f'Loaded quiz: {self.savepath}'
				if not success:
					self.reload_dtfile()
					self.create_backup()
			except OSError:
				report_error(*sys.exc_info())
				return False

			if success: self.gui.message = message
			else: self.gui.message_force = message
			return success
		else: return False

	def save_file(self, allow_json):
		self.reload_dtfile()
		
		self.savepath_tmp = ''
		self.savepath_tmp = tk.filedialog.asksaveasfilename(initialdir = os.path.dirname(self.savepath) if self.savepath else os.getcwd(), initialfile = f'{self.datafile["title"]}.qpg', filetypes = [('QuizProg-GUI Quiz Projects', '*.qpg'), ('QuizProg Quiz Projects', '*.json'), ('All Files', '*.*')], defaultextension = '.qpg')
		if self.savepath_tmp:
			if os.path.splitext(self.savepath_tmp)[1].casefold() == '.json' and not allow_json:
				tk.messagebox.showerror('Cannot save as JSON', 'To use new features present in QuizProg-GUI, you must save this file as a QuizProg-GUI quiz project.')
				return False
			self.savepath = self.savepath_tmp
			if os.name == 'nt': self.savepath = self.savepath.replace('/', '\\')
			success = False
			try:
				with open(self.savepath, 'w+') as f: f.write(json.dumps(self.datafile, indent = 4))
				message = f'Quiz saved as: {self.savepath}'
				success = True
			except OSError:
				report_error(*sys.exc_info())
				return False

			if success: self.gui.message = message
			else: self.gui.message_force = message
			return success
		else: return False

	def check_element(self, element, valtype = str, rel = True):
		if rel: self.reload_dtfile()

		test1 = False
		test2 = False
		test3 = False
		if element in self.datafile:
			test1 = True
			if not (type(self.datafile[element]) is not bool and not self.datafile[element]): test2 = True
			if type(self.datafile[element]) is valtype: test3 = True

		if test1 and test2 and test3: return True
		else: return False

	def check_question_element(self, element, qid, valtype = str, rel = True):
		if rel: self.reload_dtfile()

		test1 = False
		test2 = False
		test3 = False

		if element in self.datafile['questions'][qid]:
			test1 = True
			if self.datafile['questions'][qid][element]: test2 = True
			if type(self.datafile['questions'][qid][element]) is valtype: test3 = True

		if test1 and test2 and test3: return True
		else: return False

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

			self.win.geometry('400x200')
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
		ttk.Label(self.win, text = 'Nothing here yet...').pack()
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
		elif update_info['newupdate']: self.draw_download_msg(update_info['title'], update_info['tag'], update_info['prerelease'])
		else: self.draw_msg('You are already using the latest version.')

	def draw_check(self):
		for w in self.win.winfo_children(): w.destroy()

		ttk.Label(self.win, text = 'Checking for updates...').pack()
		self.progressbar = ttk.Progressbar(self.win, orient = 'horizontal', length = 100, mode = 'determinate')
		self.progressbar.pack()
		ttk.Label(self.win, text = 'DO NOT close the program\nwhile checking for updates', font = self.gui.bold_font).pack(side = 'bottom').pack()

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
		except: return False

		return True

	def draw_download_msg(self, title, tag, prever):
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
		ttk.Button(self.win, text = 'Visit download page', command = lambda: self.open_download(tag)).pack(side = 'bottom')
		
		self.gui.draw_blank(master = self.win)

		packages_missing = []
		for package in ('markdown', 'mdformat-gfm', 'tkinterweb'):
			if not self.package_installed(package): packages_missing.append(package)

		if packages_missing: ttk.Label(self.win, text = f'Missing package(s): {", ".join(packages_missing[:2])}{" and " + str(len(packages_missing) - 2) + " others" if len(packages_missing) > 2 else ""}', font = self.gui.bold_font).pack()
		else:
			import markdown
			import mdformat
			import tkinterweb

			html = tkinterweb.HtmlFrame(self.win, messages_enabled = False)
			html.load_html(markdown.markdown(mdformat.text(body)).replace('../..', f'https://github.com/{username}/{repo_name}'))
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
			self.request('https://google.com', True)
			return True
		except: return False

	def request(self, url, testing = False):
		success = False
		for i in range(self.request_limit):
			try:
				r = urllib.request.urlopen(url)
				success = True
				break
			except:
				if not testing:
					if not self.check_internet(): return
		if success:
			if not testing:
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
					'tag': response['tag_name']
					}
				else:
					return {
					'newupdate': False,
					'unofficial': False,
					'error': False
					}
			else:
				for version in versions:
					if not self.check_internet(): return {'newupdate': False, 'error': True, 'exceeded': False, 'nowifi': True}

					response = self.request(f'https://api.github.com/repos/{self.username}/{self.reponame}/releases/tags/{version}')
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
						'tag': response['tag_name']
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

# https://stackoverflow.com/a/65447493
class ThreadWithResult(threading.Thread):
	def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, *, daemon=None):
		def function(): self.result = target(*args, **kwargs)
		super().__init__(group=group, target=function, name=name, daemon=daemon)
