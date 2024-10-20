# Zeotap-Assignment


## Assignment 1: RuleCrafter

### Overview

**RuleCrafter** is a rule engine application designed to simplify the process of adding, evaluating, and managing rules using SQL-like syntax. The application provides a user-friendly interface for users to input rules, which are then converted into a structured JSON format for easy evaluation. The engine uses an Abstract Syntax Tree (AST) for parsing and evaluating the rules against user-provided data.

### Features

- **Add New Rules**: Users can input rules in a SQL format (e.g., `age = 30 AND department = 'Sales'`) and store them in an SQLite database.
- **Evaluate Rules**: The application evaluates the stored rules against user input data, providing feedback on whether the conditions are met.
- **Remove Rules**: Users can easily remove existing rules from the database.
- **User-Friendly Interface**: Built using Streamlit, the application offers a clean and intuitive interface for rule management.

### Technologies Used

- **Programming Language**: Python
- **Web Framework**: Streamlit
- **Database**: SQLite
- **Data Structures**: Abstract Syntax Tree (AST)

### Installation

1. **Clone the Repository**:
```bash
git clone https://github.com/Ayushverma135/Zeotap-Assignment.git
cd Zeotap-Assignment
```

2. **Install Dependencies**:
  ```bash
  pip install streamlit
  ```

3. **Run the Application**:
  ```bash
  streamlit run app_ast.py
  ```

### Usage
1. **Adding a New Rule**:
   
  - Navigate to the "Add a New Rule" section.
  - Enter your rule in SQL format.
  - Click "Add Rule" to save the rule.

2. **Evaluating Rules**:

  - Input the required data in the "Evaluate Rules" section.
  - Click "Evaluate Rules" to check which rules are satisfied based on the provided data.

3. **Removing a Rule**:

  - In the "Remove a Rule" section, select the rule you wish to delete and click "Remove Rule".

4. **Rule Format**:
   
  - The rules should be entered in a SQL-like format. Here are some examples:
      - `age = 30`
      - `experience > 5`
      - `department = 'Sales' AND salary >= 50000`

### Screenshot

![rulecrafter_screenshot](https://github.com/user-attachments/assets/235ae6ca-f071-4d94-9ab4-db69392044f4)
