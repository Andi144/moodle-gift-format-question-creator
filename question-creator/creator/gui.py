import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.messagebox import askyesno, showerror
from tkinter.scrolledtext import ScrolledText

import inout
from data import Answer, Question, Category


class QuestionFrame(ttk.Frame):
    
    def __init__(self, master, question: Question, **kwargs):
        super().__init__(master, **kwargs)
        # GUI setup
        self.frame = ttk.Frame(self.master)
        self.frame.pack(fill=tk.BOTH, side=tk.TOP, expand=True)
        inner_frame = ttk.Frame(self.frame)
        inner_frame.pack(side=tk.LEFT)
        self.id_label = ttk.Label(inner_frame)
        self.id_label.pack(side=tk.TOP)
        # TODO: question title entry
        # mode GUI elements
        label = ttk.Label(inner_frame, text="Mode:")
        label.pack(side=tk.TOP)
        # TODO: rename GUI elements (e.g., combobox -> mode_combobox)
        self.combobox = ttk.Combobox(inner_frame, values=Question.MODES, state="readonly", width=6)
        self.combobox.set(question.mode)
        self.combobox.pack(side=tk.TOP)
        # category GUI elements
        label = ttk.Label(inner_frame, text="Category:")
        label.pack(side=tk.TOP)
        self.entry = ttk.Entry(inner_frame, width=20)
        self.entry.insert(0, "" if question.category is None else question.category.name)
        self.entry.pack(side=tk.TOP)
        # textbox for main question text
        self.textbox = ScrolledText(self.frame, width=100, height=10)
        self.textbox.insert("1.0", question.text)
        self.textbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    def set_state(self, question: Question):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, "" if question.category is None else question.category.name)
        self.combobox.set(question.mode)
        self.textbox.replace("1.0", tk.END, question.text)
    
    def get_state(self):
        mode = self.combobox.get()
        category_name = self.entry.get()
        category = None if not category_name.strip() else Category(category_name)
        text = self.textbox.get("1.0", tk.END)[:-1]  # last char = \n
        return mode, category, text


class AnswerFrame(ttk.Frame):
    
    def __init__(self, master: "AnswersFrame", answer: Answer, index: int, **kwargs):
        super().__init__(master, **kwargs)
        self.answer = answer
        # GUI setup
        self.pack(fill=tk.BOTH, side=tk.TOP, expand=True)
        self.label = ttk.Label(self, text=f"{index + 1})")
        self.label.pack(side=tk.LEFT)
        # textbox for main answer text
        self.textbox = ScrolledText(self, width=100, height=5)
        self.textbox.insert("1.0", answer.text)
        self.textbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # correct checkbox and remove answer button
        frame = ttk.Frame(self)
        frame.pack(side=tk.LEFT)
        self.checkbox_var = tk.BooleanVar(frame, value=answer.correct)
        checkbox = ttk.Checkbutton(frame, text="Correct", variable=self.checkbox_var)
        checkbox.pack(side=tk.TOP)
        self.button = ttk.Button(frame, text="Remove", command=lambda: master.remove_answer(self.answer))
        self.button.pack(side=tk.TOP)
    
    def set_state(self, answer: Answer):
        self.answer = answer
        self.textbox.replace("1.0", tk.END, answer.text)
        self.checkbox_var.set(answer.correct)
    
    def get_state(self):
        text = self.textbox.get("1.0", tk.END)[:-1]  # last char = \n
        correct = self.checkbox_var.get()
        return text, correct


class AnswersFrame(ttk.Frame):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frames: list[AnswerFrame] = []
    
    def add_answer(self, answer: Answer = None):
        if answer is None:
            answer = Answer(text="new answer", correct=False)
        frame = AnswerFrame(self, answer, len(self.frames))
        self.frames.append(frame)
    
    def remove_answer(self, answer: Answer = None):
        if self.frames and answer is None:
            # remove the last one, so we do not have to adjust the label indices
            self.frames.pop(-1).destroy()
            return
        # if the answer is specified, we need to search for it, remove it and
        # adjust all following label indices (decrement by 1)
        index_to_remove = -1
        for i, frame in enumerate(self.frames):
            if frame.answer == answer:
                index_to_remove = i
                break
        assert index_to_remove != -1, "specified answer was not found in this AnswersFrame"
        self.frames.pop(index_to_remove).destroy()
        # need to adjust the label indices of all following answers
        for i in range(index_to_remove, len(self.frames)):
            self.frames[i].label.config(text=f"{i + 1})")
    
    def n_answers(self):
        return len(self.frames)
    
    def get_state(self):
        return [Answer(*f.get_state()) for f in self.frames]


class QuestionCreator:
    
    @staticmethod
    def create_new_question(question: Question = None, n_answers: int = 4):
        if question is not None:
            # use the current question mode and category and the same number of answers
            # which is usually the same for new questions (in the same exam)
            category = question.category
            mode = question.mode
            n_answers = len(question.answers)
        else:
            mode = Question.MODE_MULTI
            category = None
            n_answers = n_answers
        # mark exactly one answer as correct to avoid potential issues with mode 'single'
        answers = [Answer(text=f"answer {i + 1}", correct=i == 0) for i in range(n_answers)]
        return Question(category=category, text="question", answers=answers, mode=mode)
    
    def __init__(self, file=None):
        # always create one dummy question at startup so self._init_setup creates all
        # necessary GUI elements
        self.questions: list[Question] = [QuestionCreator.create_new_question()]
        self.cqi: int = 0  # current question index
        self.file = file
        self.changes = False  # whether there are changes not yet stored to a file
        
        # GUI elements and containers + setup
        self.window = tk.Tk()
        self.window.bind("<Control-o>", lambda event: self._open_file())
        self.window.bind("<Control-s>", lambda event: self._save_file(self.file))
        self.window.bind("<Alt-Left>", lambda event: self._prev_question())
        self.window.bind("<Alt-Right>", lambda event: self._next_question())
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        self._init_setup()
        
        if file is not None:
            self._open_file(file)
    
    def _init_setup(self):
        # buttons for opening/storing questions
        button_frame = ttk.Frame(self.window)
        button_frame.pack(side=tk.TOP)
        button_open = ttk.Button(button_frame, text="Open...", width=10, command=self._open_file)
        button_open.pack(side=tk.LEFT)
        button_save = ttk.Button(button_frame, text="Save", width=10, command=lambda: self._save_file(self.file))
        button_save.pack(side=tk.LEFT)
        button_save_as = ttk.Button(button_frame, text="Save as...", width=10, command=self._save_file)
        button_save_as.pack(side=tk.LEFT)
        
        # GUI elements for the question
        cq = self.questions[self.cqi]
        self.question_frame = QuestionFrame(self.window, cq)
        self.question_frame.id_label.config(text=f"Q {self.cqi + 1}/{len(self.questions)}:")
        
        # GUI elements for answers
        self.answers_frame = AnswersFrame(self.window)
        self.answers_frame.pack(fill=tk.BOTH, side=tk.TOP, expand=True)
        for answer in cq.answers:
            self.answers_frame.add_answer(answer)
        # button for adding new answer
        button_add_answer = ttk.Button(self.window, text="Add new answer", command=self.answers_frame.add_answer)
        button_add_answer.pack(side=tk.TOP)
        
        # buttons for showing previous/next question + adding/removing question
        button_frame = ttk.Frame(self.window)
        button_frame.pack(side=tk.TOP)
        button_prev = ttk.Button(button_frame, text="< prev", width=10, command=self._prev_question)
        button_prev.pack(side=tk.LEFT)
        button_add = ttk.Button(button_frame, text="Add new question", width=16, command=self._add_new_question)
        button_add.pack(side=tk.LEFT)
        button_rem = ttk.Button(button_frame, text="Remove question", width=16, command=self._remove_question)
        button_rem.pack(side=tk.LEFT)
        button_next = ttk.Button(button_frame, text="next >", width=10, command=self._next_question)
        button_next.pack(side=tk.LEFT)
    
    def _reload(self):
        cq = self.questions[self.cqi]
        
        # question GUI elements updates
        self.question_frame.set_state(cq)
        self.question_frame.id_label.config(text=f"Q {self.cqi + 1}/{len(self.questions)}:")
        
        # question answers GUI elements updates
        # special handling in case the new current question has fewer or more answers
        diff = len(cq.answers) - self.answers_frame.n_answers()
        if diff > 0:
            # must add answer frames for the missing answers (no need to add the answers
            # from the question here, since this is done below (setting answers) anyway)
            for i in range(diff):
                self.answers_frame.add_answer()
        elif diff < 0:
            # must remove the superfluous answer frames
            for i in range(abs(diff)):
                self.answers_frame.remove_answer()
        # setting answers
        assert len(cq.answers) == self.answers_frame.n_answers()
        for frame, answer in zip(self.answers_frame.frames, cq.answers):
            frame.set_state(answer)
    
    def _save_changes(self, validate: bool = True):
        cq = self.questions[self.cqi]
        
        mode, category, text = self.question_frame.get_state()
        answers = self.answers_frame.get_state()
        
        # if there are not already changes, detect any changes before overwriting the current question
        if not self.changes:
            # TODO: maybe make a copy, overwrite the copy and compare original with changed copy using ==
            self.changes = cq.mode != mode or cq.category != category or cq.text != text or len(cq.answers) != len(
                answers) or any([a1 != a2 for a1, a2 in zip(cq.answers, answers)])
        
        cq.mode = mode
        cq.category = category
        cq.text = text
        cq.answers = answers
        
        if validate:
            if cq.mode == Question.MODE_SINGLE and len([a for a in cq.answers if a.correct]) != 1:
                showerror(title="Error: Could not save changes",
                          message=f"Must have exactly one correct answer if question mode is '{cq.mode}'.")
                return False
            if not cq.text.strip():
                showerror(title="Error: Could not save changes", message=f"Main question text must not be empty.")
                return False
            for answer in cq.answers:
                if not answer.text.strip():
                    showerror(title="Error: Could not save changes", message=f"Answer texts must not be empty.")
                    return False
        
        return True
    
    def _add_new_question(self):
        if self.questions:
            # only save changes if there is at least one (the current) question
            save_successful = self._save_changes()
            if not save_successful:
                return
        question = QuestionCreator.create_new_question(self.questions[self.cqi])
        self.cqi += 1  # insert it after the current question, which is more logical
        self.questions.insert(self.cqi, question)
        self.changes = True
        self._reload()
    
    def _remove_question(self):
        yes = askyesno(title="Confirmation", message="Are you sure you want to remove the current question?")
        if yes:
            self.questions.pop(self.cqi)
            if not self.questions:
                # if the last question was removed, add a new empty one, so we always
                # have one active question to avoid running out of index bounds
                self.questions.append(QuestionCreator.create_new_question())
            elif self.cqi > len(self.questions) - 1:
                # if the question at the end of the list was removed, reduce the
                # current question index by 1 to avoid running out of index bounds
                self.cqi -= 1
            self.changes = True
            self._reload()
    
    def _open_file(self, file=None):
        if self.changes:
            yes = askyesno(title="Unsaved changes", message="There are unsaved changes in the current file. Do you "
                                                            "want to open a new file anyway (changes are lost)?")
            if not yes:
                return
        if file is None:
            file = askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if not file:
            return
        self.file = file
        try:
            questions = inout.read_gift(file)
        except (ValueError, FileNotFoundError) as e:
            showerror(title="Error", message=f"Could not open file:\n\n{e}")
            # set window to be focused so key binds will work again
            self.window.focus_force()
        else:
            if not questions:
                showerror(title="Error", message=f"The requested file does not contain any questions.")
                # set window to be focused so key binds will work again
                self.window.focus_force()
            else:
                self.questions = questions
                self.window.title(f"QuestionCreator - {file}")
                self.cqi = 0
                self.changes = False
                self._reload()
    
    def _save_file(self, file=None):
        if not self.questions:
            showerror(title="Error", message=f"No questions found.")
            return
        save_successful = self._save_changes()
        if not save_successful:
            return
        if file is None:
            file = asksaveasfilename(defaultextension="txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if not file:
            return
        self.file = file
        try:
            inout.write_gift(file, self.questions)
        except ValueError as e:
            showerror(title="Error", message=f"Error when writing file:\n\n{e}")
        else:
            self.window.title(f"QuestionCreator - {file}")
            self.changes = False
    
    def _prev_question(self):
        self._move_to_question(-1)
    
    def _next_question(self):
        self._move_to_question(1)
    
    def _move_to_question(self, step):
        if not self.questions:
            showerror(title="Error", message=f"No questions found.")
            return
        save_successful = self._save_changes()
        if not save_successful:
            return
        self.cqi = (self.cqi + step) % len(self.questions)
        self._reload()
    
    def _on_close(self):
        save_successful = self._save_changes()
        if not save_successful:
            return
        if self.changes:
            yes = askyesno(title="Unsaved changes", message="There are unsaved changes in the current file. Do you "
                                                            "want to quit anyway (changes are lost)?")
            if not yes:
                return
        self.window.destroy()
    
    def start(self):
        self.window.mainloop()
