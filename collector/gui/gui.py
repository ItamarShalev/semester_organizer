from enum import Enum, auto
from typing import List, Dict, Optional, Callable

import sys

try:
    import tkinter
except ImportError:
    print("You need to install tkinter to run this program.")
    sys.exit(-1)
import customtkinter


import utils
from data.language import Language
from data.activity import Activity
from data.course_choice import CourseChoice
from data.user import User
from data.settings import Settings


class MessageType(Enum):
    ERROR = auto()
    WARNING = auto()
    INFO = auto()


class UserClickExitException(Exception):
    def __init__(self):
        super().__init__("ERROR: Can't click exit button without choose from the options.")


class Gui:

    def __init__(self, language: Language = Language.ENGLISH):
        self.language = language
        self.logger = utils.get_logging()
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("blue")

    def set_language(self, language: Language):
        self.language = language

    def open_login_window(self, is_valid_user_function: Callable) -> User:
        """
        This function will open the login window.
        :param: is_valid_user_function: a function that will get a user and return if the user is valid.
        :return: the user that was logged in.
        :raises: UserClickExitException if the user clicked exit button.
        """
        user_result = User()
        app = customtkinter.CTk()
        app.geometry("500x300")
        app.title("Login window")
        user_clicked_exit = False

        def button_clicked():
            nonlocal user_result
            self.logger.info("Login button clicked - checking if user is valid...")
            user = User(username_input.get(), password_input.get())
            if not user:
                message = "Username or password is missing, please fill all the fields."
                message_view.configure(text=message)
                self.logger.warning(message)
            elif not is_valid_user_function(user):
                message = "Username or password is invalid, please check your input."
                message_view.configure(text=message)
                self.logger.warning(message)
            else:
                user_result = user
                app.destroy()

        def exit_button_clicked():
            nonlocal user_clicked_exit
            user_clicked_exit = True
            self.logger.debug("Exit button clicked.")
            app.destroy()

        container = customtkinter.CTkFrame(master=app)
        container.pack(pady=20, padx=20, fill="both", expand=True)

        title_view = customtkinter.CTkLabel(master=container, justify=tkinter.LEFT, text="Login", text_color="white")
        title_view.pack(pady=12, padx=10)

        username_input = customtkinter.CTkEntry(master=container, placeholder_text="Username")
        username_input.pack(pady=12, padx=10)

        password_input = customtkinter.CTkEntry(master=container, placeholder_text="Password", show="*")
        password_input.pack(pady=12, padx=10)

        login_button = customtkinter.CTkButton(master=container, command=button_clicked, text="Login")
        login_button.pack(pady=12, padx=10)

        message_view = customtkinter.CTkLabel(master=container, justify=tkinter.LEFT, text="", text_color="orange")
        message_view.pack(pady=12, padx=10)

        app.protocol("WM_DELETE_WINDOW", exit_button_clicked)
        app.mainloop()

        if user_clicked_exit:
            raise UserClickExitException()

        return user_result

    def open_academic_activities_window(self, ask_attendance_required: bool,
                                        course_choices: Dict[str, CourseChoice]) -> Dict[str, CourseChoice]:
        """
        This function will open the academic activities window.
        :param: ask_attendance_required: if the user should choose if the activity is attendance required.
        :param: course_choices: the courses that the user can choose from.
        :return: the courses that the user chose.
        :raises: UserClickExitException if the user clicked exit button.
        """

    def open_personal_activities_window(self) -> List[Activity]:
        """
        This function will open a window to ask the user for his custom activities.
        for example, job, army, etc.
        :return: list of custom activities, or empty list.
        """

    def open_notification_window(self, message: str, message_type: MessageType = MessageType.INFO,
                                 buttons: List[str] = None) -> Optional[str]:
        """
        This function will open a notification window.
        :param: message: the message that will be shown in the window.
        :param: message_type: the type of the message. it will be shown in the window.
        :param: buttons: the buttons that will be shown in the window.
        :return: Which button was clicked. None if no button was clicked or the exit button was clicked.
        """
        assert message, "Message can't be empty."
        assert not buttons or len(buttons) <= 3, "Can't have more than 3 buttons."

        default_button = "OK"
        button_text_selected = None
        text_color = "white"

        app = customtkinter.CTk()
        app.title(f"{message_type.name.capitalize()} notification")
        app.geometry("550x240")

        def button_clicked(text_button):
            nonlocal button_text_selected
            button_text_selected = text_button
            app.destroy()

        def exit_button_clicked():
            self.logger.debug("Exit button clicked.")
            app.destroy()

        if message_type is MessageType.ERROR:
            text_color = "red"
        elif message_type is MessageType.WARNING:
            text_color = "orange"
        elif message_type is MessageType.INFO:
            text_color = "white"

        container = customtkinter.CTkFrame(master=app)
        container.pack(pady=20, padx=20, fill="both", expand=True)

        text_view = customtkinter.CTkLabel(master=container, justify=tkinter.CENTER, text=message,
                                           text_color=text_color)
        text_view.pack(pady=12, padx=10)
        buttons_frame = customtkinter.CTkFrame(master=container)
        buttons_frame.pack(pady=30, padx=10)

        if not buttons:
            button = customtkinter.CTkButton(master=buttons_frame, command=exit_button_clicked, text=default_button)
            button.pack(padx=5, pady=5)
        else:
            for button_text in buttons:

                button = customtkinter.CTkButton(master=buttons_frame, text=button_text,
                                                 command=lambda value=button_text: button_clicked(value))
                button.pack(side=tkinter.LEFT, pady=5, padx=5)

        app.mainloop()

        return button_text_selected

    def open_settings_window(self, settings: Settings, campuses: List[str], years: Dict[int, str]) -> Settings:
        """
        This function will open the settings window.
        it will show all the campus names that the user can choose from.
        years will be dict that will contain the years in format [hebrew_year: value_of_year]
        for example: { 5783: "תשפ"ג"}
        :param: settings: the settings that will be shown in the window. the function will return the new settings.
        :param: campuses: all the campus names that the user can choose from.
        :param: years: all the years that the user can choose from.
        :return: new object of Settings, if the user click exit button, it will return the old settings.
        """
