from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle
from kivy.core.text import LabelBase
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.properties import StringProperty
import os
import csv
import matplotlib.pyplot as plt
from kivy.uix.image import Image
from matplotlib.figure import Figure
import os
import json
import csv
import google.generativeai as genai
from kivy.uix.scrollview import ScrollView

# Register custom font
LabelBase.register(name="Caveat", fn_regular="Caveat-VariableFont_wght.ttf")

# Configure Google Gemini API
genai.configure(api_key="AIzaSyBHubxpy9MKFDC_uj6fuAh0TqxvJDIGkyc")
model = genai.GenerativeModel("gemini-1.5-flash")

# File paths
SAVE_DIR = "journal_entries"
os.makedirs(SAVE_DIR, exist_ok=True)
LAST_ENTRY_FILE = os.path.join(SAVE_DIR, "last_entry.json")
CSV_FILE = os.path.join(SAVE_DIR, "emotion_analysis.csv")


def load_entry(entry_name):
    file_path = os.path.join(SAVE_DIR, f"{entry_name}.txt")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read().split("\n---\n")  # Split entry and response
            if len(content) == 2:
                return content[0], content[1]  # Return entry and response
            else:
                return content[0], ""  # Return entry and empty response
    return "", ""  # Return empty strings if the file doesn't exist


def save_entry(entry_name, text, response=""):
    file_path = os.path.join(SAVE_DIR, f"{entry_name}.txt")
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(f"{text}\n---\n{response}")  # Separate entry and response with a delimiter


def save_last_entry(entry_name):
    with open(LAST_ENTRY_FILE, "w", encoding="utf-8") as file:
        json.dump({"last_entry": entry_name}, file)


def load_last_entry():
    if os.path.exists(LAST_ENTRY_FILE):
        with open(LAST_ENTRY_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data.get("last_entry", "entry0")
    return "entry0"


class ExpandableTab(ButtonBehavior, RelativeLayout):
    def __init__(self, text, target_screen, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.target_screen = target_screen
        self.screen_manager = screen_manager
        self.size_hint = (None, None)
        self.size = (150, 50)
        self.text_label = Label(
            text=text,
            font_size=18,
            font_name="Caveat",
            color=(0, 0, 0, 1),
            size_hint=(None, None),
            size=(150, 50),
            pos=(0, 0)
        )
        self.add_widget(self.text_label)
        self.bind(on_press=self.switch_screen)

    def switch_screen(self, instance):
        self.screen_manager.current = self.target_screen


class JournalEntry(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        entry_text, response_text = load_entry(self.name)  # Unpack the tuple

        self.layout = RelativeLayout()

        with self.layout.canvas.before:
            Color(1, 1, 0.9, 1)
            self.bg_rect = Rectangle(size=self.layout.size, pos=self.layout.pos)

        self.layout.bind(size=self.update_rect, pos=self.update_rect)

        self.text_input = TextInput(
            text=entry_text,  # Use the entry text from the tuple
            font_size=24,
            font_name="Caveat",
            size_hint=(0.9, 0.6),  # Adjusted to make space for the response
            pos_hint={'center_x': 0.5, 'center_y': 0.7},
            background_color=(1, 1, 1, 0),
            foreground_color=(0, 0, 0, 1),
            cursor_color=(0, 0, 0, 1),
            padding=(20, 20),
            hint_text="Write your thoughts here..."
        )
        self.layout.add_widget(self.text_input)

        # Add a ScrollView for the Gemini response
        self.response_scroll = ScrollView(
            size_hint=(0.9, 0.3),  # Adjust size as needed
            pos_hint={'center_x': 0.5, 'y': 0.05},
            do_scroll_x=False,  # Disable horizontal scrolling
            do_scroll_y=True    # Enable vertical scrolling
        )

        # Add a Label for the Gemini response inside the ScrollView
        self.response_label = Label(
            text=response_text,  # Use the response text from the tuple
            font_size=18,
            font_name="Caveat",
            color=(0, 0, 0, 1),
            size_hint_y=None,  # Allow the label to grow vertically
            halign='left',
            valign='top',
            text_size=(Window.width * 0.85, None),  # Set text width to match ScrollView
            padding=(10, 10)
        )
        self.response_label.bind(texture_size=self.response_label.setter('size'))  # Auto-resize label height
        self.response_scroll.add_widget(self.response_label)
        self.layout.add_widget(self.response_scroll)

        self.prev_button = Button(
            text="<", font_size=32, background_color=(0, 0, 0, 0), color=(0, 0, 0, 0.2),
            size_hint=(None, None), size=(50, 50), pos_hint={'x': 0.02, 'center_y': 0.5},
            on_press=self.prev_page
        )
        self.layout.add_widget(self.prev_button)

        self.next_button = Button(
            text=">", font_size=32, background_color=(0, 0, 0, 0), color=(0, 0, 0, 0.2),
            size_hint=(None, None), size=(50, 50), pos_hint={'right': 0.98, 'center_y': 0.5},
            on_press=self.next_page
        )
        self.layout.add_widget(self.next_button)

        # Add Save button
        self.save_button = Button(
            text="Save", font_size=24, background_color=(0, 0, 0, 0), color=(0, 0, 0, 1),
            size_hint=(None, None), size=(100, 50), pos_hint={'right': 0.98, 'y': 0.02},
            on_press=self.save_entry
        )
        self.layout.add_widget(self.save_button)

        # Add Analyze button
        self.analyze_button = Button(
            text="Analyze", font_size=24, background_color=(0, 0, 0, 0), color=(0, 0, 0, 1),
            size_hint=(None, None), size=(100, 50), pos_hint={'right': 0.98, 'y': 0.1},
            on_press=self.analyze_emotions
        )
        self.layout.add_widget(self.analyze_button)

        self.add_widget(self.layout)

    def save_entry(self, instance):
        save_entry(self.name, self.text_input.text, self.response_label.text)  # Save entry and response
        save_last_entry(self.name)

    def update_rect(self, *args):
        self.bg_rect.size = self.layout.size
        self.bg_rect.pos = self.layout.pos

    def prev_page(self, instance):
        current_index = int(self.name[5:])
        if current_index > 0:
            self.manager.transition = SlideTransition(direction='right')
            self.manager.current = f'entry{current_index - 1}'

    def next_page(self, instance):
        current_index = int(self.name[5:])
        next_index = current_index + 1
        next_screen_name = f'entry{next_index}'
        if next_screen_name not in self.manager.screen_names:
            self.manager.add_widget(JournalEntry(name=next_screen_name))
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = next_screen_name

    def on_leave(self):
        save_entry(self.name, self.text_input.text)
        save_last_entry(self.name)

    def emotion_score(self, emotion, entry):
        response = model.generate_content(
            f"Here's a journal entry. Tell me on a scale of 1-10 how {emotion} it is. ONLY give me the number: {entry}")
        try:
            return int(response.text.strip())
        except ValueError:
            return 1

    def analyze_emotions(self, instance):
        journal_entry = self.text_input.text

        if not journal_entry.strip():
            self.response_label.text = "Please write something first!"
            return

        # Generate a response using Google Gemini
        try:
            response = model.generate_content(f"Here's a journal entry. Provide a thoughtful analysis and advice: {journal_entry}")
            self.response_label.text = response.text
        except Exception as e:
            self.response_label.text = f"Error generating response: {str(e)}"

        # Emotion analysis (optional, if you still want to log emotions)
        happy = self.emotion_score("happy", journal_entry)
        romantic = self.emotion_score("romantic", journal_entry)
        anxious = self.emotion_score("anxious", journal_entry)
        frustrated = self.emotion_score("frustrated", journal_entry)

        # Write to CSV
        file_exists = os.path.exists(CSV_FILE)
        with open(CSV_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["Journal Entry", "Happiness", "Romantic", "Anxiety", "Frustration"])
            writer.writerow([journal_entry, happy, romantic, anxious, frustrated])


class TestScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Today's Emotions Section
        today_label = Label(text="Today's Emotions", font_size=24, font_name="Caveat")
        self.layout.add_widget(today_label)

        # Bar Chart Image
        self.bar_image = Image(source="", size_hint=(1, 6))
        self.layout.add_widget(self.bar_image)

        # Over Time Section
        over_time_label = Label(text="Emotions Over Time", font_size=24, font_name="Caveat")
        self.layout.add_widget(over_time_label)

        # Line Graph Image
        self.line_image = Image(source="", size_hint=(1, 6))
        self.layout.add_widget(self.line_image)

        self.add_widget(self.layout)

    def on_enter(self, *args):
        # Update graphs when the screen is entered
        self.update_bar_chart()
        self.update_line_graph()

    def update_bar_chart(self):
        # Read the latest entry from the CSV file
        with open(CSV_FILE, mode='r') as file:
            reader = csv.reader(file)
            rows = list(reader)
            if len(rows) > 1:
                latest_entry = rows[-1]
                happy = float(latest_entry[1])
                romantic = float(latest_entry[2])
                anxious = float(latest_entry[3])
                frustrated = float(latest_entry[4])

                # Create bar chart
                plt.figure(figsize=(5, 3))
                categories = ["Happiness", "Romantic", "Anxiety", "Frustration"]
                values = [happy, romantic, anxious, frustrated]
                plt.bar(categories, values, color=['yellow', 'pink', 'orange', 'red'])
                plt.ylim(0, 10)
                plt.title("Today's Emotions")

                # Save as image
                plt.savefig("today_emotions.png")
                plt.close()

                # Update Image widget
                self.bar_image.source = "today_emotions.png"
                self.bar_image.reload()

    def update_line_graph(self):
        dates = []
        happiness_values = []
        romantic_values = []
        anxious_values = []
        frustrated_values = []

        with open(CSV_FILE, mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip headers

            for index, row in enumerate(reader, start=1):
                try:
                    happiness_values.append(float(row[1]))
                    romantic_values.append(float(row[2]))
                    anxious_values.append(float(row[3]))
                    frustrated_values.append(float(row[4]))
                    dates.append(index)
                except ValueError:
                    continue

        # Create line graph
        plt.figure(figsize=(5, 3))
        plt.plot(dates, happiness_values, label="Happiness", color="yellow", marker='o')
        plt.plot(dates, romantic_values, label="Romantic", color="pink", marker='o')
        plt.plot(dates, anxious_values, label="Anxiety", color="orange", marker='o')
        plt.plot(dates, frustrated_values, label="Frustration", color="red", marker='o')
        plt.xlabel("Time (Journal Entry)")
        plt.ylabel("Emotion Level")
        plt.title("Emotion Analysis Over Time")
        plt.legend()
        plt.ylim(0, 10)

        # Save as image
        plt.savefig("emotion_trend.png")
        plt.close()

        # Update Image widget
        self.line_image.source = "emotion_trend.png"
        self.line_image.reload()

class CoverPage(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Use a FloatLayout for flexible positioning
        layout = FloatLayout()

        # Set a warm background color
        with layout.canvas.before:
            Color(0.96, 0.94, 0.89, 1)  # Light beige
            self.bg_rect = Rectangle(size=layout.size, pos=layout.pos)

        layout.bind(size=self.update_bg_rect, pos=self.update_bg_rect)

        # Add a title
        title = Label(
            text="AI Journal",
            font_size=48,
            font_name="Caveat",
            color=(0.2, 0.2, 0.2, 1),  # Dark gray for contrast
            size_hint=(None, None),
            size=(400, 100),
            pos_hint={'center_x': 0.5, 'center_y': 0.7}
        )
        layout.add_widget(title)

        # Add a subtitle
        subtitle = Label(
            text="Your personal space for reflection",
            font_size=24,
            font_name="Caveat",
            color=(0.4, 0.4, 0.4, 1),  # Lighter gray
            size_hint=(None, None),
            size=(600, 50),
            pos_hint={'center_x': 0.5, 'center_y': 0.6}
        )
        layout.add_widget(subtitle)

        # Add a "Start" button
        start_button = Button(
            text="Start Journaling",
            font_size=24,
            font_name="Caveat",
            background_color=(0.8, 0.7, 0.6, 1),  # Warm button color
            color=(1, 1, 1, 1),  # White text
            size_hint=(None, None),
            size=(200, 50),
            pos_hint={'center_x': 0.5, 'center_y': 0.4},
            on_press=self.start_journaling
        )
        layout.add_widget(start_button)

        self.add_widget(layout)

    def update_bg_rect(self, *args):
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos

    def start_journaling(self, instance):
        # Transition to the main journal screen
        self.manager.current = 'entry0'


class HoverableSidebar(BoxLayout):
    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = screen_manager
        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.size = (150, 100)
        self.pos_hint = {'x': -0.3, 'center_y': 0.5}  # Initially hidden

        # Add a background rectangle
        with self.canvas.before:
            Color(0.9, 0.9, 0.9, 1)  # Light gray background
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_bg_rect, size=self.update_bg_rect)

        # Add menu items
        self.add_widget(ExpandableTab("Journal", "entry0", screen_manager))
        self.add_widget(ExpandableTab("Analytics", "test", screen_manager))

        # Manually define on_enter and on_leave events
        self.register_event_type('on_enter')
        self.register_event_type('on_leave')

    def update_bg_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def on_enter(self, *args):
        Animation(pos_hint={'x': 0, 'center_y': 0.5}, duration=0.2).start(self)

    def on_leave(self, *args):
        Animation(pos_hint={'x': -0.3, 'center_y': 0.5}, duration=0.2).start(self)


class HoverIndicator(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (10, Window.height)  # Thin vertical bar
        self.pos_hint = {'x': 0, 'y': 0}
        with self.canvas:
            Color(0.5, 0.5, 0.5, 0.3)  # Semi-transparent gray
            self.rect = Rectangle(pos=self.pos, size=self.size)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class JournalApp(App):
    def build(self):
        sm = ScreenManager()

        # Add the Cover Page as the first screen
        sm.add_widget(CoverPage(name='cover'))

        # Add the JournalEntry and TestScreen
        sm.add_widget(JournalEntry(name='entry0'))
        sm.add_widget(TestScreen(name='test'))

        # Dynamically add screens for existing entries
        for entry_name in os.listdir(SAVE_DIR):
            if entry_name.endswith(".txt") and entry_name.startswith("entry"):
                entry_number = entry_name.split(".")[0]  # Remove .txt
                if entry_number not in sm.screen_names:
                    sm.add_widget(JournalEntry(name=entry_number))

        # Add hoverable sidebar
        sidebar = HoverableSidebar(screen_manager=sm)

        # Create a FloatLayout to hold the ScreenManager and sidebar
        root = FloatLayout()
        root.add_widget(sm)
        root.add_widget(sidebar)

        # Add hover indicator
        hover_indicator = HoverIndicator()
        root.add_widget(hover_indicator)

        # Bind mouse motion to detect hover
        Window.bind(mouse_pos=lambda w, pos: self.detect_hover(pos, sidebar))

        # Set the initial screen to the Cover Page
        sm.current = 'cover'
        return root

    def detect_hover(self, mouse_pos, sidebar):
        # Check if the mouse is near the left edge of the window
        if mouse_pos[0] <= 10:  # Adjust this value for sensitivity
            sidebar.dispatch('on_enter')
        else:
            sidebar.dispatch('on_leave')

    def on_stop(self):
        # Access the ScreenManager from the root FloatLayout
        screen_manager = None
        for child in self.root.children:
            if isinstance(child, ScreenManager):
                screen_manager = child
                break

        if screen_manager:
            current_screen = screen_manager.current_screen
            if isinstance(current_screen, JournalEntry):
                current_screen.save_entry(None)  # Save the current entry


if __name__ == "__main__":
    JournalApp().run()
