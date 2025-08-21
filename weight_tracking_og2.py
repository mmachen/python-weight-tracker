import os
import datetime
from flask import Flask, render_template_string, request, redirect, url_for, flash
import openpyxl

# --- Configuration ---
# This script creates a complete Flask application in a single file.
# It will generate the necessary HTML and CSS files automatically.

# Define the absolute base directory of the script to ensure paths are correct
# regardless of where the script is run from.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define the folder structure using absolute paths
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
CSS_FILE = os.path.join(STATIC_FOLDER, 'style.css')
EXCEL_FILE = os.path.join(BASE_DIR, 'weights.xlsx')

# --- HTML Content ---
# This is the HTML for our web page.
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weight Tracker</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <div class="container">
        <h1>Weight Tracker 🏋️</h1>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="flash-messages">
                {% for category, message in messages %}
                    <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
                </div>
            {% endif %}
        {% endwith %}

        <div class="main-grid">
            <div class="left-column">
                <div class="card">
                    <h2>User Selection & Management</h2>
                    <div class="user-management-grid">
                        <form action="/" method="get" class="user-selector-form">
                            <div class="form-group">
                                <label for="user1">Primary User:</label>
                                <select name="user1" id="user1" onchange="this.form.submit()">
                                    {% for u in all_users %}
                                    <option value="{{ u }}" {% if u == primary_user %}selected{% endif %}>{{ u }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="user2">Compare With (Optional):</label>
                                <select name="user2" id="user2" onchange="this.form.submit()">
                                    <option value="">-- None --</option>
                                    {% for u in all_users %}
                                        {% if u != primary_user %}
                                        <option value="{{ u }}" {% if u == comparison_user %}selected{% endif %}>{{ u }}</option>
                                        {% endif %}
                                    {% endfor %}
                                </select>
                            </div>
                        </form>
                        <div class="user-actions">
                            <form action="{{ url_for('add_user') }}" method="post" class="add-user-form">
                                <label for="new_user_name">Add New User:</label>
                                <div class="input-with-button">
                                    <input type="text" name="new_user_name" id="new_user_name" placeholder="Enter name" required>
                                    <button type="submit" class="btn btn-primary">Add</button>
                                </div>
                            </form>
                            <form action="{{ url_for('delete_user') }}" method="post">
                                <input type="hidden" name="user" value="{{ primary_user }}">
                                <button type="submit" class="btn btn-danger" onclick="return confirm('Are you sure you want to delete {{ primary_user }} and all their data? This cannot be undone.');">Delete Primary User</button>
                            </form>
                        </div>
                    </div>
                </div>
                <div class="card">
                    <h2>Log New Weight for {{ primary_user }}</h2>
                    <form action="{{ url_for('index') }}" method="post" class="log-entry-form">
                        <input type="hidden" name="user" value="{{ primary_user }}">
                        <div class="log-entry-form-grid">
                            <div class="form-group">
                                <label for="weight">Current Weight (lbs):</label>
                                <input type="number" id="weight" name="weight" step="0.1" required placeholder="e.g., 175.5">
                            </div>
                            <div class="form-group">
                                <label for="date">Date:</label>
                                <input type="date" id="date" name="date" value="{{ today_date }}" required>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary">Add Weight Entry</button>
                    </form>
                </div>
                <div class="card">
                    <h2>{{ primary_user }}'s Goals</h2>
                    <form action="{{ url_for('update_goals') }}" method="post" class="goal-form">
                        <input type="hidden" name="user" value="{{ primary_user }}">
                        <div class="form-group">
                            <label for="start_weight">Start Weight (lbs):</label>
                            <input type="number" id="start_weight" name="start_weight" step="0.1" placeholder="e.g., 180.0" value="{{ primary_user_data.start_weight or '' }}">
                        </div>
                        <div class="form-group">
                            <label for="goal_weight">Goal Weight (lbs):</label>
                            <input type="number" id="goal_weight" name="goal_weight" step="0.1" placeholder="e.g., 165.0" value="{{ primary_user_data.goal_weight or '' }}">
                        </div>
                        <button type="submit" class="btn btn-secondary">Save Goals</button>
                    </form>
                </div>
                <div class="card">
                    <h2>History</h2>
                    {% if entries %}
                        <table>
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Weight (lbs)</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for entry in entries %}
                                    <tr>
                                        <td>{{ entry.date }}</td>
                                        <td>{{ entry.weight }}</td>
                                        <td>
                                            <!-- The actual Excel row number is passed to the delete route -->
                                            <a href="#" class="btn btn-secondary btn-sm" onclick="openEditModal('{{ entry.row_num }}', '{{ entry.date }}', '{{ entry.weight }}')">Edit</a>
                                            <a href="{{ url_for('delete_entry', row_index=entry.row_num) }}" class="btn btn-danger btn-sm">Delete</a>
                                        </td>
                                    </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    {% else %}
                        <p>No weight entries yet. Add one above to get started!</p>
                    {% endif %}
                </div>
            </div>
            <div class="right-column">
                <div class="card chart-card">
                    <h2>Progress Chart</h2>
                    {% if combined_labels %}
                        <canvas id="weightChart"></canvas>
                    {% else %}
                        <p>No data to display. Add a weight entry to see the chart.</p>
                    {% endif %}
                </div>
                <div class="card">
                    <h2>Summary</h2>
                    {% if summary_data %}
                        <table class="summary-table">
                            <tbody>
                                <tr>
                                    <td>Current Weight</td>
                                    <td>{{ '%.1f lbs'|format(summary_data.current) if summary_data.current is not none else 'N/A' }}</td>
                                </tr>
                                <tr>
                                    <td>Start Weight</td>
                                    <td>{{ '%.1f lbs'|format(summary_data.start) if summary_data.start is not none else 'N/A' }}</td>
                                </tr>
                                <tr>
                                    <td>Goal Weight</td>
                                    <td>{{ '%.1f lbs'|format(summary_data.goal) if summary_data.goal is not none else 'N/A' }}</td>
                                </tr>
                                <tr class="{{ summary_data.goal_class }}">
                                    <td>Weight to Goal</td>
                                    <td>{{ summary_data.to_goal if summary_data.to_goal is not none else 'N/A' }}</td>
                                </tr>
                                <tr>
                                    <td>Highest Weight</td>
                                    <td>{{ '%.1f lbs'|format(summary_data.highest) if summary_data.highest is not none else 'N/A' }}</td>
                                </tr>
                                <tr>
                                    <td>Lowest Weight</td>
                                    <td>{{ '%.1f lbs'|format(summary_data.lowest) if summary_data.lowest is not none else 'N/A' }}</td>
                                </tr>
                            </tbody>
                        </table>
                    {% else %}
                        <p>No data for summary.</p>
                    {% endif %}
                </div>
            </div>
        </div>

    </div>

    <div id="editModal" class="modal">
        <div class="modal-content">
            <span class="close-button" onclick="closeEditModal()">&times;</span>
            <h2>Edit Weight Entry</h2>
            <form id="editForm" method="post">
                <div class="form-group">
                    <label for="edit_date">Date:</label>
                    <input type="date" id="edit_date" name="date" required>
                </div>
                <div class="form-group">
                    <label for="edit_weight">Weight (lbs):</label>
                    <input type="number" id="edit_weight" name="weight" step="0.1" required>
                </div>
                <button type="submit" class="btn btn-primary">Save Changes</button>
            </form>
        </div>
    </div>

    <script>
        // Only run the chart script if there is data
        {% if combined_labels and chart_data_1 %}
        const ctx = document.getElementById('weightChart').getContext('2d');
        const chart_config = {{ chart_config | tojson }};
        
        const datasets = [{
            label: '{{ primary_user }} Weight (lbs)',
            data: {{ chart_data_1 | tojson }},
            borderColor: '#33CFFF', // Bright Blue
            backgroundColor: 'rgba(51, 207, 255, 0.1)',
            yAxisID: 'y1', // Link to the first y-axis
            fill: true,
            tension: 0.1,
            spanGaps: true // Connect points with null data
        }];

        // Add second dataset if a comparison user is selected
        {% if comparison_user and chart_data_2_to_plot %}
        datasets.push({
            label: '{{ comparison_user }} Weight (lbs)',
            data: {{ chart_data_2_to_plot | tojson }},
            borderColor: '#9D63FF', // Bright Purple
            backgroundColor: 'rgba(157, 99, 255, 0.1)',
            yAxisID: 'y2',
            fill: true,
            tension: 0.1,
            spanGaps: true // Connect points with null data
        });
        {% endif %}

        const chartData = {
            labels: {{ combined_labels | tojson }},
            datasets: datasets
        };

        const chartOptions = {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: '{{ primary_user }} Weight (lbs)',
                        color: '#33CFFF'
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) { label += ': '; }
                            if (context.parsed.y !== null) {
                                let value_to_show = context.parsed.y;
                                label += value_to_show.toFixed(1) + ' lbs';
                            }
                            return label;
                        }
                    }
                },
                annotation: {
                    annotations: {}
                }
            }
        };

        // Add second y-axis if a comparison user is selected
        if (chart_config.y2_axis_label) {
            chartOptions.scales.y2 = {
                type: 'linear',
                display: true,
                position: 'right',
                title: {
                    display: true,
                    text: chart_config.y2_axis_label,
                    color: '#9D63FF'
                },
                grid: {
                    drawOnChartArea: false, // only draw grid for y1
                },
            };
        }

        // Annotations for Primary User
        {% if primary_user_data.start_weight %}
        chartOptions.plugins.annotation.annotations.startLine1 = {
            type: 'line',
            yMin: {{ primary_user_data.start_weight }},
            yMax: {{ primary_user_data.start_weight }},
            yScaleID: 'y1',
            borderColor: '#33CFFF',
            borderWidth: 2,
            borderDash: [6, 6],
            label: { content: 'Start: {{ primary_user_data.start_weight }} lbs', display: {{ 'false' if comparison_user else 'true' }}, position: 'start', backgroundColor: 'rgba(51, 207, 255, 0.8)' }
        };
        {% endif %}
        {% if primary_user_data.goal_weight %}
        chartOptions.plugins.annotation.annotations.goalLine1 = {
            type: 'line',
            yMin: {{ primary_user_data.goal_weight }},
            yMax: {{ primary_user_data.goal_weight }},
            yScaleID: 'y1',
            borderColor: 'var(--danger-color)',
            borderWidth: 2,
            borderDash: [6, 6],
            label: { content: 'Goal: {{ primary_user_data.goal_weight }} lbs', display: {{ 'false' if comparison_user else 'true' }}, position: 'end', backgroundColor: 'rgba(220, 53, 69, 0.8)' }
        };
        {% endif %}

        // Annotations for Comparison User
        {% if comparison_user and comparison_user_data.start_weight is not none %}
        chartOptions.plugins.annotation.annotations.startLine2 = {
            type: 'line',
            yMin: {{ comparison_user_data.start_weight }},
            yMax: {{ comparison_user_data.start_weight }},
            yScaleID: 'y2',
            borderColor: '#9D63FF',
            borderWidth: 2,
            borderDash: [6, 6],
            label: { content: 'Start: {{ comparison_user_data.start_weight }} lbs', display: false, position: 'start', backgroundColor: 'rgba(157, 99, 255, 0.8)' }
        };
        {% endif %}
        {% if comparison_user and comparison_user_data.goal_weight is not none %}
        chartOptions.plugins.annotation.annotations.goalLine2 = {
            type: 'line',
            yMin: {{ comparison_user_data.goal_weight }},
            yMax: {{ comparison_user_data.goal_weight }},
            yScaleID: 'y2',
            borderColor: 'var(--danger-color)',
            borderWidth: 2,
            borderDash: [6, 6],
            label: { content: 'Goal: {{ comparison_user_data.goal_weight }} lbs', display: false, position: 'end', backgroundColor: 'rgba(220, 53, 69, 0.8)' }
        };
        {% endif %}

        // Set the min and max limits for the y1 axis if they are provided
        if (chart_config.y1_min !== null && chart_config.y1_max !== null) {
            chartOptions.scales.y1.min = chart_config.y1_min;
            chartOptions.scales.y1.max = chart_config.y1_max;
        }

        // Set the min and max limits for the y2 axis if they are provided
        if (chart_config.y2_axis_label && chart_config.y2_min !== null && chart_config.y2_max !== null) {
            chartOptions.scales.y2.min = chart_config.y2_min;
            chartOptions.scales.y2.max = chart_config.y2_max;
        }

        new Chart(ctx, { type: 'line', data: chartData, options: chartOptions });
        {% endif %}

        // --- Modal Control Functions ---
        function openEditModal(row_index, date, weight) {
            const modal = document.getElementById('editModal');
            const form = document.getElementById('editForm');
            document.getElementById('edit_date').value = date;
            document.getElementById('edit_weight').value = weight;
            form.action = `/update/${row_index}`;
            modal.style.display = 'block';
        }

        function closeEditModal() {
            const modal = document.getElementById('editModal');
            modal.style.display = 'none';
        }

        // Close modal if user clicks outside of it
        window.onclick = function(event) {
            const modal = document.getElementById('editModal');
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        }
    </script>
</body>
</html>
"""

# --- CSS Content ---
# This is the styling for our web page.
CSS_CONTENT = """
:root {
    --primary-color: #33CFFF;
    --secondary-color: #9D63FF;
    --danger-color: #dc3545;
    --background-color: #f4f7f6;
    --card-background: #ffffff;
    --text-color: #333;
    --border-color: #e0e0e0;
    --shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

body {
    font-family: 'Inter', sans-serif;
    background-color: var(--background-color);
    color: var(--text-color);
    margin: 0;
    padding: 20px;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    min-height: 100vh;
}

.container {
    width: 100%;
    max-width: 1200px; /* Increased width for two columns */
    display: flex;
    flex-direction: column;
    gap: 20px;
}

h1 {
    text-align: center;
    color: var(--primary-color);
    margin-bottom: 10px;
}

.card {
    background-color: var(--card-background);
    border-radius: 12px;
    padding: 25px;
    box-shadow: var(--shadow);
    border: 1px solid var(--border-color);
}

.user-management-grid {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.user-selector-form {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.user-actions {
    display: flex;
    flex-direction: column;
    gap: 15px;
    margin-top: 10px;
    border-top: 1px solid var(--border-color);
    padding-top: 20px;
}

.user-actions .btn {
    width: 100%;
}

.user-actions form:not(.add-user-form) .btn {
    width: 100%;
}

.input-with-button {
    display: flex;
    gap: 10px;
}

.input-with-button input {
    flex-grow: 1;
}

.goal-form {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    align-items: end;
}

.log-entry-form .btn-primary {
    width: 100%;
}

.log-entry-form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 20px;
}

.log-entry-form-grid .form-group {
    margin-bottom: 0;
}

.form-group {
    margin-bottom: 20px;
}

label {
    display: block;
    margin-bottom: 8px;
    font-weight: 500;
}

input[type="number"], input[type="text"], input[type="date"] {
    width: 100%;
    padding: 12px;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    box-sizing: border-box;
    font-size: 1rem;
}

select {
    width: 100%;
    padding: 10px;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    font-size: 1rem;
    background-color: white;
    box-sizing: border-box;
}

.btn {
    padding: 12px 20px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 1rem;
    font-weight: 500;
    transition: all 0.2s ease-in-out;
    text-decoration: none;
    display: inline-block;
    text-align: center;
}

.btn-primary {
    background-color: var(--primary-color);
    color: white;
}

.btn-primary:hover {
    opacity: 0.9;
    transform: translateY(-2px);
}

.btn-secondary {
    background-color: var(--secondary-color);
    color: white;
    width: 100%;
}

.btn-sm {
    padding: 5px 10px;
    font-size: 0.875rem;
}

.btn-secondary:hover {
    opacity: 0.9;
}

.btn-danger {
    background-color: var(--danger-color);
    color: white;
}

.btn-danger:hover {
    opacity: 0.9;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
}

th, td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}

thead th {
    font-weight: 600;
}

tbody tr:last-child td {
    border-bottom: none;
}

/* --- New Two-Column Layout Styles --- */
.main-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); /* Two equal-width columns */
    gap: 20px;
    align-items: start;
}

.left-column {
    display: flex;
    flex-direction: column;
    min-width: 0; /* Prevents flexbox from overflowing its grid cell */
    gap: 20px;
}

.right-column {
    position: sticky; /* Makes the column stick */
    top: 20px; /* Stick to the top after 20px of scrolling */
}

.chart-card {
    height: 100%;
}

/* Summary Table Styles */
.summary-table {
    margin-top: 0;
}

.summary-table td {
    padding: 10px 0;
}

.summary-table td:first-child {
    font-weight: 500;
    color: #555;
}

.summary-table td:last-child {
    text-align: right;
    font-weight: 600;
}

.goal-positive { color: #155724; }
.goal-negative { color: #721c24; }

/* Modal Styles */
.modal {
    display: none; 
    position: fixed; 
    z-index: 1000; 
    left: 0;
    top: 0;
    width: 100%; 
    height: 100%; 
    overflow: auto; 
    background-color: rgba(0,0,0,0.5);
}

.modal-content {
    background-color: #fefefe;
    margin: 15% auto; 
    padding: 30px;
    border: 1px solid #888;
    width: 80%;
    max-width: 500px;
    border-radius: 12px;
    position: relative;
}

.close-button {
    color: #aaa;
    position: absolute;
    top: 10px;
    right: 20px;
    font-size: 28px;
    font-weight: bold;
}

.close-button:hover,
.close-button:focus {
    color: black;
    text-decoration: none;
    cursor: pointer;
}

/* Flash Messages */
.flash-messages {
    list-style: none;
    padding: 0;
    margin-bottom: 1rem;
}
.flash {
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 0.5rem;
    text-align: center;
}
.flash.success {
    background-color: #d4edda;
    color: #155724;
}
.flash.error {
    background-color: #f8d7da;
    color: #721c24;
}
"""

# 1. Setup: Create directories and files
def setup_environment():
    """Creates necessary directories and files if they don't exist."""
    """Creates and validates necessary directories and files."""
    print("Validating application environment...")
    os.makedirs(STATIC_FOLDER, exist_ok=True)

    # Always write the CSS file to ensure it's up to date with the script.
    with open(CSS_FILE, 'w') as f:
        f.write(CSS_CONTENT)
    print(f"Ensured '{CSS_FILE}' is up to date.")

    # --- Excel File Validation and Creation ---
    if not os.path.exists(EXCEL_FILE):
        # Create a brand new workbook if the file doesn't exist
        workbook = openpyxl.Workbook()
        
        # Create "Weight Data" sheet
        sheet_data = workbook.active
        sheet_data.title = "Weight Data"
        sheet_data.append(["Date", "Weight (lbs)", "User"])

        # Create "Users" sheet
        sheet_users = workbook.create_sheet("Users")
        sheet_users.append(["Username", "Start Weight (lbs)", "Goal Weight (lbs)"])
        sheet_users.append(["User 1", None, None])
        sheet_users.append(["User 2", None, None])
        
        workbook.save(EXCEL_FILE)
        print(f"Created '{EXCEL_FILE}' with 'Weight Data' and 'Users' sheets.")
    else:
        # If file exists, validate its structure to prevent KeyErrors.
        workbook = openpyxl.load_workbook(EXCEL_FILE)
        if "Users" not in workbook.sheetnames:
            sheet_users = workbook.create_sheet("Users")
            sheet_users.append(["Username", "Start Weight (lbs)", "Goal Weight (lbs)"])
            sheet_users.append(["User 1", None, None])
            sheet_users.append(["User 2", None, None])
            workbook.save(EXCEL_FILE)
            print("Added missing 'Users' sheet to existing Excel file.")

# Run the setup immediately to ensure files exist before the app is configured.
# This is crucial for the Flask reloader in debug mode.
setup_environment()

# 2. Initialize Flask App
# Explicitly tell Flask where to find the static folder using an absolute path.
app = Flask(__name__, static_folder=STATIC_FOLDER)
# Secret key is needed for flashing messages
app.secret_key = 'a_secure_random_secret_key'

# 3. Define Helper Functions for Excel
def get_users():
    """Reads the list of users from the 'Users' sheet."""
    try:
        workbook = openpyxl.load_workbook(EXCEL_FILE)
        sheet = workbook["Users"]
        users = [row[0] for row in sheet.iter_rows(min_row=2, values_only=True) if row[0]]
        return users
    except (FileNotFoundError, KeyError):
        return ["User 1", "User 2"] # Fallback

def get_user_data(user):
    """Reads start and goal weight for a specific user and converts them to floats."""
    raw_data = {"start_weight": None, "goal_weight": None}
    try:
        workbook = openpyxl.load_workbook(EXCEL_FILE)
        sheet = workbook["Users"]
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if row[0] == user:
                raw_data = {"start_weight": row[1], "goal_weight": row[2]}
                break # Found the user, no need to continue
    except (FileNotFoundError, KeyError):
        return {"start_weight": None, "goal_weight": None}

    # Safely convert values to float, defaulting to None on failure.
    # This handles cases where the Excel cell contains text or is empty.
    start_weight, goal_weight = None, None
    try:
        if raw_data["start_weight"] is not None:
            start_weight = float(raw_data["start_weight"])
    except (ValueError, TypeError):
        pass # Keep as None if conversion fails

    try:
        if raw_data["goal_weight"] is not None:
            goal_weight = float(raw_data["goal_weight"])
    except (ValueError, TypeError):
        pass # Keep as None if conversion fails
        
    return {"start_weight": start_weight, "goal_weight": goal_weight}

def get_weight_entries(active_user):
    """Reads all weight entries for a specific user from the Excel file."""
    entries = []
    try:
        workbook = openpyxl.load_workbook(EXCEL_FILE)
        sheet = workbook["Weight Data"]
        # Iterate over rows, including their index, skipping the header row (row 1).
        # The index will be the actual row number in the Excel sheet.
        for index, row_values in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            # Check if row has enough columns and user matches
            if len(row_values) >= 3 and row_values[2] == active_user:
                date_val = row_values[0]
                weight_val = row_values[1]

                if date_val is not None and weight_val is not None:
                    # --- Robustly convert weight to float ---
                    try:
                        numeric_weight = float(weight_val)
                    except (ValueError, TypeError):
                        # Skip rows where weight is not a valid number
                        continue

                    # --- Date Normalization ---
                    if isinstance(date_val, datetime.datetime):
                        normalized_date = date_val.strftime("%Y-%m-%d")
                    else:
                        # If it's not a datetime object, it's likely already a string.
                        # We'll take the first part in case it has a time component.
                        normalized_date = str(date_val).split(' ')[0]
                    
                    entries.append({
                        "date": normalized_date, 
                        "weight": numeric_weight, # Use the converted numeric weight
                        "row_num": index
                    })
    except FileNotFoundError:
        # This case is handled by setup_environment, but it's good practice
        return []
    return sorted(entries, key=lambda x: x['date'], reverse=True)

def add_weight_entry(date_str, weight, active_user):
    """Adds a new weight entry for a specific user and date to the Excel file."""
    workbook = openpyxl.load_workbook(EXCEL_FILE)
    sheet = workbook["Weight Data"]
    sheet.append([date_str, weight, active_user])
    workbook.save(EXCEL_FILE)

def update_weight_entry(row_index, new_date, new_weight):
    """Finds a row by its index and updates its date and weight."""
    try:
        workbook = openpyxl.load_workbook(EXCEL_FILE)
        sheet = workbook["Weight Data"]
        if 1 < row_index <= sheet.max_row:
            sheet.cell(row=row_index, column=1).value = new_date
            sheet.cell(row=row_index, column=2).value = new_weight
            workbook.save(EXCEL_FILE)
            return True
    except Exception:
        return False

# 4. Define Flask Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    """Handles both displaying the form/data and submitting new data."""
    if request.method == 'POST':
        # This block handles adding a new weight entry
        user = request.form.get('user')
        date_str = request.form.get('date')
        try:
            # Get weight from the form
            weight = float(request.form['weight'])
            if weight > 0 and date_str:
                add_weight_entry(date_str, weight, user)
                flash('Weight entry added successfully!', 'success')
            else:
                flash('Weight must be a positive number.', 'error')
        except (ValueError, TypeError):
            flash('Invalid input. Please enter a valid number for weight.', 'error')
        
        # Redirect to the same primary user's page using GET to prevent form resubmission
        return redirect(url_for('index', user1=user))

    # For a GET request, read data and render the page
    all_users = get_users()
    if not all_users: # Handle case where there are no users
        return render_template_string(HTML_CONTENT, all_users=[], primary_user=None, entries=[], primary_user_data={})

    # --- 1. Get Users and Base Data ---
    primary_user = request.args.get('user1', all_users[0])
    comparison_user = request.args.get('user2') # This will be None if not provided

    # Data for the primary user (for history table and chart)
    entries = get_weight_entries(primary_user) 
    primary_user_data = get_user_data(primary_user)
    today_date = datetime.datetime.now().strftime("%Y-%m-%d")

    # Get comparison user data (will be numeric thanks to get_user_data)
    comparison_user_data = get_user_data(comparison_user) if comparison_user else {}

    # --- 2. Prepare Data for Charting ---
    entries1 = sorted(get_weight_entries(primary_user), key=lambda x: x['date'])
    data1_map = {e['date']: e['weight'] for e in entries1}
    
    # --- 3. Calculate Axis Limits and Chart Config ---
    y1_start = primary_user_data.get('start_weight')
    y1_goal = primary_user_data.get('goal_weight')
    y2_start = comparison_user_data.get('start_weight')
    y2_goal = comparison_user_data.get('goal_weight')

    # Calculate Y1 axis limits
    y1_values = list(data1_map.values())
    if y1_start is not None: y1_values.append(y1_start)
    if y1_goal is not None: y1_values.append(y1_goal)

    y1_min, y1_max = None, None
    valid_y1_values = [v for v in y1_values if v is not None]
    if valid_y1_values:
        padding = 5
        y1_min = min(valid_y1_values) - padding
        y1_max = max(valid_y1_values) + padding

    # Initialize chart data structures
    combined_labels = []
    chart_data_1 = []
    chart_data_2_to_plot = []
    chart_config = {
        "y1_min": y1_min,
        "y1_max": y1_max,
        "y2_axis_label": None,
        "y2_min": None,
        "y2_max": None
    }

    if comparison_user:
        entries2 = sorted(get_weight_entries(comparison_user), key=lambda x: x['date'])
        data2_map = {e['date']: e['weight'] for e in entries2}
        combined_labels = sorted(list(set(data1_map.keys()) | set(data2_map.keys())))
        chart_data_1 = [data1_map.get(date) for date in combined_labels]
        chart_data_2_to_plot = [data2_map.get(date) for date in combined_labels]
        chart_config["y2_axis_label"] = f"{comparison_user} Weight (lbs)"

        # Calculate Y2 axis limits
        y2_values = [v for v in chart_data_2_to_plot if v is not None]
        if y2_start is not None: y2_values.append(y2_start)
        if y2_goal is not None: y2_values.append(y2_goal)
        
        if y2_values:
            padding = 5
            chart_config['y2_min'] = min(y2_values) - padding
            # Use proportional calculation for y2_max if possible, otherwise fallback
            if y1_max is not None and y1_start is not None and y2_start is not None and y1_start > 0:
                chart_config['y2_max'] = y1_max * (y2_start / y1_start)
            else:
                chart_config['y2_max'] = max(y2_values) + padding
    else:
        # If no comparison, use only primary user's data
        combined_labels = [e['date'] for e in entries1]
        chart_data_1 = [e['weight'] for e in entries1]

    # --- 4. Calculate Summary Data ---
    summary_data = {}
    if entries:
        all_weights = [e['weight'] for e in entries]
        summary_data['current'] = all_weights[0] # entries are sorted desc by date
        summary_data['highest'] = max(all_weights)
        summary_data['lowest'] = min(all_weights)
    
    summary_data['start'] = primary_user_data.get('start_weight')
    summary_data['goal'] = primary_user_data.get('goal_weight')

    # Calculate weight to goal
    if summary_data.get('current') and summary_data.get('goal'):
        to_goal = summary_data['current'] - summary_data['goal']
        if to_goal > 0.05: # Using a small threshold to handle float inaccuracies
            summary_data['to_goal'] = f"{to_goal:.1f} lbs to lose"
            summary_data['goal_class'] = 'goal-negative'
        elif to_goal < -0.05:
            summary_data['to_goal'] = f"{-to_goal:.1f} lbs below goal"
            summary_data['goal_class'] = 'goal-positive'
        else:
            summary_data['to_goal'] = "Goal reached!"
            summary_data['goal_class'] = 'goal-positive'

    return render_template_string(
        HTML_CONTENT,
        entries=entries,
        primary_user=primary_user,
        comparison_user=comparison_user,
        all_users=all_users,
        primary_user_data=primary_user_data,
        comparison_user_data=comparison_user_data,
        combined_labels=combined_labels,
        chart_data_1=chart_data_1,
        chart_data_2_to_plot=chart_data_2_to_plot,
        chart_config=chart_config,
        today_date=today_date,
        summary_data=summary_data
    )

@app.route('/update_goals', methods=['POST'])
def update_goals():
    """Updates the start and goal weights for a user."""
    user = request.form.get('user')
    if not user:
        flash("No user selected.", "error")
        return redirect(url_for('index'))

    try:
        # Use .get() to avoid errors if fields are empty, provide None as default
        start_weight = request.form.get('start_weight')
        goal_weight = request.form.get('goal_weight')

        # Convert to float if not empty, else None. Handle potential ValueError.
        start_weight_val = float(start_weight) if start_weight else None
        goal_weight_val = float(goal_weight) if goal_weight else None

        workbook = openpyxl.load_workbook(EXCEL_FILE)
        sheet = workbook["Users"]
        
        # Find the user's row and update it
        user_found = False
        for row in sheet.iter_rows(min_row=2):
            if row[0].value == user:
                row[1].value = start_weight_val
                row[2].value = goal_weight_val
                user_found = True
                break # Stop after finding and updating
        
        if user_found:
            workbook.save(EXCEL_FILE)
            flash(f"Goals for {user} updated successfully!", "success")
        else:
            flash(f"Could not find user {user} to update.", "error")

    except ValueError:
        flash("Invalid input. Please enter valid numbers for weights.", "error")
    except Exception as e:
        flash(f"An error occurred while updating goals: {e}", "error")

    return redirect(url_for('index', user1=user))

@app.route('/add_user', methods=['POST'])
def add_user():
    """Adds a new user to the 'Users' sheet."""
    new_user_name = request.form.get('new_user_name', '').strip()
    if not new_user_name:
        flash("User name cannot be empty.", "error")
        return redirect(url_for('index'))

    if new_user_name in get_users():
        flash(f"User '{new_user_name}' already exists.", "error")
        return redirect(url_for('index'))

    workbook = openpyxl.load_workbook(EXCEL_FILE)
    sheet = workbook["Users"]
    sheet.append([new_user_name, None, None])
    workbook.save(EXCEL_FILE)
    flash(f"User '{new_user_name}' added successfully!", "success")
    return redirect(url_for('index', user1=new_user_name))

@app.route('/update/<int:row_index>', methods=['POST'])
def update_entry(row_index):
    """Updates a specific weight entry."""
    new_date = request.form.get('date')
    try:
        new_weight = float(request.form.get('weight'))
        if new_weight > 0 and new_date:
            if update_weight_entry(row_index, new_date, new_weight):
                flash('Entry updated successfully!', 'success')
            else:
                flash('Could not find entry to update.', 'error')
        else:
            flash('Invalid weight or date.', 'error')
    except (ValueError, TypeError):
        flash('Invalid input for weight.', 'error')
    
    return redirect(request.referrer or url_for('index'))

@app.route('/delete/<int:row_index>')
def delete_entry(row_index):
    """Deletes a specific entry from the Excel file using its row number."""
    try:
        workbook = openpyxl.load_workbook(EXCEL_FILE)
        sheet = workbook["Weight Data"]
        
        # The row_index passed from the template is the actual Excel row number.
        excel_row_to_delete = row_index

        # Check if the row exists before trying to delete (must be > 1 to protect header)
        if 1 < excel_row_to_delete <= sheet.max_row:
            sheet.delete_rows(excel_row_to_delete)
            workbook.save(EXCEL_FILE)
            flash('Entry deleted successfully!', 'success')
        else:
            # This can happen if the user tries to delete a row that doesn't exist
            # (e.g., by manually changing the URL or a race condition)
            flash('Could not find the entry to delete. It may have already been removed.', 'error')
            
    except Exception as e:
        flash(f'An error occurred while deleting: {e}', 'error')
        
    # Redirect back to the user's page that was being viewed
    return redirect(request.referrer or url_for('index'))

@app.route('/delete_user', methods=['POST'])
def delete_user():
    """Deletes a user and all their associated data."""
    user_to_delete = request.form.get('user')
    
    if len(get_users()) <= 1:
        flash("Cannot delete the last user.", "error")
        return redirect(url_for('index', user1=user_to_delete))

    try:
        workbook = openpyxl.load_workbook(EXCEL_FILE)

        # 1. Delete from "Weight Data" sheet
        sheet_data = workbook["Weight Data"]
        rows_to_keep_data = [cell.value for cell in sheet_data[1]] # Header
        data_to_write = [row for row in sheet_data.iter_rows(min_row=2, values_only=True) if row[2] != user_to_delete]
        sheet_data.delete_rows(2, sheet_data.max_row + 1)
        for row_data in data_to_write:
            sheet_data.append(row_data)

        # 2. Delete from "Users" sheet
        sheet_users = workbook["Users"]
        users_to_write = [row for row in sheet_users.iter_rows(min_row=2, values_only=True) if row[0] != user_to_delete]
        sheet_users.delete_rows(2, sheet_users.max_row + 1)
        for user_data in users_to_write:
            sheet_users.append(user_data)

        workbook.save(EXCEL_FILE)
        flash(f"User '{user_to_delete}' and all their data have been deleted.", "success")

    except Exception as e:
        flash(f"An error occurred while deleting the user: {e}", "error")
        return redirect(url_for('index', user1=user_to_delete))

    # Redirect to the main page, which will now select the first available user
    return redirect(url_for('index'))



# 5. Main execution block
if __name__ == '__main__':
    # Run the Flask app
    # host='0.0.0.0' makes it accessible on your local network
    # debug=True allows for auto-reloading on code changes
    # The reloader will execute this block twice. We only want to print the startup message
    # in the main process, not the reloader's child process.
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        print("\n--- Starting Flask Server ---")
        print("Open your web browser and go to: http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
