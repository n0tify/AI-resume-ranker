import os
import re
import logging
from typing import List, Dict
import PyPDF2
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

# Configure enterprise-grade logging for debugging and tracking
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s | %(levelname)s | %(message)s'
)

class ResumeAnalyzer:
    r"""
    Advanced NLP Engine for processing, cleaning, and ranking resumes against a target Job Description.
    Utilizes SpaCy for linguistic processing and Scikit-Learn for vector mathematics.
    
    The ranking algorithm relies on Cosine Similarity between TF-IDF vectors:
    $$\text{similarity} = \cos(\theta) = \frac{\mathbf{A} \cdot \mathbf{B}}{\|\mathbf{A}\| \|\mathbf{B}\|}$$
    """
    
    def __init__(self):
        logging.info("Initializing Enterprise ResumeAnalyzer Engine...")
        try:
            # Load small English web model for tokenization, POS tagging, and NER
            self.nlp = spacy.load("en_core_web_sm")
            logging.info("SpaCy model 'en_core_web_sm' loaded successfully.")
        except OSError:
            logging.error("SpaCy model missing. Execute: python -m spacy download en_core_web_sm")
            raise
        
        # UPGRADE: Added ngram_range=(1, 2) to capture two-word phrases (e.g., "Machine Learning")
        self.vectorizer = TfidfVectorizer(stop_words='english', lowercase=True, ngram_range=(1, 2))

    def extract_text(self, pdf_path: str) -> str:
        """Securely parses a PDF document and extracts raw text."""
        raw_text = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        raw_text += extracted + " "
        except Exception as e:
            logging.error(f"Failed to read {pdf_path}. Error: {str(e)}")
            return ""
        
        # Sanitize whitespace and line breaks
        return re.sub(r'\s+', ' ', raw_text).strip()

    def extract_candidate_name(self, text: str, filename: str) -> str:
        """Attempts to extract the candidate's real name using Named Entity Recognition (NER)."""
        doc = self.nlp(text[:1000]) # Only scan the top of the resume for efficiency
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = re.sub(r'[^a-zA-Z\s]', '', ent.text).strip()
                if len(name.split()) >= 2: # Ensure it looks like a First Last name
                    return name.title()
        
        # Fallback mechanism: use the filename without the .pdf extension
        clean_filename = os.path.splitext(filename)[0]
        return clean_filename.replace('_', ' ').title()

    def process_linguistics(self, text: str) -> str:
        """Applies a rigorous NLP pipeline including Lemmatization."""
        if not text:
            return ""
            
        doc = self.nlp(text.lower())
        processed_tokens = [
            token.lemma_ for token in doc 
            if not token.is_stop and not token.is_punct and not token.like_num and token.is_alpha
        ]
        return " ".join(processed_tokens)

    def extract_missing_keywords(self, jd_text: str, resume_text: str, top_n: int = 6) -> List[str]:
        """Identifies key nouns/proper nouns in the JD that are completely missing from the resume."""
        jd_doc = self.nlp(jd_text.lower())
        resume_doc = self.nlp(resume_text.lower())

        # Extract meaningful keywords from JD (Nouns and Proper Nouns)
        jd_keywords = set([token.lemma_ for token in jd_doc if token.pos_ in ["NOUN", "PROPN"] and not token.is_stop and token.is_alpha])
        resume_keywords = set([token.lemma_ for token in resume_doc if token.pos_ in ["NOUN", "PROPN"] and not token.is_stop and token.is_alpha])

        # Find the mathematical gap
        missing = jd_keywords - resume_keywords
        
        # Sort by length/importance to get the most substantial words and return top N
        sorted_missing = sorted(list(missing), key=len, reverse=True)
        return [word.title() for word in sorted_missing[:top_n]]

    def evaluate_candidates(self, job_desc: str, file_paths: List[str], file_names: List[str]) -> List[Dict]:
        """Calculates the mathematical overlap and returns a sorted list of candidate profiles."""
        logging.info(f"Initiating evaluation for {len(file_paths)} candidates.")
        
        clean_jd = self.process_linguistics(job_desc)
        document_corpus = [clean_jd]
        candidate_profiles = []
        raw_resumes = []
        
        for path, fname in zip(file_paths, file_names):
            raw_content = self.extract_text(path)
            if raw_content:
                clean_content = self.process_linguistics(raw_content)
                document_corpus.append(clean_content)
                raw_resumes.append(raw_content)
                
                inferred_name = self.extract_candidate_name(raw_content, fname)
                candidate_profiles.append({"name": inferred_name, "filename": fname})
            else:
                logging.warning(f"Discarding {fname}: No readable text found.")

        if len(document_corpus) <= 1:
            logging.warning("Insufficient data to perform ranking.")
            return []

        # Generate TF-IDF Matrix and compute Cosine Similarity
        tfidf_matrix = self.vectorizer.fit_transform(document_corpus)
        similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

        final_rankings = []
        for i, (profile, score) in enumerate(zip(candidate_profiles, similarity_matrix)):
            
            # UPGRADE: Scale the raw cosine score to a human-readable ATS percentage curve
            curved_score = min(round((score * 2.5) * 100, 2), 99.00) 
            
            # Generate the Gap Analysis
            missing_words = self.extract_missing_keywords(job_desc, raw_resumes[i])

            final_rankings.append({
                "Candidate Name": profile["name"],
                "Source File": profile["filename"],
                "Match Score": curved_score,
                "Missing Keywords": missing_words
            })

        # Sort dynamically by highest match score
        final_rankings.sort(key=lambda x: x['Match Score'], reverse=True)
        return final_rankings

    def export_to_csv(self, rankings_data: List[Dict], export_path: str) -> str:
        """Converts the Python dictionary data into a downloadable CSV report for HR."""
        if not rankings_data:
            return ""
            
        csv_data = []
        for r in rankings_data:
            row = r.copy()
            row['Missing Keywords'] = ", ".join(row['Missing Keywords'])
            csv_data.append(row)

        dataframe = pd.DataFrame(csv_data)
        dataframe.index = dataframe.index + 1
        dataframe.index.name = 'Overall Rank'
        dataframe.to_csv(export_path)
        return export_path