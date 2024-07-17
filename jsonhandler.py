import os
import copy
import json
import tkinter as tk
import tkinter.filedialog

class JSONHandler:
	def __init__(self, gui, report_error, fmt_oserror):
		self.gui = gui
		self.report_error = report_error
		self.fmt_oserror = fmt_oserror

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
		filetypes = [('All supported types', '*.qpg *.json'), ('QuizProg-GUI Quiz Projects', '*.qpg'), ('QuizProg Quiz Projects', '*.json'), ('All Files', '*.*')]
		defaultextension = '.json'

		self.savepath_tmp = ''
		self.savepath_tmp = tk.filedialog.askopenfilename(initialdir = os.path.dirname(self.savepath) if self.savepath else os.getcwd(), filetypes = filetypes, defaultextension = defaultextension)
		if self.savepath_tmp:
			if os.path.splitext(self.savepath_tmp)[1].casefold() == '.json':
				pass#if not tk.messagebox.askyesno('Note for JSON files', 'The file you are trying to open is a (console) QuizProg quiz project. However, these quiz projects are limited to the features in (console) QuizProg.\nRight now you are not required to save this file as a QuizProg-GUI quiz project until you want to use new features present in QuizProg-GUI.\nDo you want to continue?'): return False
			success, message = self.check_json(self.savepath_tmp)
			if success: self.gui.message = message
			else: self.gui.message_force = message
			return success
		else: return False

	def check_json(self, path):
		old_path = self.savepath
		self.savepath = path
		if os.name == 'nt': self.savepath = self.savepath.replace('/', '\\')
		try:
			success = False
			for i in range(1):
				try: self.datafile = json.load(open(self.savepath, encoding = 'utf-8'))
				except OSError as exc: message = self.fmt_oserror(exc); self.savepath = old_path; break
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
		except OSError: report_error(*sys.exc_info())

		return success, message

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
				with open(self.savepath, 'w', encoding = 'utf-8') as f: f.write(json.dumps(self.datafile, ensure_ascii = False, indent = 4))
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
