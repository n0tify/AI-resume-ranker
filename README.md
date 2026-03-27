# 🧠 Synapse: AI-Powered NLP Resume Ranker

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![spaCy](https://img.shields.io/badge/spaCy-09A3D5?style=for-the-badge&logo=spacy&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![Render](https://img.shields.io/badge/Deployed_on-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)

> **An enterprise-grade Application Tracking System (ATS) pipeline that mathematically ranks candidate dossiers against target job descriptions using advanced Natural Language Processing and TF-IDF vectorization.**

### 🌐 **Live Demo: [ai-resume-ranker-n0m2.onrender.com](https://ai-resume-ranker-n0m2.onrender.com)**

---

## 📑 Table of Contents
1. [About the Project](#-about-the-project)
2. [Core Features](#-core-features)
3. [System Architecture](#-system-architecture)
4. [Tech Stack](#-tech-stack)
5. [Local Installation](#-local-installation)
6. [Security & Privacy](#-security--privacy)
7. [Author](#-author)

---

## 🚀 About the Project
**Synapse** was engineered to eliminate the manual bottleneck of recruitment screening. Traditional keyword scanners fail to understand semantic context. By leveraging the **spaCy `en_core_web_sm` language model** and **Scikit-Learn's Machine Learning libraries**, this tool actively reads, sanitizes, and evaluates hundreds of resumes in seconds. 

It calculates the precise angular overlap (Cosine Similarity) between a candidate's experience and the required job profile, returning an actionable, color-coded dashboard of the best candidates.

---

## ✨ Core Features
* **🎯 Mathematical Ranking:** Converts text into multi-dimensional bi-gram arrays to calculate true semantic match percentages.
* **🔍 ATS Gap Analysis:** Automatically cross-references Nouns and Proper Nouns to generate a hit-list of critical "Missing Keywords" for low-scoring candidates.
* **⚡ Batch Processing:** Capable of reading and scoring multiple PDF dossiers simultaneously via an asynchronous drag-and-drop interface.
* **📊 Volatile Telemetry Reports:** Generates comprehensive CSV scoring reports instantly.
* **📨 SMTP Feedback Loop:** Integrated, secure 5-star rating system that routes UI/UX feedback directly to the engineering team via encrypted email.
* **🎨 Aurora Glassmorphism UI:** A highly engaging, interactive frontend built without external CSS frameworks, featuring dynamic background animations and reactive components.

---

## ⚙️ System Architecture
1. **Extraction Pipeline:** `PyPDF2` parses the raw bytes of uploaded PDF resumes, utilizing internal bypasses for minor encryptions.
2. **Linguistic Preprocessing:** `spaCy` executes tokenization, stop-word elimination, and deep lemmatization to reduce words to their base roots (e.g., treating "developer" and "development" equally).
3. **Vectorization:** `TfidfVectorizer` generates a Term Frequency-Inverse Document Frequency matrix utilizing an `ngram_range=(1,2)` to capture complex two-word technical phrases.
4. **Scoring Protocol:** The engine calculates the `cosine_similarity` between the Job Description vector and the Candidate Corpus vectors, applying a custom grading curve to output a 0-100% Probability Score.

---

## 🛠 Tech Stack
* **Backend Engine:** Python 3.10, Flask, Werkzeug
* **Data Science & ML:** spaCy, Scikit-Learn, Pandas, NumPy
* **Data Extraction:** PyPDF2
* **Frontend:** HTML5, Modern CSS3 (Glassmorphism), Vanilla JavaScript
* **Cloud Deployment:** Render, Gunicorn WSGI

---

## 💻 Local Installation
To run this intelligence protocol on your local machine, follow these secure steps:

**1. Clone the repository**

git clone [https://github.com/n0tify/AI-ML_Projects.git](https://github.com/n0tify/AI-ML_Projects.git)
cd AI-ML_Projects/resume_ranker_project

2. Create a virtual environment

python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

3. Install dependencies

pip install -r requirements.txt
python -m spacy download en_core_web_sm

4. Configure Security Vault (.env)
Create a .env file in the root directory and add your credentials:

Code snippet:
FLASK_SECRET_KEY=your_secure_random_key
ADMIN_EMAIL=your_email@gmail.com
EMAIL_APP_PASSWORD=your_16_digit_app_password

5. Initialize the Server

Bash
python app.py
The dashboard will be live at http://127.0.0.1:5000

🔒 Security & Privacy (Zero-Trace Architecture)
This application handles highly sensitive candidate data. To ensure strict compliance with modern data privacy standards:

No Database Persistence: Synapse does not use SQL or NoSQL databases.

Volatile RAM Generation: Scoring reports (CSVs) are generated strictly in the server's isolated io.StringIO memory.

Auto-Shredding: The moment a report is downloaded to the client's browser, the server executes a .pop() command to instantly and permanently destroy the memory sector. Uploaded PDFs are wiped from the server the second text extraction is complete.
