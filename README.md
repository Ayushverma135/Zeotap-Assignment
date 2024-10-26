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

## Assignment 2: WeatherPro 

### Overview 

WeatherPro is a web application designed for real-time weather monitoring, allowing users to check 
current weather conditions and five-day forecasts for various cities. The application provides a 
simple and intuitive user interface built using Streamlit and fetches weather data from the 
OpenWeatherMap API. Users can add cities to their watchlist and receive timely updates on weather 
conditions. 

### Features 
1. **Current Weather Updates:**
  - Users can enter city names to view the current weather conditions, including temperature, 
humidity, and weather description. 
  - Weather icons are displayed based on the current weather conditions, enhancing visual 
representation.

2. **Five-Day Forecast:** 
  - The application provides a five-day weather forecast, including daily temperature highs and 
lows, humidity levels, and conditions. 
  - Each forecast entry is clearly labeled with the corresponding weekday (e.g., Monday, 
Tuesday).

3. **Add City Functionality:** 
  - Users can easily add cities to their watchlist by entering the city name and clicking the "Add 
City" button. 
  - The added cities are stored in memory and can be displayed together with their weather 
updates.

4. **Responsive Design:**
  - The user interface is designed to be visually appealing and responsive, ensuring a seamless 
experience across various devices.

5. **Scheduled Updates:** 
  - Weather data is fetched automatically at regular intervals (every 5 minutes) to keep users 
informed.

### Technical Implementation 

1. **API Integration:** 
  - The application integrates with the OpenWeatherMap API to fetch weather data. Users must 
sign up for a free API key to access the service. 
  - The current weather and five-day forecast are retrieved using separate API calls.

2. **Data Processing:**
  - The retrieved data is parsed to extract relevant information such as temperature, humidity, 
weather conditions, and icon codes.
  - The application organizes this data into a user-friendly format for display.

3. **User Interface with Streamlit:**
  - The frontend is built using Streamlit, which facilitates rapid deployment of web applications 
with Python. Key components of the UI include: 
    - An input field for city names. 
    - A button to add cities to the watchlist. 
    - Display sections for current weather and five-day forecasts. 
    - Weather icons corresponding to the weather conditions.

4. **Scheduler Setup:**
  - APScheduler is utilized to periodically fetch weather updates every 5 minutes. This ensures 
that users always have access to the most current weather data.

5. **Weather Widget Display:** 
  - The current weather and forecasts are displayed in a widget-style format, making it easy for 
users to read and interpret the information.

### User Experience 
  - Adding a City: Users can easily input city names, and upon submission, the application 
fetches and displays the corresponding weather data. 
  - Viewing Weather Updates: Current weather conditions and the five-day forecast are 
displayed in a clean and organized manner, allowing for quick reference. 
  - Weather Icons: Icons representing the weather conditions enhance the visual appeal and 
provide immediate context for users. 

### Error Handling 

The application includes error handling to manage issues that may arise during data fetching and 
user input. Users receive feedback if: 
- The city name input is empty or invalid. 
- There are errors in fetching data from the OpenWeatherMap API (e.g., city not found). 
- Network issues prevent data retrieval. 

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
  streamlit run weather.py
  ```


### Conclusion 

WeatherPro is an innovative and user-friendly application that simplifies real-time weather 
monitoring. With its intuitive interface and reliable backend, it serves as a powerful tool for users 
who want to stay informed about weather conditions in their chosen cities. Future improvements 
could include: 
- User accounts to save preferred cities across sessions. 
- Enhanced visualizations, such as temperature trends over time. 
- Support for additional weather metrics and historical data.

This project demonstrates the practical application of web technologies and APIs, providing valuable 
insights into real-time data handling and user interface design. 

### Screenshot

![screencapture-localhost-8501-2024-10-26-23_58_27](https://github.com/user-attachments/assets/7f2fd818-aaa1-4c35-a3c2-d644fb8e66c9)

