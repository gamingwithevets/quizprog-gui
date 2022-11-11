import os
import re
import sys
import json
import traceback
import tkinter as tk
import tkinter.font
import tkinter.messagebox
import tkinter.filedialog

def report_error(self, exc, val, tb):
	try: GUI.window.quit()
	except Exception: pass
	print(f'Whoops! QuizProg-GUI has suffered a very fatal error.\n\n{traceback.format_exc()}\nIf this error persists, please report it here:\nhttps://github.com/gamingwithevets/quizprog-gui/issues')
	tk.messagebox.showerror('Whoops!', f'QuizProg-GUI has suffered a very fatal error.\n\n{traceback.format_exc()}\nIf this error persists, please report it here:\nhttps://github.com/gamingwithevets/quizprog-gui/issues')
	sys.exit()

tk.Tk.report_callback_exception = report_error

version = 'Beta 1.0.2'
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

		self.message = ('Welcome to QuizProg-GUI! Any save-related messages will appear here.', False)
		self.datafile = {'title': 'My Quiz', 'questions': [{'question': 'Question', 'a': 'Answer A', 'b': 'Answer B', 'c': 'Answer C', 'd': 'Answer D', 'correct': 'a'}]}
		self.datafile_mode = 'json'

		self.savepath = ''
		self.allowsave = True

		self.modified = False

		self.jsonhandler = JSONHandler(self)
		self.quizconf = QuizConf(self)
		self.init_window()
		self.menubar()
		self.init_protocols()
		
		self.main_menu()

	def n_a(self): tk.messagebox.showinfo('Not implemented', 'This feature is not implemented into QuizProg-GUI... yet.\nSorry!')

	def refresh(self, load_func = False, custom_func = None):
		for w in self.window.winfo_children(): w.destroy()
		self.menubar()
		self.set_title()

		if load_func:
			if custom_func == None: self.main_menu()
			else: custom_func() 

	def quit(self):
		cancel = self.prompt_save_changes()
		if cancel: return

		self.window.quit()
		sys.exit()

	def set_title(self):
		if self.modified: self.window.title(f'QuizProg-GUI - {self.datafile["title"]}{f" - {self.savepath}" if self.savepath else ""}*')
		else: self.window.title(f'QuizProg-GUI - {self.datafile["title"]}{f" - {self.savepath}" if self.savepath else ""}')

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

	def draw_blank(self, side = 'top', anchor = 'center', recwidth = None, recheight = None, master = None):
		if master == None: master = self.window
		self.draw_label('', side = side, anchor = anchor, recwidth = recwidth, recheight = recheight, master = master)

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
			#else: self.datafile_mode = 'qpg'
			else: self.datafile_mode = 'json'
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
		self.print_msg()

		self.draw_label('You are editing:')
		try: self.draw_label(self.datafile['title'], font = (f'{self.font_name}', f'{self.font_size}', 'bold'))
		except Exception: self.draw_label(self.datafile['title'])
		self.draw_label(f'Quiz format: {self.datafile_mode.upper()}')
		tk.Button(text = 'Quiz settings', command = self.quiz_conf).pack(side = 'bottom')
		tk.Button(text = 'Edit quiz questions').pack(side = 'bottom')
		self.draw_blank(side = 'bottom')
		tk.Button(text = 'Edit quiz description', command = self.quiz_desc).pack(side = 'bottom')
		tk.Button(text = 'Rename quiz', command = self.quiz_name).pack(side = 'bottom')

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
			else: tk.messagebox.showerror('Error', 'Quiz name cannot be blank!')

		def discard():
			if tk.messagebox.askyesno('Discard', 'Discard changes?'): self.menu()

		self.refresh()
		self.draw_label('Type your quiz name.')
		tk.Button(text = 'OK', command = save).pack(side = 'bottom', anchor = 's')
		tk.Button(text = 'Discard', command = discard).pack(side = 'bottom', anchor = 's')
		
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
			text = self.format_text(entry.get('1.0', 'end-1c'))
			if text != self.datafile['description']:
				self.datafile['description'] = re.sub(r'\n+', '\n', text)
				self.modified = True
			if self.datafile['description'] == '': del self.datafile['description']
			self.refresh(True)

		self.refresh()
		self.draw_label('Type your quiz description.')
		tk.Button(text = 'OK', command = save).pack(side = 'bottom', anchor = 's')

		scroll = tk.Scrollbar(orient = 'vertical')
		entry = tk.Text(width = self.display_w, yscrollcommand = scroll.set, wrap = 'word')
		entry.insert('end', self.datafile['description'])
		scroll.config(command = entry.yview)
		scroll.pack(side = 'right', fill = 'y')
		entry.focus()
		entry.pack(side = 'left')

	def quiz_conf(self): self.quizconf.main()

	"""----------- END MENUS ---------"""

class QuizConf():
	def __init__(self, gui):
		self.gui = gui

		self.display_w = self.gui.display_w
		self.jsonhandler = self.gui.jsonhandler
		self.refresh = self.gui.refresh
		self.draw_label = self.gui.draw_label
		self.format_text = self.gui.format_text

		self.wrongmsg_editor = WrongMsg_Editor(self.gui, self)

	def main(self):
		self.datafile = self.gui.datafile

		if not self.jsonhandler.check_element('lives', int): self.datafile['lives'] = 0
		if not self.jsonhandler.check_element('randomize', bool): self.datafile['randomize'] = False
		if not self.jsonhandler.check_element('showcount', bool): self.datafile['showcount'] = True
		if not self.jsonhandler.check_element('wrongmsg', list): self.datafile['wrongmsg'] = []
		if not self.jsonhandler.check_element('fail'): self.datafile['fail'] = ''
		if not self.jsonhandler.check_element('finish'): self.datafile['finish'] = ''

		self.wrongmsg_list = self.datafile['wrongmsg']
		self.fail_text = self.datafile['fail']
		self.finish_text = self.datafile['finish']

		self.menu()

	def menu(self):
		self.refresh()
		self.draw_label('Quiz settings', font = (f'{self.gui.font_name}', f'{self.gui.font_size}', 'bold'))
		tk.Button(text = 'Back', command = self.back).pack(side = 'bottom', anchor = 's')
		tk.Button(text = 'Reset to defaults', command = self.reset).pack(side = 'bottom', anchor = 's')
		tk.Button(text = 'Apply', command = self.save).pack(side = 'bottom', anchor = 's')
		self.draw_label('* Click Apply to save changes to this setting', side = 'bottom')

		life_frame = tk.Frame()
		self.draw_label(f'Lives (0 = disabled)*', master = life_frame, side = 'left')
		self.life_entry = tk.Entry(life_frame, width = 10, justify = 'right')
		self.life_entry.insert(0, str(self.datafile['lives']))
		self.life_entry.pack(side = 'right')
		life_frame.pack(fill = 'x')

		rand_frame = tk.Frame()
		self.draw_label(f'Randomize question order*', master = rand_frame, side = 'left')
		self.rand_value = tk.BooleanVar()
		self.rand_value.set(self.datafile['randomize'])
		rand_checkbox = tk.Checkbutton(rand_frame, variable = self.rand_value)
		rand_checkbox.pack(side = 'right')
		rand_frame.pack(fill = 'x')

		showcount_frame = tk.Frame()
		self.draw_label(f'Show question count*', master = showcount_frame, side = 'left')
		self.showcount_value = tk.BooleanVar()
		self.showcount_value.set(self.datafile['showcount'])
		showcount_checkbox = tk.Checkbutton(showcount_frame, variable = self.showcount_value)
		showcount_checkbox.pack(side = 'right')
		showcount_frame.pack(fill = 'x')

		wrongmsg_frame = tk.Frame()
		self.draw_label(f'Global wrong answer comments', master = wrongmsg_frame, side = 'left')
		tk.Button(wrongmsg_frame, text = 'Edit', command = self.wrongmsg_editor.main).pack(side = 'right')
		if len(self.datafile['wrongmsg']) == 0: self.draw_label('None  ', master = wrongmsg_frame, side = 'right')
		else: self.draw_label(f'{len(self.datafile["wrongmsg"])} comment{"s" if len(self.datafile["wrongmsg"]) > 1 else ""}  ', master = wrongmsg_frame, side = 'right')
		wrongmsg_frame.pack(fill = 'x')

		fail_frame = tk.Frame()
		self.draw_label(f'Game over comment (requires lives to be enabled)', master = fail_frame, side = 'left')
		tk.Button(fail_frame, text = 'Edit', command = self.fail_edit).pack(side = 'right')
		fail_frame.pack(fill = 'x')

		win_frame = tk.Frame()
		self.draw_label(f'Quiz completion comment', master = win_frame, side = 'left')
		tk.Button(win_frame, text = 'Edit', command = self.finish_edit).pack(side = 'right')
		win_frame.pack(fill = 'x')

	def fail_edit(self):
		def save():
			text = self.format_text(entry.get('1.0', 'end-1c'))
			if text != self.fail_text:
				self.fail_text = text
				self.gui.modified = True
			self.menu()

		self.refresh()
		self.draw_label('Type your quiz game over comment.')
		tk.Button(text = 'OK', command = save).pack(side = 'bottom', anchor = 's')

		scroll = tk.Scrollbar(orient = 'vertical')
		entry = tk.Text(width = self.display_w, yscrollcommand = scroll.set)
		entry.insert('end', self.fail_text)
		scroll.config(command = entry.yview)
		scroll.pack(side = 'right', fill = 'y')
		entry.pack(side = 'left')

	def finish_edit(self):
		def save():
			text = self.format_text(entry.get('1.0', 'end-1c'))
			if text != self.finish_text:
				self.finish_text = text
				self.gui.modified = True
			self.menu()

		self.refresh()
		self.draw_label('Type your quiz completion comment.')
		tk.Button(text = 'OK', command = save).pack(side = 'bottom', anchor = 's')

		scroll = tk.Scrollbar(orient = 'vertical')
		entry = tk.Text(width = self.display_w, yscrollcommand = scroll.set)
		entry.insert('end', self.finish_text)
		scroll.config(command = entry.yview)
		scroll.pack(side = 'right', fill = 'y')
		entry.pack(side = 'left')

	def save(self):
		lives_text = self.life_entry.get()
		try:
			if int(lives_text) != self.datafile['lives']:
				if int(lives_text) < 0: tk.messagebox.showerror('Error', 'Life count cannot be negative!'); return
				else:
					self.datafile['lives'] = int(lives_text)
					self.gui.modified = True
		except ValueError:
			if lives_text == '': tk.messagebox.showerror('Error', 'Life count cannot be blank!'); return
			else: tk.messagebox.showerror('Error', 'Life count must only contain an integer!'); return
		randval = self.rand_value.get()
		if randval != self.datafile['randomize']:
			self.datafile['randomize'] = randval
			self.gui.modified = True

		scval = self.showcount_value.get()
		if scval != self.datafile['showcount']:
			self.datafile['showcount'] = scval
			self.gui.modified = True

		self.end()

	def reset(self):
		if self.datafile['lives'] != 0: self.gui.modified = True
		if self.datafile['randomize']: self.gui.modified = True
		if not self.datafile['showcount']: self.gui.modified = True
		if self.datafile['wrongmsg'] != []: self.gui.modified = True
		if self.datafile['fail'] != '': self.gui.modified = True
		if self.datafile['finish'] != '': self.gui.modified = True

		self.datafile['lives'] = 0
		self.datafile['randomize'] = False
		self.datafile['showcount'] = True
		self.datafile['wrongmsg'] = []
		self.datafile['fail'] = ''
		self.datafile['finish'] = ''
		self.menu()

	def back(self):
		modified = False

		lives_text = self.life_entry.get()
		try:
			if int(lives_text) != self.datafile['lives']: modified = True
		except ValueError: modified = True

		randval = self.rand_value.get()
		if randval != self.datafile['randomize']: modified = True

		scval = self.showcount_value.get()
		if scval != self.datafile['showcount']: modified = True

		if self.wrongmsg_list != self.datafile['wrongmsg']: modified = True
		if self.fail_text != self.datafile['fail']: modified = True
		if self.finish_text != self.datafile['finish']: modified = True

		if modified:
			if tk.messagebox.askyesno('Abandon changes?', 'Your changes won\'t be saved. Abandon these changes?', icon = 'warning'): self.end()
		else: self.end()

	def end(self):
		if self.datafile['lives'] == 0: del self.datafile['lives']
		if not self.datafile['randomize']: del self.datafile['randomize']
		if self.datafile['showcount']: del self.datafile['showcount']
		if self.datafile['wrongmsg'] == []: del self.datafile['wrongmsg']
		if self.datafile['fail'] == '': del self.datafile['fail']
		if self.datafile['finish'] == '': del self.datafile['finish']

		self.gui.datafile = self.datafile
		self.refresh(True)

class WrongMsg_Editor():
	def __init__(self, gui, quizconf):
		self.gui = gui
		self.quizconf = quizconf

		self.refresh = self.gui.refresh
		self.display_w = self.gui.display_w
		self.draw_label = self.gui.draw_label
		self.draw_blank = self.gui.draw_blank
		self.format_text = self.gui.format_text

	def main(self):
		self.wrongmsg = self.quizconf.wrongmsg_list

		self.index = 0

		self.menu()

	def navigation_prev(self): self.index -= 1; self.menu()
	def navigation_next(self): self.index += 1; self.menu()

	def menu(self):
		self.refresh()
		self.draw_label('Global wrong answer comments', font = (f'{self.gui.font_name}', f'{self.gui.font_size}', 'bold'))
		tk.Button(text = 'Back', command = self.end).pack(side = 'bottom')
		self.draw_blank(side = 'bottom')

		if len(self.wrongmsg) == 0:
			self.draw_label('No global wrong answer comments!')
			tk.Button(text = 'Create new comment', command = self.new).pack(side = 'bottom')
		else:
			self.draw_label(f'{self.index + 1} / {len(self.wrongmsg)}')
			tk.Button(text = 'Delete comment', command = self.delete).pack(side = 'bottom')
			tk.Button(text = 'Edit comment', command = self.edit).pack(side = 'bottom')
			tk.Button(text = 'Create new comment', command = self.new).pack(side = 'bottom')
			self.draw_blank(side = 'bottom')
			nav_frame = tk.Frame()
			prev_bt = tk.Button(nav_frame, text = 'Previous', command = self.navigation_prev)
			next_bt = tk.Button(nav_frame, text = 'Next', command = self.navigation_next)
			if len(self.wrongmsg) > 1:
				if self.index == 0: next_bt.pack(side = 'right')
				elif self.index == len(self.wrongmsg) - 1: prev_bt.pack(side = 'left')
				else: prev_bt.pack(side = 'left'); next_bt.pack(side = 'right')
			nav_frame.pack(side = 'bottom', fill = 'x')

			scroll = tk.Scrollbar(orient = 'vertical')
			text = tk.Text(width = self.display_w, yscrollcommand = scroll.set, wrap = 'word')
			text.insert('end', self.wrongmsg[self.index])
			text.bind('<Key>', self.romsg)
			scroll.config(command = text.yview)
			scroll.pack(side = 'right', fill = 'y')
			text.pack(side = 'left')

	def romsg(self, event):
		tk.messagebox.showwarning('Text read-only', 'Sorry, this text is READ-ONLY. To edit it, click "Edit comment" instead.\nThank you!')
		return 'break'

	def new(self):
		def save():
			text = self.format_text(entry.get('1.0', 'end-1c'))
			if len(self.wrongmsg) > 0:
				for i in range(len(self.wrongmsg)):
					if text == self.wrongmsg[i]:
						tk.messagebox.showerror('Error', f'Duplicate global wrong answer comment detected!\nDuplicate of comment w/ index {i + 1} / {len(self.wrongmsg)}')
						return
			if text != '':
				self.wrongmsg.append(text)
				self.gui.modified = True
				self.index = len(self.wrongmsg) - 1
			self.menu()

		def discard():
			if tk.messagebox.askyesno('Discard', 'Discard this comment?'): self.menu()

		self.refresh()
		self.draw_label('Type your global wrong answer comment.')
		tk.Button(text = 'OK', command = save).pack(side = 'bottom', anchor = 's')
		tk.Button(text = 'Discard', command = discard).pack(side = 'bottom', anchor = 's')

		scroll = tk.Scrollbar(orient = 'vertical')
		entry = tk.Text(width = self.display_w, yscrollcommand = scroll.set, wrap = 'word')
		scroll.config(command = entry.yview)
		scroll.pack(side = 'right', fill = 'y')
		entry.focus()
		entry.pack(side = 'left')

	def edit(self):
		def save():
			text = self.format_text(entry.get('1.0', 'end-1c'))
			if len(self.wrongmsg) > 0:
				for i in range(len(self.wrongmsg)):
					if i != self.index and text == self.wrongmsg[i]:
						tk.messagebox.showerror('Error', f'Duplicate global wrong answer comment detected!\nDuplicate of comment w/ index {i + 1} / {len(self.wrongmsg)}')
						return
			if text != '':
				self.wrongmsg[self.index] = text
				self.gui.modified = True
				self.index = len(self.wrongmsg) - 1
			self.menu()

		def discard():
			text = self.format_text(entry.get('1.0', 'end-1c'))
			if text != self.wrongmsg[self.index]:
				if tk.messagebox.askyesno('Discard', 'Discard changes to this comment?'): self.menu()
			else: self.menu()

		self.refresh()
		self.draw_label('Type your global wrong answer comment.')
		tk.Button(text = 'OK', command = save).pack(side = 'bottom', anchor = 's')
		tk.Button(text = 'Discard', command = discard).pack(side = 'bottom', anchor = 's')

		scroll = tk.Scrollbar(orient = 'vertical')
		entry = tk.Text(width = self.display_w, yscrollcommand = scroll.set, wrap = 'word')
		entry.insert('end', self.wrongmsg[self.index])
		scroll.config(command = entry.yview)
		scroll.pack(side = 'right', fill = 'y')
		entry.focus()
		entry.pack(side = 'left')

	def delete(self):
		if tk.messagebox.askyesno('Delete this comment?', 'Are you sure you want to delete this comment?'):
			del self.wrongmsg[self.index]
			if len(self.wrongmsg) > 0: self.index -= 1
			else: self.index = 0
			self.modified = True
			self.refresh()
			self.menu()


	def end(self):
		self.quizconf.wrongmsg_list = self.wrongmsg
		self.quizconf.menu()

class JSONHandler():
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
				#if not tk.messagebox.askyesno('Note for JSON files', 'The file you are trying to open is a (console) QuizProg quiz project. However, these quiz projects are limited to the features in (console) QuizProg.\nRight now you are not required to save this file as a QuizProg-GUI quiz project until you want to use new features present in QuizProg-GUI.\nDo you want to continue?'): return False
				tk.messagebox.showinfo('Note for JSON files', 'The file you are trying to open is a (console) QuizProg quiz project. However, these quiz projects are limited to the features in (console) QuizProg.\nHowever, the new features of the QPG format aren\'t implemented yet, so I\'ll let you open this without any problems.\n\n...for now.')
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