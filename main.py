import google.generativeai as genai

genai.configure(api_key="AIzaSyBHubxpy9MKFDC_uj6fuAh0TqxvJDIGkyc")
model = genai.GenerativeModel("gemini-1.5-flash")

print (model.generate_content("testing")
