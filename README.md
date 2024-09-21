# Email-AI

This project implements a real-time email prediction system that integrates with Gmail to predict whether an email will be read or not. It consists of a webhook for processing new emails, a Flask API for serving predictions, and a Chrome extension for displaying predictions in the Gmail interface.

### Components

1. Webhook: Receives new email data and generates predictions.
2. SQLite Database: Stores email predictions.
3. Flask API: Serves recent predictions to the Chrome extension.
4. Chrome Extension: Displays predictions in the Gmail UI.
