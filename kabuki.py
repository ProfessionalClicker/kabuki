from datetime import datetime
import json
import sys
from pathlib import Path
from consolemenu import *
from consolemenu.items import *

class Quiz:
    def __init__(self, id, name, description, image, questions):
        self.id = id
        self.name = name
        self.description = description
        self.image = image
        self.questions = questions
    def __str__(self):
        return f"{self.name} - {self.description}"

class Question:
    def __init__(self, prompt, image, type, choices, answer, time_limit, points, choice=None):
        self.prompt = prompt
        self.image = image
        self.type = type
        self.image = image
        self.choices = choices
        self.answer = answer
        self.time_limit = time_limit
        self.points = points
        self.choice = choice
    def get_question(self):
        #return the entire question, and if choice is not None, print out the user's choice
        if self.choice is not None:
            if self.type != "custom_answer":
                choices = "\n".join(self.choices)
                return f"Type: {self.type}\nPrompt: {self.prompt}\n{choices}\nYou answered: {self.choice}\nCorrect answer(s): {self.answer}\n\n"
            else:
                return f"Type: {self.type}\nPrompt: {self.prompt}\nYou answered: {self.choice}\nCorrect answer(s): {self.answer}\n\n"
            
        return f"Type: {self.type}\nPrompt: {self.prompt}\n"

def select_two(input_list, index):
    input_list.append(index)
    return input_list

def get_quiz_list(path):
    # get list of files from quizzes directory
    all_files = []
    for item in Path(path).iterdir():
        if Path(item).is_file():
            all_files.append(item)
    # create a list of Quiz objects from list of files
    quiz_list = []
    for file in all_files:
        with open(file, "r") as quiz_file:
            data = json.load(quiz_file)
            quiz = Quiz(data["quiz_id"], data["name"], data["description"], data["image"], data["questions"])
            quiz_list.append(quiz)
    return quiz_list

def create_record(quiz):
    # returns the file path of newly created text record
    user_name = input("Enter your name: ")

    user_name = "".join(user_name.split())
    user_name = "".join(e for e in user_name if e.isalnum())

    quiz_name = quiz.name
    quiz_name = "".join(quiz_name.split())
    quiz_name = "".join(e for e in quiz_name if e.isalnum())

    now = datetime.now()
    timestamp = f"{now.year}-{now.month:02d}-{now.day:02d}_{now.hour:02d}-{now.minute:02d}-{now.second:02d}"

    record_name = f"{user_name}_{quiz_name}_{timestamp}.txt"

    record_path = f"./results/{record_name}"
    with open(record_path, "a") as record:
        record.write(f"user: {user_name}\n")
        record.write(f"quiz: {quiz_name}\n")
        record.write(f"start_time: {timestamp}\n\n")
    return record_path

def main_menu(options):
    menu = SelectionMenu(options,"Select a quiz")
    menu.show()
    menu.join()
    return menu.selected_option

def question_menu(question, title):
    if question.type == "multiple_choice":
        qmenu = SelectionMenu(question.choices, title, question.prompt, show_exit_option=False)
        qmenu.show()
        qmenu.join()
        choice = qmenu.selected_option
        question.choice = question.choices[choice]
        if question.choice == question.answer:
            return True
    if question.type == "select_two":
        while True:
            selections = []
            qmenu = MultiSelectMenu(title, question.prompt, show_exit_option=False)
            for index, choice in enumerate(question.choices):
                fitem = FunctionItem(choice, select_two, [selections, index], kwargs=None, menu=qmenu, should_exit=True)
                qmenu.append_item(fitem)
            qmenu.show()
            qmenu.join()
            # break out of loop when 2 choices are selected
            if len(selections) == 2:
                break
        question.choice = [question.choices[selections[0]], question.choices[selections[1]]]
        counter = 0
        for i, choice in enumerate(question.choice):
            if choice == question.answer[i]:
                counter += 1
        if counter == 2:
            return True
    if question.type == "custom_answer":
        qmenu = ConsoleMenu(title, question.prompt, show_exit_option=False)
        fitem = FunctionItem("Select to input your answer", input, [f"{title}\n{question.prompt}\nInput your answer: "], should_exit=True)
        qmenu.append_item(fitem)
        qmenu.show()
        qmenu.join()
        question.choice = fitem.get_return()
        question.choice = question.choice.strip().lower()
        for answer in question.answer:
            answer = answer.strip().lower()
            if question.choice == answer:
                return True
    return False

def feedback_menu(correct, title):
    if correct:
        feedback = "Correct"
    else:
        feedback = "Incorrrect"
    rlist = ["Continue"]
    rmenu = SelectionMenu(rlist, title, feedback, show_exit_option=False)
    rmenu.show()
    rmenu.join()
    index = rmenu.selected_option

def main():
    # load quiz list
    quizzes_path = "./quizzes/"
    quiz_list = get_quiz_list(quizzes_path)
    # main menu
    selection = main_menu(quiz_list) 
    if selection == len(quiz_list):
        sys.exit("### Exiting Kabuki ###")

    # Quiz object
    quiz = quiz_list[selection]

    # create a record of the quiz so we can add feedback later
    record_path = create_record(quiz)

    # build question objects
    question_list = []
    for q in quiz.questions:
        question = Question(q["prompt"], q["image"], q["type"], q["choices"], q["answer"], q["time_limit"], q["points"])
        question_list.append(question)
    
    # start the quiz
    points = 0
    number_correct = 0

    for index, question in enumerate(question_list):
        title = f"#{index+1} - {question.type}"
        correct = question_menu(question, title)
        feedback_menu(correct, title)
        
        if correct:
            number_correct += 1
            points += question.points

        # add to the record after each question
        with open(record_path, "a") as file:
            file.write(question.get_question())

        
    
    percentage = float(number_correct / len(question_list)) * 100
    score_str = f"Quiz complete!\nScore: {percentage}\nNumber Correct: {number_correct}/{len(question_list)}\nPoints: {points}"
    print(score_str)
    with open(record_path, "a") as file:
            file.write(score_str)
    
    # add a final menu to allow the user to view the record file in terminal or open the file, return to main menu, or exit

    # the record should be formatted better with indents, bullets/numbers/letters for choices, if the user was correct, and for how many points scored

if __name__ == "__main__":
    main()