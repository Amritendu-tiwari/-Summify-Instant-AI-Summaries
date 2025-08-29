# ✨ Summify: Instant AI Summaries  

Summify is a simple yet powerful **Streamlit web app** that generates quick, clear summaries of any **website** or **YouTube video**.  
It uses **Groq’s LLaMA 3 model (via LangChain)** for summarization, making learning and content consumption faster and easier.  

---

##📸 Demo
👉 [Add demo link or screenshot here]

---

## 🚀 Features  
- Summarize **web pages** instantly  
- Summarize **YouTube videos** (using transcript or fallback to video title + description)  
- Clean, simple **Streamlit UI**  
- Handles invalid URLs gracefully  
- Uses **Groq’s ultra-fast inference** for summaries  

---

## 🛠️ Tech Stack  
- **Streamlit** – Web app framework  
- **LangChain** – For LLM chaining and summarization  
- **Groq (LLaMA 3 model)** – Fast, efficient LLM inference  
- **UnstructuredURLLoader** – To fetch and parse website content  
- **YouTubeTranscriptApi** – To extract video transcripts  
- **pytubefix** – Fallback for fetching YouTube title + description  
- **Python** – Glue for everything  

---

## 📦 Installation  

1. Clone the repo:  
   ```bash
   git clone https://github.com/yourusername/summify.git
   cd summify
Create a virtual environment (optional but recommended):

bash
Copy code
python -m venv venv
source venv/bin/activate   # On macOS/Linux
venv\Scripts\activate      # On Windows
Install dependencies:

bash
Copy code
pip install -r requirements.txt
🔑 Groq API Key
You’ll need a Groq API key to use this project.

Get your API key from Groq Console.

When you run the app, enter your API key in the Streamlit sidebar input box.

▶️ Run the App
bash
Copy code
streamlit run app.py
Open your browser at http://localhost:8501/ and start summarizing! 🎉


UI enhancements with dark mode

🤝 Contributing
Feel free to fork this repo, open issues, or submit PRs. Feedback is always welcome!
