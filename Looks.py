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
from kivy.properties import BooleanProperty
import os
import json

# Register custom font
LabelBase.register(name="Caveat", fn_regular="Caveat-VariableFont_wght.ttf")

SAVE_DIR = "journal_entries"
os.makedirs(SAVE_DIR, exist_ok=True)
LAST_ENTRY_FILE = os.path.join(SAVE_DIR, "last_entry.json")

def load_entry(entry_name):
    file_path = os.path.join(SAVE_DIR, f"{entry_name}.txt")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    return ""

def save_entry(entry_name, text):
    file_path = os.path.join(SAVE_DIR, f"{entry_name}.txt")
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(text)

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
        self.entry_text = load_entry(self.name)
        
        self.layout = RelativeLayout()
        
        with self.layout.canvas.before:
            Color(1, 1, 0.9, 1)
            self.bg_rect = Rectangle(size=self.layout.size, pos=self.layout.pos)
        
        self.layout.bind(size=self.update_rect, pos=self.update_rect)
        
        self.text_input = TextInput(
            text=self.entry_text, 
            font_size=24, 
            font_name="Caveat", 
            size_hint=(0.9, 0.8), 
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            background_color=(1, 1, 1, 0),
            foreground_color=(0, 0, 0, 1),
            cursor_color=(0, 0, 0, 1),
            padding=(20, 20),
            hint_text="Write your thoughts here..."
        )
        self.layout.add_widget(self.text_input)
        
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
        
        self.add_widget(self.layout)

    def save_entry(self, instance):
        save_entry(self.name, self.text_input.text)
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

class TestScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(Label(text="This is the Test Tab", font_size=24, font_name="Caveat", pos_hint={'center_x': 0.5, 'center_y': 0.5}))

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
        self.add_widget(ExpandableTab("Test", "test", screen_manager))
        
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

# class for the hover indicator
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
        last_entry = load_last_entry()
        
        # Add initial screens
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

        # Inside the JournalApp.build method, after creating the FloatLayout
        hover_indicator = HoverIndicator()
        root.add_widget(hover_indicator)
        
        # Bind mouse motion to detect hover
        Window.bind(mouse_pos=lambda w, pos: self.detect_hover(pos, sidebar))
        
        sm.current = last_entry
        return root
    
    def detect_hover(self, mouse_pos, sidebar):
        # Check if the mouse is near the left edge of the window
        if mouse_pos[0] <= 10:  # Adjust this value for sensitivity
            sidebar.dispatch('on_enter')
        else:
            sidebar.dispatch('on_leave')

    # Add this method to the JournalApp class
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
