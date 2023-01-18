import copy
import sys

from typing import List, Dict, Optional, Callable, Literal

try:
    import tkinter
    from tkinter import Listbox, Scrollbar, BooleanVar
    from tkinter.font import Font
except ImportError:
    print("You need to install tkinter to run this program, Try to install new python version.")
    sys.exit(-1)

import customtkinter
from customtkinter import CTkEntry, CTkLabel, CTk, CTkCheckBox, CTkButton, CTkFrame, CTkComboBox, CTkToplevel

import utils
from data.message_type import MessageType
from data.activity import Activity
from data.course_choice import CourseChoice
from data.user import User
from data.settings import Settings
from data.translation import translate
from data.day import Day
from data.language import Language
from data.meeting import Meeting
from data.output_format import OutputFormat
from data.semester import Semester
from data.type import Type
from data.degree import Degree


def _(text: str):
    if Language.get_current() is Language.HEBREW:
        return " ".join(translate(text).replace(":", "").split(" ")[::-1])
    return translate(text)


class UserClickExitException(Exception):
    def __init__(self):
        super().__init__(_("ERROR: Can't click exit button without choose from the options."))


class Gui:

    def __init__(self):
        self.logger = utils.get_logging()
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("blue")
        self._is_blocked = False

    def open_login_window(self, is_valid_user_function: Callable) -> User:
        """
        This function will open the login window.
        :param: is_valid_user_function: a function that will get a user and return if the user is valid.
        :return: the user that was logged in.
        :raises: UserClickExitException if the user clicked exit button.
        """
        user_result = User()
        app = CTk()
        app.geometry("500x300")
        app.title(_("Login window"))
        user_clicked_exit = False

        def button_clicked():
            nonlocal user_result
            self.logger.info("Login button clicked - checking if user is valid...")
            user = User(username_input.get(), password_input.get())
            if not user:
                message = "Username or password is missing, please fill all the fields."
                message_view.configure(text=_(message))
                self.logger.warning(message)
            elif not is_valid_user_function(user):
                message = "Username or password is invalid, please check your input."
                message_view.configure(text=_(message))
                self.logger.warning(message)
            else:
                user_result = user
                app.destroy()

        def exit_button_clicked():
            nonlocal user_clicked_exit
            user_clicked_exit = True
            self.logger.debug("Exit button clicked.")
            app.destroy()

        container = CTkFrame(master=app)
        container.pack(pady=20, padx=20, fill="both", expand=True)

        title_view = CTkLabel(master=container, justify=tkinter.LEFT, text=_("Login"), text_color="white")
        title_view.pack(pady=12, padx=10)

        username_input = CTkEntry(master=container, placeholder_text=_("Username"))
        username_input.pack(pady=12, padx=10)

        password_input = CTkEntry(master=container, placeholder_text=_("Password"), show="*")
        password_input.pack(pady=12, padx=10)

        login_button = CTkButton(master=container, command=button_clicked, text="Login")
        login_button.pack(pady=12, padx=10)

        message_view = CTkLabel(master=container, justify=tkinter.LEFT, text="", text_color="orange")
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
        academic_activities_window = CTk()
        is_hebrew = Language.get_current() is Language.HEBREW
        justify_direction = "right" if is_hebrew else "left"
        label_column, widget_column = (1, 0) if is_hebrew else (0, 1)
        sticky_direction, scrollbar_direction = ("e", "w") if is_hebrew else ("w", "e")
        padx, pady = (10, 12)

        chosen_courses = {}

        row_number = 0
        # ask attendance label
        add_activity_frame = CTkFrame(master=academic_activities_window)
        add_activity_frame.grid(row=row_number, column=0, sticky="nsew", pady=pady, padx=padx)

        # choose an activity label
        choose_activity_label = CTkLabel(master=add_activity_frame, justify=justify_direction)
        choose_activity_label.configure(text=_("Choose a course:"))
        choose_activity_label.grid(row=row_number, column=label_column, pady=pady, padx=padx, sticky=sticky_direction)
        # choose an activity combobox
        values = list(course_choices.keys())
        choose_activity_combobox = CTkComboBox(master=add_activity_frame, justify=justify_direction, values=values)
        choose_activity_combobox.grid(row=row_number, column=widget_column, pady=pady, padx=padx,
                                      sticky=sticky_direction)
        row_number += 1

        # choose an activity button

        def button_clicked():
            course_choice = course_choices[choose_activity_combobox.get()]
            return self._open_course_settings_window(course_choice, ask_attendance_required, chosen_courses, listbox)

        choose_activity_button = CTkButton(master=add_activity_frame, text=_("Course settings"), command=button_clicked)
        choose_activity_button.grid(row=row_number, columnspan=3, pady=pady, padx=padx)

        # listbox label
        listbox_label = CTkLabel(master=academic_activities_window, justify=justify_direction)
        listbox_label.configure(text=_("Chosen courses:"), width=300)
        listbox_label.grid(pady=12, padx=10, sticky="nswe")
        # listbox in the center of the frame
        font = Font(family="Helvetica", size=12, weight="bold")

        listbox = Listbox(master=listbox_label, justify=justify_direction, width=300, height=200, font=font)
        listbox.grid(pady=pady, padx=padx, sticky="nsew", rowspan=5)
        # listbox scrollbar
        listbox_scrollbar = Scrollbar(master=listbox, orient=tkinter.VERTICAL)
        listbox_scrollbar.grid(row=1, column=widget_column, sticky=scrollbar_direction)
        listbox_scrollbar.configure(command=listbox.yview)
        listbox.configure(yscrollcommand=listbox_scrollbar.set)
        # double click on listbox item

        def list_item_double_clicked(event):
            course = chosen_courses[listbox.get(listbox.curselection())]
            return self._show_chosen_course(course, listbox, chosen_courses)

        listbox.bind("<Double-Button-1>", list_item_double_clicked)
        # save courses button
        save_courses_button = CTkButton(master=academic_activities_window, text=_("Save chosen courses"),
                                        command=academic_activities_window.destroy)
        save_courses_button.grid(row=2, columnspan=2, pady=12, padx=10)

        academic_activities_window.mainloop()

        return chosen_courses

    def open_personal_activities_window(self) -> List[Activity]:
        """
        This function will open a window to ask the user for his custom activities.
        for example, job, army, etc.
        :return: list of custom activities, or empty list.
        """
        # Create a list to store the custom activities
        result_personal_activities = {}
        self._is_blocked = False
        is_hebrew = Language.get_current() is Language.HEBREW
        justify_direction: Literal["right", "left"] = "right" if is_hebrew else "left"
        label_column, widget_column = (1, 0) if is_hebrew else (0, 1)
        sticky_direction, scrollbar_direction = ("e", "w") if is_hebrew else ("w", "e")
        padx = 5
        pady = 5

        # Create the main window
        window = CTk()
        window.title(_("Personal Activities"))
        # Create labels and entry widgets to ask the user for their custom activities
        activity_label = CTkLabel(window, text=_("Activity name:"), justify=justify_direction)
        activity_entry = CTkEntry(window)
        # 6 Radio buttons to choose the days of the week
        for i in range(len(Day)):
            CTkCheckBox(window, text="").grid(row=i + 1, column=widget_column, sticky=sticky_direction, padx=padx,
                                              pady=pady)

        start_time_label = CTkLabel(window, text=_("Start time:"), justify=justify_direction)
        start_time_entry = CTkEntry(window, placeholder_text="10:00")
        end_time_label = CTkLabel(window, text=_("End time:"), justify=justify_direction)
        end_time_entry = CTkEntry(window, placeholder_text="17:30")

        list_font = Font(family="Helvetica", size=12, weight="bold")

        added_activities_list_box = Listbox(window, width=30, justify=justify_direction, font=list_font)
        scrollbar = Scrollbar(master=window, orient='vertical', command=added_activities_list_box.yview)
        added_activities_list_box.config(yscrollcommand=scrollbar.set)

        def submit():
            # Get the user's input from the entry widgets
            activity_name = activity_entry.get()

            if not activity_name:
                self.open_notification_window(_("Please enter an activity name"), MessageType.ERROR)
                return

            # Get the user's chosen days of the week
            days = []
            for day_index in range(1, len(Day) + 1):
                if window.grid_slaves(row=day_index, column=widget_column)[0].get():
                    days.append(Day(day_index))

            meetings = []
            if not days:
                self.open_notification_window(_("Please choose at least one day."), MessageType.ERROR)
                return

            for day in days:
                # Get the user's chosen start and end times
                start_time = start_time_entry.get()
                end_time = end_time_entry.get()
                # Create a Meeting object for the user's custom activity
                try:
                    meetings.append(Meeting(day, start_time, end_time))
                except Exception as exception:
                    error_message = "Invalid time format, please try again."
                    self.logger.error(str(exception))
                    self.open_notification_window(error_message, MessageType.ERROR)
                    return

            new_activity = Activity(activity_name, Type.PERSONAL, True)
            new_activity.add_slots(meetings)

            if activity_name in result_personal_activities:
                try:
                    result_personal_activities[activity_name].add_slots(meetings)
                except Exception as error:
                    message = "You have two activities with the same name and overlapping time slots, please try again."
                    self.logger.error(str(error))
                    self.open_notification_window(_(message), MessageType.ERROR)
                    return
            else:
                result_personal_activities[activity_name] = new_activity
                # Add the activity to the listbox
                added_activities_list_box.insert(tkinter.END, new_activity.name)
                added_activities_list_box.update()

        # Create a button to submit the custom activities
        add_activity_button = CTkButton(window, text=_("Add activity:"), command=submit)

        # Place the widgets in the window
        activity_label.grid(row=0, column=label_column, sticky=sticky_direction, padx=padx, pady=pady)
        activity_entry.grid(row=0, column=widget_column, sticky=sticky_direction, padx=padx, pady=pady)
        for i in range(len(Day)):
            CTkLabel(window, text=_(str(Day(i + 1)))).grid(row=i + 1, column=label_column, sticky=sticky_direction,
                                                           padx=padx, pady=pady)
        start_time_label.grid(row=9, column=label_column, sticky=sticky_direction, padx=padx, pady=pady)
        start_time_entry.grid(row=9, column=widget_column, sticky=sticky_direction, padx=padx, pady=pady)
        end_time_label.grid(row=10, column=label_column, sticky=sticky_direction, padx=padx, pady=pady)
        end_time_entry.grid(row=10, column=widget_column, sticky=sticky_direction, padx=padx, pady=pady)
        add_activity_button.grid(row=11, columnspan=2, padx=padx + 5, pady=pady + 5)
        added_activities_list_box.grid(row=12, columnspan=2, rowspan=20, sticky='nsew', padx=padx, pady=pady)
        scrollbar.grid(row=13, columnspan=2, rowspan=20, padx=padx, pady=pady, sticky=scrollbar_direction + "ns")
        # save activities button
        save_button = CTkButton(window, text=_("Save activity:"), command=window.destroy)
        save_button.grid(row=33, column=0, columnspan=2, padx=padx + 5, pady=pady + 5)

        # calling the function open activity when item is double clicked,only one at a time
        def item_double_clicked(event):
            self._open_activity(event, result_personal_activities, added_activities_list_box)

        added_activities_list_box.bind("<Double-Button-1>", item_double_clicked)

        # Start the event loop
        window.mainloop()
        return list(result_personal_activities.values())

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

        default_button = _("OK")
        button_text_selected = None
        text_color = "white"

        app = CTk()
        app.title(f"{_(str(message_type))} {_('notification')}")
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

        container = CTkFrame(master=app)
        container.pack(pady=20, padx=20, fill="both", expand=True)

        text_view = CTkLabel(master=container, justify=tkinter.CENTER, text=message, text_color=text_color)
        text_view.pack(pady=12, padx=10)
        buttons_frame = CTkFrame(master=container)
        buttons_frame.pack(pady=30, padx=10)

        if not buttons:
            button = CTkButton(master=buttons_frame, command=exit_button_clicked, text=default_button)
            button.pack(padx=5, pady=5)
        else:
            for button_text in buttons:
                button = CTkButton(master=buttons_frame, text=button_text,
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
        new_settings = copy.deepcopy(settings)

        settings_root = CTk()
        settings_root.title(_("Settings"))
        is_hebrew = Language.get_current() is Language.HEBREW
        label_column, widget_column = (1, 0) if is_hebrew else (0, 1)
        sticky_direction = "e" if is_hebrew else "w"
        first_frame_side, second_frame_side = ("right", "left") if is_hebrew else ("left", "right")

        # right frame
        settings_frame = CTkFrame(master=settings_root)
        settings_frame.pack(side=first_frame_side, fill="both", expand=True, padx=10, pady=10)
        # left frame
        settings_frame_2 = CTkFrame(master=settings_root)
        settings_frame_2.pack(side=second_frame_side, fill="both", expand=True, padx=10, pady=10)

        # Create a list of labels and checkboxes

        checkboxes = []
        checkboxes_vars = []
        format_checkboxes = []
        format_vars = []
        semester_dict = {_(str(semester)): semester for semester in [Semester.FALL, Semester.SPRING]}
        format_dict = list(OutputFormat)

        labels = [
            "Attendance requirement",
            "Available places",
            "Active classes",
            "Can register to class",
            "Show Herzog",
            "Actual number",
            "Dont show courses that were done",
            "Show only courses with complete prequistities"
        ]
        booleans_settings = [
            "attendance_required_all_courses",
            "show_only_courses_with_free_places",
            "show_only_courses_active_classes",
            "show_only_classes_can_enroll",
            "show_hertzog_and_yeshiva",
            "show_only_courses_with_the_same_actual_number",
            "dont_show_courses_already_done",
            "show_only_courses_with_prerequisite_done",
        ]

        booleans_settings = dict(zip(labels, booleans_settings))

        for index, (label, setting_attribute) in enumerate(zip(labels, booleans_settings.values())):
            bool_var = BooleanVar()
            bool_var.set(getattr(new_settings, setting_attribute))
            checkbox = CTkCheckBox(settings_frame, text="", variable=bool_var)
            checkboxes_vars.append(bool_var)
            checkboxes.append(checkbox)
            checkbox.grid(row=index, column=widget_column, sticky=sticky_direction, padx=7)
            label = CTkLabel(settings_frame, text=_(label))
            label.grid(row=index, column=label_column, sticky=sticky_direction)

        row_number = len(labels)
        # campus label
        campus_label = CTkLabel(settings_frame, text=_("Please choose a campus:"))
        campus_label.grid(row=row_number, column=label_column, sticky=sticky_direction)
        row_number += 1
        # Create a combobox
        campuses_combobox = CTkComboBox(master=settings_frame, values=campuses)
        campuses_combobox.grid(row=row_number, column=label_column, pady=10, padx=10, sticky=sticky_direction)
        row_number += 1

        # year label
        year_label = CTkLabel(settings_frame, text=_("Please choose a year:"))
        year_label.grid(row=row_number, column=label_column, sticky=sticky_direction)
        row_number += 1
        # Create a combobox
        years_combobox = CTkComboBox(master=settings_frame, values=list(years.values()))
        years_combobox.grid(row=row_number, column=label_column, pady=10, padx=10, sticky=sticky_direction)
        row_number += 1

        # semester label
        semester_label = CTkLabel(settings_frame, text=_("Please choose a semester:"))
        semester_label.grid(row=row_number, column=label_column, sticky=sticky_direction)
        row_number += 1
        # Create a combobox
        semester_combobox = CTkComboBox(master=settings_frame, values=list(semester_dict.keys()))
        semester_combobox.grid(row=row_number, column=label_column, pady=10, padx=10, sticky=sticky_direction)
        row_number += 1

        # language label
        language_label = CTkLabel(settings_frame, text=_("Please choose a language:"))
        language_label.grid(row=row_number, column=label_column, sticky=sticky_direction)
        row_number += 1
        # Create a combobox
        language_combobox = CTkComboBox(master=settings_frame, values=[_(str(language)) for language in Language])
        language_combobox.grid(row=row_number, column=label_column, pady=10, padx=10, sticky=sticky_direction)
        row_number += 1

        # format label
        format_label = CTkLabel(settings_frame, text=_("Please choose an output format:"))
        format_label.grid(row=row_number, column=label_column, sticky=sticky_direction)
        row_number += 1
        # Create a combobox
        for i in range(len(OutputFormat)):
            bool_var = BooleanVar()
            bool_var.set(True)
            checkbox = CTkCheckBox(settings_frame, text=_(format_dict[i].name), variable=bool_var)
            format_vars.append(bool_var)
            checkbox.grid(row=row_number, column=label_column, pady=10, padx=10, sticky=sticky_direction)
            format_checkboxes.append(checkbox)
            row_number += 1

        row_number_2 = 0
        # days labels
        days_label = CTkLabel(settings_frame_2, text=_("Please choose the days you want to see:"))
        days_label.grid(row=row_number_2, column=label_column, sticky=sticky_direction)
        row_number_2 += 1
        # Create checkboxes
        days = list(Day)
        days_vars = []
        days_checkboxes = []
        for i in range(len(Day)):
            bool_var = BooleanVar()
            bool_var.set(True)
            day_label = CTkLabel(settings_frame_2, text=_(days[i].name))
            day_label.grid(row=row_number_2, column=label_column, sticky=sticky_direction)
            checkbox = CTkCheckBox(settings_frame_2, text="", variable=bool_var)
            days_vars.append(bool_var)
            checkbox.grid(row=row_number_2, column=widget_column, pady=10, sticky=sticky_direction)
            days_checkboxes.append(checkbox)
            row_number_2 += 1

        degrees = list(Degree)

        # degree label
        degree_label = CTkLabel(settings_frame_2, text=_("The degrees to choose the courses from:"))
        degree_label.grid(row=row_number_2, column=label_column, sticky=sticky_direction)
        row_number_2 += 1
        # Create checkboxes
        degrees_vars = []
        degrees_checkboxes = []
        for degree in degrees:
            bool_var = BooleanVar()
            bool_var.set(True)
            degree_label = CTkLabel(settings_frame_2, text=_(str(degree)))
            degree_label.grid(row=row_number_2, column=label_column, sticky=sticky_direction)
            checkbox = CTkCheckBox(settings_frame_2, text="", variable=bool_var)
            degrees_vars.append(bool_var)
            checkbox.grid(row=row_number_2, column=widget_column, pady=10, sticky=sticky_direction)
            degrees_checkboxes.append(checkbox)
            row_number_2 += 1

        # current degree label
        current_degree_label = CTkLabel(settings_frame_2, text=_("Please choose a current degree:"))
        current_degree_label.grid(row=row_number_2, column=label_column, sticky=sticky_direction, padx=5, pady=5)

        # current degree combobox
        current_degree_combobox = CTkComboBox(master=settings_frame_2, values=[_(str(degree)) for degree in Degree])
        current_degree_combobox.grid(row=row_number_2, column=widget_column, pady=10, padx=10, sticky=sticky_direction)
        row_number_2 += 1

        def get_checked():
            # Get a list of boolean values corresponding to the checked checkboxes
            for j, attribute in enumerate(booleans_settings.values()):
                setattr(new_settings, attribute, checkboxes_vars[j].get())
            new_settings.campus_name = campuses_combobox.get()
            new_settings.semester = semester_dict[semester_combobox.get()]
            chosen_language = language_combobox.get().upper()
            new_settings.language = Language[chosen_language]
            checked_format = []
            for j, format_var in enumerate(format_vars):
                if format_var.get():
                    checked_format.append(format_dict[j])
            new_settings.output_formats = checked_format
            checked_days = []
            for j, day_var in enumerate(days_vars):
                if day_var.get():
                    checked_days.append(days[j])
            chosen_degrees = set()
            for j, degree in enumerate(degrees):
                if degrees_vars[j].get():
                    chosen_degrees.add(degree)
            new_settings.degrees = chosen_degrees
            new_settings.show_only_classes_in_days = checked_days
            new_settings.year = [key for key, value in years.items() if value == years_combobox.get()][0]
            new_settings.degree = Degree[current_degree_combobox.get().replace(" ", "_").upper()]
            settings_root.destroy()

        get_button = CTkButton(master=settings_frame_2, text="Update settings", command=get_checked)
        get_button.grid(row=row_number_2, columnspan=2, pady=10)

        settings_root.mainloop()
        return new_settings

    # function that open an activity window when the item is double-clicked, only one window can be open at a time
    def _open_activity(self, event, result_personal_activities, list_box):
        if self._is_blocked:
            return
        self._is_blocked = True
        is_hebrew = Language.get_current() is Language.HEBREW
        justify_direction: Literal["right", "left"] = "right" if is_hebrew else "left"
        current_selection = list_box.curselection()
        activity_name = list_box.get(current_selection)
        activity = result_personal_activities[activity_name]
        activity_window = CTkToplevel()
        activity_window.title(activity.name)
        # activity time slots display
        activity_time_slots = CTkLabel(activity_window, text=_("Activity time slots:"))
        activity_time_slots.grid(row=2, column=0, columnspan=2)
        # activity time slots list
        activity_time_slots_list = Listbox(activity_window, width=30, justify=justify_direction)
        activity_time_slots_scrollbar = Scrollbar(master=activity_window, orient='vertical',
                                                  command=activity_time_slots_list.yview)
        activity_time_slots_list.config(yscrollcommand=activity_time_slots_scrollbar.set)
        for meeting in activity.meetings:
            activity_time_slots_list.insert(tkinter.END, f"{meeting} {_(str(meeting.day))}")
        activity_time_slots_list.grid(row=3, columnspan=2, rowspan=20, sticky='nsew')
        activity_time_slots_scrollbar.grid(row=3, columnspan=2, rowspan=20, sticky='wns')

        # button to delete the activity
        def delete_activity(new_result_personal_activities=result_personal_activities):
            self._is_blocked = False
            list_box.delete(current_selection)
            del new_result_personal_activities[activity_name]
            activity_window.destroy()

        def exit_button_clicked():
            self._is_blocked = False
            activity_window.destroy()

        delete_button = CTkButton(activity_window, text=_("Delete activity:"), command=delete_activity)
        delete_button.grid(row=2, column=0, columnspan=2)

        activity_window.protocol("WM_DELETE_WINDOW", exit_button_clicked)

        activity_window.mainloop()

    def _open_course_settings_window(self, chosen_course: CourseChoice, attendance_required_all_courses: bool,
                                     chosen_courses, listbox):
        '''
        This function opens a window that allows the user to change the settings of the course
        :param chosen_course: the course that the user wants to change the settings of
        :param attendance_required_all_courses: a boolean value that indicates if the user wants to set the attendance
        :return:
        '''
        if self._is_blocked or chosen_course.name in chosen_courses:
            return

        self._is_blocked = True

        row_number = 0
        is_hebrew = Language.get_current() is Language.HEBREW
        justify_direction: Literal["right", "left"] = "right" if is_hebrew else "left"
        label_column, widget_column = (1, 0) if is_hebrew else (0, 1)
        sticky_direction: Literal["w", "e"] = "e" if is_hebrew else "w"
        padx = 5
        pady = 5

        lecturers = list(chosen_course.available_teachers_for_lecture)
        practices = list(chosen_course.available_teachers_for_practice)

        course_settings_window = CTkToplevel()
        course_settings_window.title(_("Course settings"))

        course_settings_frame = CTkFrame(course_settings_window)
        course_settings_frame.grid(row=0, columnspan=2, sticky='nsew')
        # course name
        course_name_label = CTkLabel(course_settings_frame, text=_("Course name:"), justify=justify_direction)
        course_name_label.grid(row=row_number, column=label_column, sticky=sticky_direction, padx=padx, pady=pady)
        course_name = CTkLabel(course_settings_frame, text=chosen_course.name, justify=justify_direction)
        course_name.grid(row=row_number, column=widget_column, sticky=sticky_direction, padx=padx, pady=pady)
        row_number += 1

        if not attendance_required_all_courses:
            # lecture attendance label
            lecture_attendance_label = CTkLabel(course_settings_frame, text=_("Lecture attendance:"),
                                                justify=justify_direction)
            lecture_attendance_label.grid(row=row_number, column=label_column, sticky=sticky_direction, padx=padx,
                                          pady=pady)
            # lecture attendance checkbox
            lecture_attendance_required = BooleanVar()
            lecture_attendance_required.set(chosen_course.attendance_required_for_lecture)
            lecture_attendance_checkbox = CTkCheckBox(course_settings_frame, variable=lecture_attendance_required,
                                                      text="")
            lecture_attendance_checkbox.grid(row=row_number, column=widget_column, sticky=sticky_direction,
                                             padx=padx + 5, pady=pady)
            row_number += 1

            # practice attendance label
            practice_attendance_label = CTkLabel(course_settings_frame, text=_("Practice attendance:"),
                                                 justify=justify_direction)
            practice_attendance_label.grid(row=row_number, column=label_column, sticky=sticky_direction, padx=padx,
                                           pady=pady)
            # practice attendance checkbox
            practice_attendance_required = BooleanVar()
            practice_attendance_required.set(chosen_course.attendance_required_for_practice)
            practice_attendance_checkbox = CTkCheckBox(course_settings_frame, variable=practice_attendance_required,
                                                       text="")
            practice_attendance_checkbox.grid(row=row_number, column=widget_column, sticky=sticky_direction,
                                              padx=padx + 5, pady=pady)
            row_number += 1

        # list of lecturers with checkboxes
        lecture_list_label = CTkLabel(course_settings_frame, text=_("Please choose your favorite lecturers:"),
                                      justify=justify_direction)
        lecture_list_label.grid(row=row_number, column=label_column, sticky=sticky_direction, padx=padx, pady=pady)
        row_number += 1
        lecture_teachers_vars = []
        for teacher in chosen_course.available_teachers_for_lecture:
            teacher_var = BooleanVar()
            lecture_teachers_vars.append(teacher_var)
            teacher_var.set(False)
            teacher_label = CTkLabel(course_settings_frame, text=teacher, justify=justify_direction)
            teacher_label.grid(row=row_number, column=label_column, sticky=sticky_direction, padx=padx, pady=pady)
            teacher_checkbox = CTkCheckBox(course_settings_frame, variable=teacher_var, text="")
            teacher_checkbox.grid(row=row_number, column=widget_column, sticky=sticky_direction, padx=padx + 5,
                                  pady=pady)
            row_number += 1

        # list of practice teachers with checkboxes
        text = _("Please choose your favorite practice teachers:")
        practice_list_label = CTkLabel(course_settings_frame, text=text, justify=justify_direction)
        practice_list_label.grid(row=row_number, column=label_column, columnspan=2, sticky=sticky_direction, padx=padx,
                                 pady=pady)

        row_number += 1
        practice_teachers_vars = []
        for teacher in chosen_course.available_teachers_for_practice:
            teacher_var = BooleanVar()
            practice_teachers_vars.append(teacher_var)
            teacher_var.set(False)
            teacher_label = CTkLabel(course_settings_frame, text=teacher, justify=justify_direction)
            teacher_label.grid(row=row_number, column=label_column, sticky=sticky_direction, padx=padx, pady=pady)
            teacher_checkbox = CTkCheckBox(course_settings_frame, variable=teacher_var, text="")
            teacher_checkbox.grid(row=row_number, column=widget_column, sticky=sticky_direction, padx=padx + 5,
                                  pady=pady)
            row_number += 1

        def add_course():
            course_choice = copy.deepcopy(chosen_course)
            if not attendance_required_all_courses:
                course_choice.attendance_required_for_lecture = lecture_attendance_required.get()
                course_choice.attendance_required_for_practice = practice_attendance_required.get()

            chosen_teachers_for_lecture = []
            for index, lecture_var in enumerate(lecture_teachers_vars):
                if lecture_var.get():
                    chosen_teachers_for_lecture.append(lecturers[index])
            chosen_teachers_for_practice = []
            for index, practice_teachers_var in enumerate(practice_teachers_vars):
                if practice_teachers_var.get():
                    chosen_teachers_for_practice.append(practices[index])
            course_choice.available_teachers_for_lecture = set(chosen_teachers_for_lecture)
            course_choice.available_teachers_for_practice = set(chosen_teachers_for_practice)
            self._is_blocked = False
            listbox.insert(tkinter.END, course_choice.name)
            chosen_courses[course_choice.name] = course_choice
            course_settings_window.destroy()

        # save button
        save_button = CTkButton(course_settings_window, text=_("Add course"), command=add_course)
        save_button.grid(row=3, column=0, columnspan=2, padx=padx, pady=pady)

        course_settings_window.mainloop()

        self._is_blocked = False

    def _show_chosen_course(self, course_to_show, listbox, chosen_courses):
        self._is_blocked = True
        course_settings_window = CTkToplevel()
        course_settings_window.title(_("Course display"))
        justify_direction = "right" if Language.get_current() is Language.HEBREW else "left"
        label_column, widget_column = (0, 1) if Language.get_current() == Language.ENGLISH else (1, 0)
        sticky_direction = "e" if Language.get_current() is Language.HEBREW else "w"
        padx = 5
        pady = 5

        # display attendance requirememnts
        course_settings_frame = CTkFrame(course_settings_window)
        course_settings_frame.grid(row=0, column=0, sticky='nsew')
        row_number = 0
        # course name label
        course_name_headline_label = CTkLabel(course_settings_frame, text=_("Course name:"), justify=justify_direction)
        course_name_headline_label.grid(row=row_number, column=label_column, sticky=sticky_direction, padx=padx,
                                        pady=pady)
        # course name checkbox
        course_name_label = CTkLabel(course_settings_frame, text=course_to_show.name, justify=justify_direction)
        course_name_label.grid(row=row_number, column=widget_column, sticky=sticky_direction, padx=padx, pady=pady)
        row_number += 1
        # lecture attendance label
        lecture_attendance_label = CTkLabel(course_settings_frame, text=_("Lecture attendance:"),
                                            justify=justify_direction)
        lecture_attendance_label.grid(row=row_number, column=label_column, sticky=sticky_direction, padx=padx,
                                      pady=pady)
        # lecture attendance checkbox
        lecture_var = BooleanVar()
        lecture_var.set(course_to_show.attendance_required_for_lecture)
        lecture_attendance_checkbox = CTkCheckBox(course_settings_frame, text="", variable=lecture_var,
                                                  state="disabled")
        lecture_attendance_checkbox.grid(row=row_number, column=widget_column, sticky=sticky_direction, padx=padx + 5,
                                         pady=pady)
        row_number += 1
        # practice attendance label
        practice_attendance_label = CTkLabel(course_settings_frame, text=_("Practice attendance:"),
                                             justify=justify_direction)
        practice_attendance_label.grid(row=row_number, column=label_column, sticky=sticky_direction, padx=padx,
                                       pady=pady)
        # practice attendance checkbox
        practice_var = BooleanVar()
        practice_var.set(course_to_show.attendance_required_for_practice)
        practice_attendance_checkbox = CTkCheckBox(course_settings_frame, text="", variable=practice_var,
                                                   state="disabled")
        practice_attendance_checkbox.grid(row=row_number, column=widget_column, sticky=sticky_direction, padx=padx + 5,
                                          pady=pady)
        row_number += 1
        # list of lecture teachers with checkboxes
        lecture_list_label = CTkLabel(course_settings_frame, text=_("Lecture teachers:"), justify=justify_direction)
        lecture_list_label.grid(row=row_number, column=label_column, sticky=sticky_direction,
                                padx=padx, pady=pady)
        row_number += 1
        for teacher in course_to_show.available_teachers_for_lecture:
            teacher_label = CTkLabel(course_settings_frame, text=teacher, justify=justify_direction)
            teacher_label.grid(row=row_number, column=label_column, sticky=sticky_direction, padx=padx, pady=pady)
            row_number += 1
        # list of practice teachers with checkboxes
        practice_list_label = CTkLabel(course_settings_frame, text=_("Practice teachers:"), justify=justify_direction)
        practice_list_label.grid(row=row_number, column=label_column, sticky=sticky_direction, padx=padx, pady=pady)
        row_number += 1
        for teacher in course_to_show.available_teachers_for_practice:
            teacher_label = CTkLabel(course_settings_frame, text=teacher, justify=justify_direction)
            teacher_label.grid(row=row_number, column=label_column, sticky=sticky_direction, padx=padx, pady=pady)
            row_number += 1

        def close_window():
            self._is_blocked = False
            course_settings_window.destroy()

        def remove_course():
            self._is_blocked = False
            listbox.delete(listbox.curselection())
            del chosen_courses[course_to_show.name]
            course_settings_window.destroy()

        # close button
        close_button = CTkButton(course_settings_window, text=_("Close"), command=close_window)
        close_button.grid(row=1, column=0, padx=padx, pady=pady)

        # delete button
        delete_button = CTkButton(course_settings_window, text=_("Delete"), command=remove_course)
        delete_button.grid(row=2, column=0, padx=padx, pady=pady)

        course_settings_window.mainloop()
