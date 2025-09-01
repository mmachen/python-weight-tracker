Flask Weight & Body Tracker
A simple, self-contained, multi-user web application for tracking weight, body fat percentage, and waist circumference. Built with Flask and Python, this application uses a local Excel file for data persistence, making it easy to set up and manage without needing a database.

✨ Key Features
Multi-User Support: Add, delete, and switch between multiple user profiles.

Comprehensive Tracking: Log daily entries for weight, body fat percentage (optional), and waist size (optional).

Goal Setting: Set and visualize start and goal weights.

Interactive Visualizations:

A primary line chart to track weight progress over time.

Compare your weight progress against another user on a dual-axis chart.

Separate, optional charts for body fat % and waist size trends.

Data Summary: A dashboard card that shows key statistics like current, start, goal, highest, and lowest metrics.

Full CRUD Functionality: Create, read, update, and delete any entry or user profile.

File-Based Storage: All data is saved in a local weights.xlsx file, making your data portable and easy to back up or edit manually.

Single-File Application: The entire Flask backend and frontend template are contained within a single Python script for simplicity.

🛠️ Technology Stack
Backend: Python 3, Flask

Data Storage: openpyxl library for reading from and writing to an Excel (.xlsx) file.

Frontend: HTML, CSS, JavaScript

Charting Library: Chart.js with the chartjs-plugin-annotation for goal lines.

Fonts: Google Fonts (Inter)

🚀 Getting Started
Follow these instructions to get a copy of the project up and running on your local machine.

Prerequisites
Python 3.6 or newer

pip (Python package installer)

Installation & Setup
Clone the Repository:

git clone [https://github.com/your-username/your-repository-name.git](https://github.com/your-username/your-repository-name.git)
cd your-repository-name

Create and Activate a Virtual Environment (Recommended):

Windows:

python -m venv venv
.\venv\Scripts\activate

macOS / Linux:

python3 -m venv venv
source venv/bin/activate

Install Dependencies:
This project uses a few Python packages. Install them using the requirements.txt file.

pip install -r requirements.txt

(If you don't have a requirements.txt file, create one and add the following lines):

Flask
openpyxl

Run the Application:
Execute the main Python script.

python your_script_name.py

(Replace your_script_name.py with the actual name of your Python file).

Access the Application:
Open your web browser and navigate to:
http://127.0.0.1:5000

The application will automatically create the static directory, the style.css file, and the weights.xlsx data file on the first run.

📁 File Structure
The project is organized to be simple and self-contained:

.
├── your_script_name.py    # Main Flask application file containing all backend logic and HTML/CSS.
├── requirements.txt       # Lists the required Python packages.
├── static/                # (Auto-generated) Contains the CSS file.
│   └── style.css
└── weights.xlsx           # (Auto-generated) The Excel file used as the database.

your_script_name.py: The heart of the application. It runs the Flask server, defines all routes, handles data manipulation with openpyxl, and contains the complete HTML, CSS, and JavaScript as Python strings.

weights.xlsx: This file stores all user data.

Weight Data sheet: Contains all time-series entries (date, weight, user, body fat %, waist size).

Users sheet: Contains user profiles and their corresponding goals.

🤝 Contributing
Contributions are welcome! If you have suggestions for improvements, please feel free to fork the repository and submit a pull request.

Fork the Project

Create your Feature Branch (git checkout -b feature/AmazingFeature)

Commit your Changes (git commit -m 'Add some AmazingFeature')

Push to the Branch (git push origin feature/AmazingFeature)

Open a Pull Request

📄 License
This project is distributed under the MIT License. See the LICENSE file for more information.
