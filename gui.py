import os
import sys
import json
import traceback
import tkinter as tk
import tkinter.font
import tkinter.messagebox
import tkinter.filedialog

def report_error(self = None, exc = None, val = None, tb = None):
	if exc == None: exc = traceback.format_exc()


	try: GUI.window.quit()
	except Exception: pass
	print(f'Whoops! QuizProg-GUI has suffered a very fatal error.\n\n{exc}\nIf this error persists, please report it here:\nhttps://github.com/gamingwithevets/quizprog-gui/issues')
	tk.messagebox.showerror('Whoops!', f'QuizProg-GUI has suffered a very fatal error.\n\n{exc}\nIf this error persists, please report it here:\nhttps://github.com/gamingwithevets/quizprog-gui/issues')
	sys.exit()

tk.Tk.report_callback_exception = report_error

version = 'Beta 1.0.0'
about_msg = f'''\
QuizProg-GUI - {version}
Project page: https://github.com/gamingwithevets/quizprog-gui

NOTE: This version is not final! Therefore it may have bugs and/or glitches.

Licensed under the MIT license

Copyright (c) 2022 GamingWithEvets Inc.

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
'''

class GUI():
	def __init__(self, window):
		self.version = version

		self.window = window

		self.display_w = 500
		self.display_h = 500

		tk_font = tk.font.nametofont('TkDefaultFont').actual()
		self.font_name = tk_font['family']
		self.font_size = tk_font['size']

		self.message = ('Welcome to QuizProg-GUI! Any messages will appear here.', False)
		self.datafile = {'title': 'My Quiz', 'questions': [{'question': 'Question', 'a': 'Answer A', 'b': 'Answer B', 'c': 'Answer C', 'd': 'Answer D', 'correct': 'a'}]}
		self.datafile_mode = 'qpg'

		self.savepath = ''
		self.allowsave = True

		self.modified = False

		self.jsonhandler = JSONHandler(self)
		self.init_window()
		self.menubar()
		self.init_protocols()
		
		self.main_menu()

	def n_a(self): tk.messagebox.showinfo('Not implemented', 'This feature is not implemented into QuizProg-GUI... yet.\n\nIn the meantime you could use the console version!\nLink to it in the README file.')

	def refresh(self, load_func = False):
		for w in self.window.winfo_children(): w.destroy()
		self.menubar()

		if load_func: self.main_menu()

	def quit(self):
		cancel = self.prompt_save_changes()
		if cancel: return

		self.window.quit()
		sys.exit()

	def set_title(self):
		if self.modified: self.window.title(f'QuizProg-GUI - {self.datafile["title"]}*')
		else: self.window.title(f'QuizProg-GUI - {self.datafile["title"]}')

	def init_window(self):
		self.window.geometry(f'{self.display_w}x{self.display_h}')
		self.window.resizable(False, False)
		self.set_title()
		try: self.window.iconbitmap('icon.ico')
		except: pass

	def init_protocols(self):
		self.window.protocol('WM_DELETE_WINDOW', self.quit)

	def draw_label(self, text, font = None, color = 'black', bg = None, side = 'top', anchor = 'center', recwidth = None, recheight = None, master = None):
		if master == None: master = self.window

		def conv_anchor(a):
			if a == 'topleft': return 'nw'
			elif a == 'midtop': return 'n' 
			elif a == 'topright': return 'ne'
			elif a == 'midleft': return 'w'
			elif a == 'midright': return 'e'
			elif a == 'bottomleft': return 'sw'
			elif a == 'midbottom': return 's'
			elif a == 'bottomright': return 'se'
			else: return a

		anc = conv_anchor(anchor)
		text = tk.Label(master, text = text, font = font, fg = color, bg = bg, width = recwidth, height = recheight, anchor = anc)
		text.pack(side = side, anchor = anc)

	def prompt_save_changes(self):
		if self.modified:
			prompt = tk.messagebox.askyesnocancel('Unsaved changes!', 'Do you want to save changes to the current quiz?')
			if prompt == None: return True
			elif prompt: self.save_file()

	def new_quiz(self):
		cancel = self.prompt_save_changes()
		if cancel: return

		self.jsonhandler.new_quiz()
		self.datafile = self.jsonhandler.datafile
		self.savepath = self.jsonhandler.savepath
		self.modified = False

		self.refresh(True)

	def open_file(self):
		cancel = self.prompt_save_changes()
		if cancel: return


		ok = self.jsonhandler.open_file()
		if ok:
			self.savepath = self.jsonhandler.savepath
			if os.path.splitext(self.savepath)[1].casefold() == '.json': self.datafile_mode = 'json'
			else: self.datafile_mode = 'qpg'
			self.datafile = self.jsonhandler.datafile
			self.modified = False		
		self.message = self.jsonhandler.message
		
		self.refresh(True)

	def save_file(self):
		if not self.savepath: self.save_file_as()

		try:
			with open(self.savepath, 'w+') as f: f.write(json.dumps(self.datafile, indent = 4))
			self.message = 'Quiz saved!'
			self.modified = False
		except IOError as e: self.message = f'Can\'t save file: {e.strerror}'

		self.refresh(True)

	def save_file_as(self):
		ok = self.jsonhandler.save_file(self.datafile_mode == 'json')
		if ok:
			self.savepath = self.jsonhandler.savepath
			self.modified = False
		self.message = self.jsonhandler.message
		
		self.refresh(True)

	def reload(self):
		if self.modified:
			confirm = tk.messagebox.askyesno('Reload changes?', 'Are you sure you want to reload this quiz and lose the changes you made in QuizProg-GUI?')
			if not confirm: return
			else:
				self.jsonhandler.reload()
				self.modified = False
				self.refresh(True)

	def about_menu(self):
		tk.messagebox.showinfo('About QuizProg-GUI', about_msg)

	def menubar(self):
		menubar = tk.Menu(self.window)

		file_menu = tk.Menu(menubar, tearoff = False)
		file_menu.add_command(label = 'New quiz', command = self.new_quiz)
		file_menu.add_command(label = 'Open...', command = self.open_file)
		file_menu.add_command(label = 'Save', command = self.save_file)
		file_menu.add_command(label = 'Save as...', command = self.save_file_as)
		file_menu.add_separator()
		file_menu.add_command(label = 'Export', command = self.n_a)
		file_menu.add_separator()
		file_menu.add_command(label = 'Exit', command = self.quit)
		menubar.add_cascade(label = 'File', menu = file_menu)

		edit_menu = tk.Menu(menubar, tearoff = False)
		edit_menu.add_command(label = 'Reload', command = self.reload)
		menubar.add_cascade(label = 'Edit', menu = edit_menu)

		help_menu = tk.Menu(menubar, tearoff = False)
		help_menu.add_command(label = 'Check for updates', command = self.n_a)
		help_menu.add_command(label = 'About QuizProg-GUI', command = self.about_menu)
		menubar.add_cascade(label = 'Help', menu = help_menu)

		self.window.config(menu = menubar)

	def print_msg(self):
		if self.message[0]: self.draw_label(self.message[0], color = 'black' if self.message[1] else 'white', bg = 'red' if self.message[1] else 'green', recwidth = self.display_w)
		else: self.draw_label('QuizProg - GUI edition', color = 'white', bg = 'black', recwidth = self.display_w)
		self.message = ('', False)

	"""--------- BEGIN MENUS ---------"""

	def main_menu(self):

		self.set_title()
		self.print_msg()

		self.draw_label('You are editing:')
		try: self.draw_label(self.datafile['title'], font = (f'{self.font_name}', f'{self.font_size}', 'bold'))
		except Exception: self.draw_label(self.datafile['title'])
		self.draw_label(self.datafile['description'] if self.jsonhandler.check_element('description') else '(no description provided)')
		tk.Button(text = 'Quiz settings', command = self.quiz_conf).pack(side = 'bottom')
		tk.Button(text = 'Edit quiz questions').pack(side = 'bottom')
		self.draw_label('', side = 'bottom')
		tk.Button(text = 'Edit quiz description', command = self.quiz_desc).pack(side = 'bottom')
		tk.Button(text = 'Rename quiz', command = self.quiz_name).pack(side = 'bottom')

		self.window.mainloop()

	def quiz_name(self):
		def save(event):
			text = entry.get()
			if text:
				if text != self.datafile['title']:
					self.datafile['title'] = text
					self.modified = True
				self.refresh(True)
			else: tk.messagebox.showerror('Error', 'Quiz name cannot be blank!')

		self.refresh()
		self.draw_label('Type your quiz name and press Enter.')
		
		scroll = tk.Scrollbar(orient = 'horizontal')
		entry = tk.Entry(width = self.display_w, xscrollcommand = scroll.set)
		entry.insert(0, self.datafile['title'])
		entry.bind('<Return>', save)
		entry.focus()
		entry.pack()
		scroll.config(command = entry.xview)
		scroll.pack(fill = 'x')

	def quiz_desc(self):
		if not self.jsonhandler.check_element('description'): self.datafile['description'] = ''

		def save():
			text = entry.get('1.0', 'end-1c')
			if text != self.datafile['description']:
				self.datafile['description'] = text
				self.modified = True
			if self.datafile['description'] == '': del self.datafile['description']
			self.refresh(True)

		self.refresh()
		self.draw_label('Type your quiz description.')
		tk.Button(text = 'OK', command = save).pack(side = 'bottom', anchor = 's')

		scroll = tk.Scrollbar(orient = 'vertical')
		entry = tk.Text(width = self.display_w, yscrollcommand = scroll.set)
		entry.insert('end', self.datafile['description'])
		scroll.config(command = entry.yview)
		scroll.pack(side = tk.RIGHT, fill = 'y')
		entry.pack(side = tk.LEFT)

	def quiz_conf(self):
		if not self.jsonhandler.check_element('lives', int): self.datafile['lives'] = 0
		if not self.jsonhandler.check_element('randomize', bool): self.datafile['randomize'] = False
		if not self.jsonhandler.check_element('showcount', bool): self.datafile['showcount'] = True
		if not self.jsonhandler.check_element('wrongmsg', list): self.datafile['wrongmsg'] = []
		if not self.jsonhandler.check_element('fail'): self.datafile['fail'] = ''
		if not self.jsonhandler.check_element('finish'): self.datafile['finish'] = ''

		def save():
			text = life_entry.get()
			try:
				if int(text) != self.datafile['lives']:
					self.datafile['lives'] = int(text)
					self.modified = True
			except ValueError:
				if text == '': tk.messagebox.showerror('Error', 'Life count cannot be blank!')
				else: tk.messagebox.showerror('Error', 'Life count must only contain an integer!')
			randval = rand_value.get()
			if randval != self.datafile['randomize']:
				self.datafile['randomize'] = randval
				self.modified = True

			scval = showcount_value.get()
			if scval != self.datafile['showcount']:
				self.datafile['showcount'] = scval
				self.modified = True
			
			self.set_title()

		def reset():
			if self.datafile['lives'] != 0: self.modified = True
			self.datafile['lives'] = 0
			if self.datafile['randomize']: self.modified = True
			self.datafile['randomize'] = False
			if not self.datafile['showcount']: self.modified = True
			self.datafile['showcount'] = True
			if self.datafile['wrongmsg'] != []: self.modified = True
			self.datafile['wrongmsg'] = []
			if self.datafile['fail'] != '': self.modified = True
			self.datafile['fail'] = ''
			if self.datafile['finish'] != '': self.modified = True
			self.datafile['finish'] = ''
			self.refresh()
			self.set_title()
			self.quiz_conf()

		def back(): self.refresh(True)

		self.refresh()
		self.draw_label('Quiz settings')
		tk.Button(text = 'Back', command = back).pack(side = 'bottom', anchor = 's')
		tk.Button(text = 'Reset to defaults', command = reset).pack(side = 'bottom', anchor = 's')
		tk.Button(text = 'Apply', command = save).pack(side = 'bottom', anchor = 's')

		life_frame = tk.Frame()
		self.draw_label(f'Lives (0 = disabled)', master = life_frame, side = 'left')
		life_entry = tk.Entry(life_frame, width = 10, justify = 'right')
		life_entry.insert(0, str(self.datafile['lives']))
		life_entry.pack(side = 'right')
		life_frame.pack(fill = 'x')

		rand_frame = tk.Frame()
		self.draw_label(f'Randomize question order', master = rand_frame, side = 'left')
		rand_value = tk.BooleanVar()
		rand_value.set(self.datafile['randomize'])
		rand_checkbox = tk.Checkbutton(rand_frame, variable = rand_value)
		rand_checkbox.pack(side = 'right')
		rand_frame.pack(fill = 'x')

		showcount_frame = tk.Frame()
		self.draw_label(f'Show question count', master = showcount_frame, side = 'left')
		showcount_value = tk.BooleanVar()
		showcount_value.set(self.datafile['showcount'])
		showcount_checkbox = tk.Checkbutton(showcount_frame, variable = showcount_value)
		showcount_checkbox.pack(side = 'right')
		showcount_frame.pack(fill = 'x')

	"""----------- END MENUS ---------"""

class JSONHandler(object):
	def __init__(self, gui):
		self.datafile_new = {'title': 'My Quiz', 'questions': [{'question': 'Question', 'a': 'Answer A', 'b': 'Answer B', 'c': 'Answer C', 'd': 'Answer D', 'correct': 'a'}]}
		self.new_quiz()

		self.savepath = ''
		self.savepath_tmp = ''
		self.message =  ('', False)

		self.gui = gui

	def reload_dtfile(self): self.datafile = self.gui.datafile

	def reload(self):
		self.reload_dtfile()
		self.datafile = self.datafile_bak
		self.create_backup()
		self.gui.datafile = self.datafile.copy()
		self.gui.datafile['questions'] = self.datafile['questions'].copy()

	def create_backup(self):
		self.datafile_bak = self.datafile.copy()
		self.datafile_bak['questions'] = self.datafile['questions'].copy()

	def new_quiz(self):
		self.datafile = self.datafile_new.copy()
		self.datafile['questions'] = self.datafile_new['questions'].copy()
		self.create_backup()

	def open_file(self):
		self.savepath_tmp = ''
		self.savepath_tmp = tk.filedialog.askopenfilename(initialdir = os.path.dirname(self.savepath) if self.savepath else os.getcwd(), filetypes = [('QuizProg-GUI Quiz Projects', '*.qpg'), ('QuizProg Quiz Projects', '*.json'), ('All Files', '*.*')], defaultextension = '.qpg')
		if self.savepath_tmp:
			if os.path.splitext(self.savepath_tmp)[1].casefold() == '.json':
				if not tk.messagebox.askyesno('Note for JSON files', 'The file you are trying to open is a (console) QuizProg quiz project. However, these quiz projects are limited to the features in (console) QuizProg.\nRight now you are not required to save this file as a QuizProg-GUI quiz project until you want to use new features present in QuizProg-GUI.\nDo you want to continue?'): return False
			old_path = self.savepath
			self.savepath = self.savepath_tmp
			if os.name == 'nt': self.savepath = self.savepath.replace('/', '\\')
			try:
				success = False
				for i in range(1):
					try: self.datafile = json.load(open(self.savepath, encoding = 'utf-8'))
					except (json.decoder.JSONDecodeError, UnicodeDecodeError): message = 'Invalid JSON data!'; self.savepath = old_path; break
					if not self.check_element('title', rel = False): message = 'String variable "title" not found or empty!'; self.savepath = old_path; break
					if not self.check_element('questions', list, rel = False): message = 'String variable "questions" not found or empty!'; self.savepath = old_path; break
					for i in range(len(self.datafile['questions'])):
						if not self.check_question_element('question', i, rel = False): message = f'String variable "question" not found or empty in question ' + str(i+1) + '!'; success = False; self.savepath = old_path; break
						if not self.check_question_element('a', i, rel = False): message = f'String variable "a" not found or empty in question {i+1}!'; success = False; self.savepath = old_path; break
						if not self.check_question_element('b', i, rel = False): message = f'String variable "b" not found or empty in question {i+1}!'; success = False; self.savepath = old_path; break
						if not self.check_question_element('c', i, rel = False): message = f'String variable "c" not found or empty in question {i+1}!'; success = False; self.savepath = old_path; break
						if not self.check_question_element('d', i, rel = False): message = f'String variable "d" not found or empty in question {i+1}!'; success = False; self.savepath = old_path; break
						if not self.check_question_element('correct', i, rel = False): message = f'String variable "correct" not found or empty in question {i+1}!'; success = False; self.savepath = old_path; break
						success = True
					if not success: break
					self.create_backup()
					message = f'Loaded quiz: {self.savepath}'
				if not success:
					self.reload_dtfile()
					self.create_backup()
			except IOError as e: message = f'Can\'t open file: {e.strerror}'

			self.message = (message, not success)
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
			except IOError as e: message = f'Can\'t save file: {e.strerror}'

			self.message = (message, not success)
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