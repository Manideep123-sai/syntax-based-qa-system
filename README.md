# Syntax-Based QA System
A question answering system that uses syntax-based parsing, NLP, Wikipedia API, and DuckDuckGo search to extract answers automatically from the web.

---

## Project Overview
This project reads questions from `questions.txt`, identifies their type (Person, Location, Date, Number, Capital), and extracts the best possible answer using:

- SpaCy (NLP)
- Wikipedia API
- DuckDuckGo Search
- Entity extraction and regex patterns
- Multithreading for faster processing
- Web text filtering and cleaning

The results are printed in the terminal and saved to `answers.txt`.

---

## Project Structure
syntax-based-qa-system/
│── main.py # main QA engine
│── questions.txt # list of questions
│── answers.txt # auto-generated answers
│── README.md # documentation

yaml
Copy code

---

## Features
- Automatically detects question type:
  - PERSON  
  - LOCATION  
  - DATE  
  - NUMBER  
  - PLACE (Capital city)
- Fetches relevant text from:
  - Wikipedia API  
  - DuckDuckGo Search
- Performs named-entity extraction (NER)
- Cleans and filters answers for accuracy
- Writes final results to `answers.txt`

---

## How to Run the Project

### 1. Create a Python Virtual Environment
```sh
python -m venv qa_env
qa_env\Scripts\activate
2. Install Required Libraries
sh
Copy code
pip install spacy duckduckgo-search wikipedia-api requests ddgs
python -m spacy download en_core_web_sm
3. Run the Program
sh
Copy code
python main.py
Input File: questions.txt
Example:

vbnet
Copy code
Where is the Taj Mahal located?
Who invented the airplane?
How many continents are there?
What is the capital of Japan?
When was Microsoft founded?
...
Output File: answers.txt
Contains automatically generated answers for each question.

Example:

yaml
Copy code
Question 1: India (LOCATION)

Question 2: Orville Wright (PERSON)

Question 3: Seven (NUMBER)
Technologies Used
Python 3

SpaCy NLP

Wikipedia API

DuckDuckGo Search (DDGS)

Regular expressions

Multithreading (ThreadPoolExecutor)

