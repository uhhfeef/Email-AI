import csv
import pandas as pd   
from flask import Flask, request
import joblib
import numpy as np
from sklearn.preprocessing import OneHotEncoder
import requests
import regex as re
import os
import sqlite3

df = pd.read_csv('../data/gmail_data-6-months.csv')

# Loading the model
loaded_model = joblib.load('../models/email_read_model.joblib')
loaded_vectorizer = joblib.load('../models/email_vectorizer.joblib')

# Function to remove URLs from text
def remove_urls_numbers(text):
    url_pattern = re.compile(r'https?://\S+|www\.\S+|\d+')
    return url_pattern.sub(r'', text)

def extract_domain_names(text):
    sender = re.compile(r'(?<=@)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    matches = sender.findall(text)
    return matches[0] if matches else None  # Return None if no match found

df['From'] = df['From'].apply(extract_domain_names)

sender_stats = df.groupby('From').agg({
    'From': 'count',
    'Read': 'mean'
}).rename(columns={'From': 'from_frequency', 'Read': 'from_read_rate'}).reset_index()

df = df.merge(sender_stats, on='From', how='left')
print(df.head())


# Function to predict on a new email
def predict_email_read(from_address, subject, body):
    # Load the saved model and vectorizer

    # Apply body changes
    clean_body = remove_urls_numbers(body)
    domain_name = extract_domain_names(from_address)

    # Create features
    from_freq = df[df['From'] == domain_name]['from_frequency'].values[0] if domain_name in df['From'].values else 0
    from_read_rate = df[df['From'] == domain_name]['from_read_rate'].values[0] if domain_name in df['From'].values else 0
    email_length = len(clean_body)
    # print(from_freq, from_read_rate, email_length)

    # Process body
    tfidf_body = loaded_vectorizer.transform([clean_body])
    tfidf_subject = loaded_vectorizer.transform([subject])

    # Combine features
    email_features = pd.DataFrame({
        'from_frequency': [from_freq],
        'from_read_rate': [from_read_rate],
        'email_length': [email_length]
    })
    email_features = pd.concat([
        email_features,
        pd.DataFrame(tfidf_body.toarray(), columns=loaded_vectorizer.get_feature_names_out()),
        pd.DataFrame(tfidf_subject.toarray(), columns=loaded_vectorizer.get_feature_names_out())
    ], axis=1)

    # Predict
    prediction = loaded_model.predict(email_features)
    probability = loaded_model.predict_proba(email_features)[0][1]  # Probability of being read

    # return prediction[0], probability
    return probability



if __name__ == '__main__':
    app.run(port=5001)