# Flask Weight & Body Tracker

A simple, self-contained, multi-user web application for tracking weight, body fat percentage, and waist circumference. Built with Flask and Python, this application uses a local Excel file for data persistence, making it easy to set up and manage without needing a database.

## ✨ Key Features

* **Multi-User Support**: Add, delete, and switch between multiple user profiles.
* **Comprehensive Tracking**: Log daily entries for weight, body fat percentage (optional), and waist size (optional).
* **Goal Setting**: Set and visualize start and goal weights.
* **Interactive Visualizations**:
  * A primary line chart to track weight progress over time.
  * Compare your weight progress against another user on a dual-axis chart.
  * Separate, optional charts for body fat % and waist size trends.
* **Data Summary**: A dashboard card that shows key statistics like current, start, goal, highest, and lowest metrics.
* **Full CRUD Functionality**: Create, read, update, and delete any entry or user profile.
* **File-Based Storage**: All data is saved in a local `weights.xlsx` file, making your data portable and easy to back up or edit manually.
* **Single-File Application**: The entire Flask backend and frontend template are contained within a single Python script for simplicity.

## 🛠️ Technology Stack

* **Backend**: Python 3, Flask
* **Data Storage**: `openpyxl` library for reading from and writing to an Excel (`.xlsx`) file.
* **Frontend**: HTML, CSS, JavaScript
* **Charting Library**: `Chart.js` with the `chartjs-plugin-annotation` for goal lines.
* **Fonts**: Google Fonts (Inter)

## 🚀 Getting Started

Follow these instructions to get a copy of the project up and running on your local machine.

### Prerequisites

* Python 3.6 or newer
* `pip` (Python package installer)

### Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone [https://github.com/your-username/your-repository-name.git](https://github.com/your-username/your-repository-name.git)
   cd your-repository-name
