import google.generativeai as genai
import csv
import os
import matplotlib.pyplot as plt
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.properties import StringProperty

# Configure Google Gemini API
genai.configure(api_key="AIzaSyBHubxpy9MKFDC_uj6fuAh0TqxvJDIGkyc")
model = genai.GenerativeModel("gemini-1.5-flash")

# File path
csv_file = r"C:\Users\User\OneDrive\Documents\AI Journal\journal.csv"

class JournalApp(App):
    journal_text = StringProperty("")

    def build(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        self.text_input = TextInput(hint_text="Enter your journal entry", size_hint=(1, 0.5))
        self.submit_button = Button(text="Analyze", size_hint=(1, 0.1), on_press=self.analyze_emotions)
        self.result_label = Label(text="", size_hint=(1, 0.2))
        
        layout.add_widget(self.text_input)
        layout.add_widget(self.submit_button)
        layout.add_widget(self.result_label)
        
        return layout
    
    def emotion_score(self, emotion, entry):
        response = model.generate_content(f"Here's a journal entry. Tell me on a scale of 1-10 how {emotion} it is. ONLY give me the number: {entry}")
        try:
            return int(response.text.strip())
        except ValueError:
            return 1

    def analyze_emotions(self, instance):
        journal_entry = self.text_input.text
        
        if not journal_entry.strip():
            self.result_label.text = "Please enter a journal entry."
            return

        happy = self.emotion_score("happy", journal_entry)
        romantic = self.emotion_score("romantic", journal_entry)
        anxious = self.emotion_score("anxious", journal_entry)
        frustrated = self.emotion_score("frustrated", journal_entry)

        advice = model.generate_content(f"Here's a journal entry. Give the writer some advice :" + journal_entry)

        # Update UI
        self.result_label.text = f"Happiness: {happy}\nRomantic: {romantic}\nAnxiety: {anxious}\nFrustration: {frustrated}\n{advice}"
        
        # Write to CSV
        file_exists = os.path.exists(csv_file)
        with open(csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["Journal Entry", "Happiness", "Romantic", "Anxiety", "Frustration"])
            writer.writerow([journal_entry, happy, romantic, anxious, frustrated])

        # Display bar chart
        self.show_bar_chart(happy, romantic, anxious, frustrated)
        self.show_emotion_trend()
    
    def show_bar_chart(self, happy, romantic, anxious, frustrated):
        categories = ["Happiness", "Romantic", "Anxiety", "Frustration"]
        values = [happy, romantic, anxious, frustrated]
        plt.figure(figsize=(8, 5))
        plt.bar(categories, values, color=['yellow', 'pink', 'orange', 'red'])
        plt.xlabel("Emotion Type")
        plt.ylabel("Score")
        plt.title("Emotion Analysis for the Latest Journal Entry")
        plt.ylim(0, 10)
        plt.show()
    
    def show_emotion_trend(self):
        dates = []
        happiness_values = []
        romantic_values = []
        anxious_values = []
        frustrated_values = []
        
        with open(csv_file, mode='r') as file:
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

        plt.figure(figsize=(10, 6))
        plt.plot(dates, happiness_values, label="Happiness", color="yellow", marker='o')
        plt.plot(dates, romantic_values, label="Romantic", color="pink", marker='o')
        plt.plot(dates, anxious_values, label="Anxiety", color="orange", marker='o')
        plt.plot(dates, frustrated_values, label="Frustration", color="red", marker='o')
        plt.xlabel("Time (Journal Entry)")
        plt.ylabel("Emotion Level")
        plt.title("Emotion Analysis Over Time")
        plt.legend()
        plt.ylim(0, 10)
        plt.show()

if __name__ == "__main__":
    JournalApp().run()
