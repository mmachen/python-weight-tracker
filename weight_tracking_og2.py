import os
import re
import csv
import io
import threading
import datetime
from flask import Flask, render_template_string, request, redirect, url_for, flash, Response
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
    <title>Weight & Body Tracker</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <div class="container">
        <h1>Weight & Body Tracker 🏋️</h1>

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
                            <input type="hidden" name="start_date" value="{{ date_filter.start }}">
                            <input type="hidden" name="end_date" value="{{ date_filter.end }}">
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
                    <h2>Date Range Filter</h2>
                    <form action="/" method="get" class="date-filter-form" id="dateFilterForm">
                        <input type="hidden" name="user1" value="{{ primary_user }}">
                        {% if comparison_user %}
                        <input type="hidden" name="user2" value="{{ comparison_user }}">
                        {% endif %}
                        {% for u in selected_compare_users or [] %}
                        <input type="hidden" name="compare_users" value="{{ u }}">
                        {% endfor %}
                        <div class="date-filter-grid">
                            <div class="form-group">
                                <label for="start_date">From:</label>
                                <input type="date" id="start_date" name="start_date" value="{{ date_filter.start }}">
                            </div>
                            <div class="form-group">
                                <label for="end_date">To:</label>
                                <input type="date" id="end_date" name="end_date" value="{{ date_filter.end }}">
                            </div>
                        </div>
                        <div class="date-presets">
                            <button type="button" class="btn btn-secondary btn-sm" onclick="setDateRange(30)">30d</button>
                            <button type="button" class="btn btn-secondary btn-sm" onclick="setDateRange(90)">90d</button>
                            <button type="button" class="btn btn-secondary btn-sm" onclick="setDateRange(180)">6m</button>
                            <button type="button" class="btn btn-secondary btn-sm" onclick="setDateRange(365)">1y</button>
                            <button type="button" class="btn btn-secondary btn-sm" onclick="setDateRange('ytd')">YTD</button>
                            <button type="button" class="btn btn-secondary btn-sm" onclick="setDateRange('all')">All</button>
                        </div>
                        <button type="submit" class="btn btn-primary btn-block">Apply Filter</button>
                        <p class="form-hint filter-note">{{ date_filter.summary }}</p>
                    </form>
                </div>
                <div class="card">
                    <h2>Multi-User Comparison</h2>
                    <form action="/" method="get" class="multi-user-form">
                        <input type="hidden" name="user1" value="{{ primary_user }}">
                        {% if comparison_user %}
                        <input type="hidden" name="user2" value="{{ comparison_user }}">
                        {% endif %}
                        <input type="hidden" name="start_date" value="{{ date_filter.start }}">
                        <input type="hidden" name="end_date" value="{{ date_filter.end }}">
                        <p class="form-hint">Select users to compare on the normalized chart:</p>
                        <div class="checkbox-grid">
                            {% for u in all_users %}
                            <label class="checkbox-label">
                                <input type="checkbox" name="compare_users" value="{{ u }}" 
                                    {% if u in selected_compare_users %}checked{% endif %}
                                    onchange="this.form.submit()">
                                <span class="checkbox-text">{{ u }}</span>
                            </label>
                            {% endfor %}
                        </div>
                    </form>
                </div>
                <div class="card">
                    <h2>Log New Entry for {{ primary_user }}</h2>
                    <form action="{{ url_for('index') }}" method="post" class="log-entry-form">
                        <input type="hidden" name="user" value="{{ primary_user }}">
                        <input type="hidden" name="start_date" value="{{ date_filter.start }}">
                        <input type="hidden" name="end_date" value="{{ date_filter.end }}">
                        <div class="log-entry-form-grid">
                            <div class="form-group">
                                <label for="weight">Current Weight (lbs):</label>
                                <input type="number" id="weight" name="weight" step="0.01" required placeholder="e.g., 175.50">
                            </div>
                            <div class="form-group">
                                <label for="date">Date:</label>
                                <input type="date" id="date" name="date" value="{{ today_date }}" required>
                            </div>
                            <div class="form-group">
                                <label for="body_fat">Body Fat (%): <span class="optional-text">(Optional)</span></label>
                                <input type="number" id="body_fat" name="body_fat" step="0.01" placeholder="e.g., 21.50">
                            </div>
                            <div class="form-group">
                                <label for="waist_size">Waist Size (in): <span class="optional-text">(Optional)</span></label>
                                <input type="number" id="waist_size" name="waist_size" step="0.01" placeholder="e.g., 34.55">
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary">Add Entry</button>
                    </form>
                </div>
                <div class="card">
                    <h2>{{ primary_user }}'s Goals &amp; Profile</h2>
                    <form action="{{ url_for('update_goals') }}" method="post" class="goal-form">
                        <input type="hidden" name="user" value="{{ primary_user }}">
                        <input type="hidden" name="start_date" value="{{ date_filter.start }}">
                        <input type="hidden" name="end_date" value="{{ date_filter.end }}">
                        <div class="form-group">
                            <label for="start_weight">Start Weight (lbs):</label>
                            <input type="number" id="start_weight" name="start_weight" step="0.01" placeholder="e.g., 180.00" value="{{ primary_user_data.start_weight or '' }}">
                        </div>
                        <div class="form-group">
                            <label for="goal_weight">Goal Weight (lbs):</label>
                            <input type="number" id="goal_weight" name="goal_weight" step="0.01" placeholder="e.g., 165.00" value="{{ primary_user_data.goal_weight or '' }}">
                        </div>
                        <div class="form-group">
                            <label for="height">Height (in): <span class="optional-text">(for BMI)</span></label>
                            <input type="number" id="height" name="height" step="0.25" placeholder="e.g., 70" value="{{ primary_user_data.height or '' }}">
                        </div>
                        <button type="submit" class="btn btn-secondary">Save Goals</button>
                    </form>
                </div>
                <div class="card">
                    <div class="chart-header">
                        <h2>History</h2>
                        {% if entries %}
                        <a href="{{ export_url }}" class="btn btn-secondary btn-sm">Export CSV</a>
                        {% endif %}
                    </div>
                    {% if date_filter.active %}
                    <p class="form-hint filter-note">{{ date_filter.summary }}</p>
                    {% endif %}
                    {% if entries %}
                        <table>
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Weight (lbs)</th>
                                    <th>Body Fat %</th>
                                    <th>Waist (in)</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for entry in entries %}
                                    <tr>
                                        <td>{{ entry.date }}</td>
                                        <td>{{ '%.2f'|format(entry.weight) }}</td>
                                        <td>{{ '%.2f'|format(entry.body_fat) if entry.body_fat is not none else '–' }}</td>
                                        <td>{{ '%.2f'|format(entry.waist_size) if entry.waist_size is not none else '–' }}</td>
                                        <td>
                                            <a href="#" class="btn btn-secondary btn-sm" onclick="openEditModal('{{ entry.id }}', '{{ entry.date }}', '{{ entry.weight }}', '{{ entry.body_fat or '' }}', '{{ entry.waist_size or '' }}')">Edit</a>
                                            <form action="{{ url_for('delete_entry', entry_id=entry.id) }}" method="post" class="inline-form" onsubmit="return confirm('Delete the entry from {{ entry.date }}? This cannot be undone.');">
                                                <button type="submit" class="btn btn-danger btn-sm">Delete</button>
                                            </form>
                                        </td>
                                    </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    {% else %}
                        {% if date_filter.active %}
                        <p>No entries fall inside the selected date range. Widen the range or press "All".</p>
                        {% else %}
                        <p>No entries yet. Add one above to get started!</p>
                        {% endif %}
                    {% endif %}
                </div>
            </div>
            <div class="right-column">
                <div class="card chart-card">
                    <div class="chart-header">
                        <h2>Weight Progress</h2>
                        <div class="chart-header-controls">
                            {% if date_filter.active %}
                                <span class="filter-badge">{{ date_filter.label }}</span>
                            {% endif %}
                            <div class="view-toggle">
                                <a href="{{ view_links.all }}" class="view-option {% if view_mode != 'monthly' %}active{% endif %}">All Entries</a>
                                <a href="{{ view_links.monthly }}" class="view-option {% if view_mode == 'monthly' %}active{% endif %}">Monthly Avg</a>
                            </div>
                        </div>
                    </div>
                    {% if view_mode == 'monthly' %}
                    <p class="chart-subtitle">One point per month, averaged from that month's entries.</p>
                    {% endif %}
                    {% if combined_labels %}
                        <canvas id="weightChart"></canvas>
                    {% elif date_filter.active %}
                        <p>No data in the selected date range.</p>
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
                                    <td>{{ '%.2f lbs'|format(summary_data.current) if summary_data.current is not none else 'N/A' }}</td>
                                </tr>
                                {% if summary_data.change_text %}
                                <tr class="{{ summary_data.change_class }}">
                                    <td>Since Last Entry</td>
                                    <td>{{ summary_data.change_text }}</td>
                                </tr>
                                {% endif %}
                                {% if summary_data.avg_recent_text %}
                                <tr>
                                    <td>Average (last {{ summary_data.avg_recent_n }})</td>
                                    <td>{{ summary_data.avg_recent_text }}</td>
                                </tr>
                                {% endif %}
                                {% if summary_data.range_change_text %}
                                <tr class="{{ summary_data.range_change_class }}">
                                    <td>Change ({{ summary_data.range_span_text }})</td>
                                    <td>{{ summary_data.range_change_text }}</td>
                                </tr>
                                {% endif %}
                                {% if summary_data.range_rate_text %}
                                <tr class="{{ summary_data.range_change_class }}">
                                    <td>Rate</td>
                                    <td>{{ summary_data.range_rate_text }}</td>
                                </tr>
                                {% endif %}
                                <tr>
                                    <td>Start Weight</td>
                                    <td>{{ '%.2f lbs'|format(summary_data.start) if summary_data.start is not none else 'N/A' }}</td>
                                </tr>
                                <tr>
                                    <td>Goal Weight</td>
                                    <td>{{ '%.2f lbs'|format(summary_data.goal) if summary_data.goal is not none else 'N/A' }}</td>
                                </tr>
                                <tr class="{{ summary_data.goal_class }}">
                                    <td>Weight to Goal</td>
                                    <td>{{ summary_data.to_goal if summary_data.to_goal is not none else 'N/A' }}</td>
                                </tr>
                                {% if summary_data.goal_eta %}
                                <tr>
                                    <td>Projected Goal Date<br><span class="optional-text">{{ summary_data.goal_eta_weeks }}</span></td>
                                    <td>{{ summary_data.goal_eta }}</td>
                                </tr>
                                {% endif %}
                                <tr>
                                    <td>Highest Weight</td>
                                    <td>{{ '%.2f lbs'|format(summary_data.highest) if summary_data.highest is not none else 'N/A' }}</td>
                                </tr>
                                <tr>
                                    <td>Lowest Weight</td>
                                    <td>{{ '%.2f lbs'|format(summary_data.lowest) if summary_data.lowest is not none else 'N/A' }}</td>
                                </tr>
                                {% if summary_data.bmi or summary_data.lean_mass %}
                                <tr class="summary-divider"><td colspan="2"></td></tr>
                                {% endif %}
                                {% if summary_data.bmi %}
                                <tr>
                                    <td>BMI</td>
                                    <td>{{ summary_data.bmi }} <span class="optional-text">({{ summary_data.bmi_category }})</span></td>
                                </tr>
                                {% endif %}
                                {% if summary_data.lean_mass %}
                                <tr>
                                    <td>Lean Mass</td>
                                    <td>{{ summary_data.lean_mass }}</td>
                                </tr>
                                <tr>
                                    <td>Fat Mass</td>
                                    <td>{{ summary_data.fat_mass }}</td>
                                </tr>
                                {% endif %}
                                {% if 'current_bf' in summary_data %}
                                <tr class="summary-divider"><td colspan="2"></td></tr>
                                <tr>
                                    <td>Current Body Fat</td>
                                    <td>{{ '%.2f%%'|format(summary_data.current_bf) }}</td>
                                </tr>
                                <tr>
                                    <td>Highest Body Fat</td>
                                    <td>{{ '%.2f%%'|format(summary_data.highest_bf) }}</td>
                                </tr>
                                <tr>
                                    <td>Lowest Body Fat</td>
                                    <td>{{ '%.2f%%'|format(summary_data.lowest_bf) }}</td>
                                </tr>
                                {% endif %}
                                {% if 'current_ws' in summary_data %}
                                <tr class="summary-divider"><td colspan="2"></td></tr>
                                <tr>
                                    <td>Current Waist Size</td>
                                    <td>{{ '%.2f in'|format(summary_data.current_ws) }}</td>
                                </tr>
                                <tr>
                                    <td>Highest Waist Size</td>
                                    <td>{{ '%.2f in'|format(summary_data.highest_ws) }}</td>
                                </tr>
                                <tr>
                                    <td>Lowest Waist Size</td>
                                    <td>{{ '%.2f in'|format(summary_data.lowest_ws) }}</td>
                                </tr>
                                {% endif %}
                            </tbody>
                        </table>
                    {% else %}
                        <p>No data for summary.</p>
                    {% endif %}
                </div>
            </div>
        </div>

        <div class="charts-grid">
            {% if body_fat_labels %}
            <div class="card">
                <h2>Body Fat % Progress</h2>
                <canvas id="bodyFatChart"></canvas>
            </div>
            {% endif %}

            {% if waist_size_labels %}
            <div class="card">
                <h2>Waist Size Progress (in)</h2>
                <canvas id="waistSizeChart"></canvas>
            </div>
            {% endif %}
        </div>

        {% if normalized_chart_data %}
        <div class="card normalized-chart-card">
            <h2>Normalized Weight Progress (%)</h2>
            <p class="chart-subtitle">Percentage of starting weight over time (100% = start weight)</p>
            <canvas id="normalizedChart"></canvas>
        </div>
        {% endif %}

    </div>

    <div id="editModal" class="modal">
        <div class="modal-content">
            <span class="close-button" onclick="closeEditModal()">&times;</span>
            <h2>Edit Entry</h2>
            <form id="editForm" method="post">
                <div class="form-group">
                    <label for="edit_date">Date:</label>
                    <input type="date" id="edit_date" name="date" required>
                </div>
                <div class="form-group">
                    <label for="edit_weight">Weight (lbs):</label>
                    <input type="number" id="edit_weight" name="weight" step="0.01" required>
                </div>
                <div class="form-group">
                    <label for="edit_body_fat">Body Fat (%): <span class="optional-text">(Optional)</span></label>
                    <input type="number" id="edit_body_fat" name="body_fat" step="0.01">
                </div>
                <div class="form-group">
                    <label for="edit_waist_size">Waist Size (in): <span class="optional-text">(Optional)</span></label>
                    <input type="number" id="edit_waist_size" name="waist_size" step="0.01">
                </div>
                <button type="submit" class="btn btn-primary">Save Changes</button>
            </form>
        </div>
    </div>

    <script>
        // --- Main Weight Chart ---
        {% if combined_labels and chart_data_1 %}
        const ctx = document.getElementById('weightChart').getContext('2d');
        const chart_config = {{ chart_config | tojson }};
        const datasets = [{
            label: '{{ primary_user }} Weight (lbs)',
            data: {{ chart_data_1 | tojson }},
            pointCounts: {{ chart_counts_1 | tojson }},
            borderColor: '#33CFFF',
            backgroundColor: 'rgba(51, 207, 255, 0.1)',
            yAxisID: 'y1',
            fill: true,
            tension: 0.1,
            spanGaps: true
        }];

        {% if comparison_user and chart_data_2_to_plot %}
        datasets.push({
            label: '{{ comparison_user }} Weight (lbs)',
            data: {{ chart_data_2_to_plot | tojson }},
            pointCounts: {{ chart_counts_2 | tojson }},
            borderColor: '#9D63FF',
            backgroundColor: 'rgba(157, 99, 255, 0.1)',
            yAxisID: 'y2',
            fill: true,
            tension: 0.1,
            spanGaps: true
        });
        {% endif %}

        const chartData = { labels: {{ combined_labels | tojson }}, datasets: datasets };
        const chartOptions = {
            responsive: true,
            interaction: { mode: 'index', intersect: false },
            scales: { y1: { type: 'linear', display: true, position: 'left', title: { display: true, text: '{{ primary_user }} Weight (lbs)', color: '#33CFFF'}}},
            plugins: { tooltip: { callbacks: { label: function(context) { let label = context.dataset.label || ''; if (label) { label += ': '; } if (context.parsed.y !== null) { label += context.parsed.y.toFixed(2) + ' lbs'; } const counts = context.dataset.pointCounts; if (counts && counts[context.dataIndex]) { label += ' (avg of ' + counts[context.dataIndex] + ')'; } return label; }}}, annotation: { annotations: {}}}
        };

        if (chart_config.y2_axis_label) {
            chartOptions.scales.y2 = { type: 'linear', display: true, position: 'right', title: { display: true, text: chart_config.y2_axis_label, color: '#9D63FF' }, grid: { drawOnChartArea: false }};
        }
        {% if primary_user_data.start_weight %}
        chartOptions.plugins.annotation.annotations.startLine1 = { type: 'line', yMin: {{ primary_user_data.start_weight }}, yMax: {{ primary_user_data.start_weight }}, yScaleID: 'y1', borderColor: '#33CFFF', borderWidth: 2, borderDash: [6, 6], label: { content: 'Start: {{ "%.2f"|format(primary_user_data.start_weight) }} lbs', display: {{ 'false' if comparison_user else 'true' }}, position: 'start', backgroundColor: 'rgba(51, 207, 255, 0.8)' }};
        {% endif %}
        {% if primary_user_data.goal_weight %}
        chartOptions.plugins.annotation.annotations.goalLine1 = { type: 'line', yMin: {{ primary_user_data.goal_weight }}, yMax: {{ primary_user_data.goal_weight }}, yScaleID: 'y1', borderColor: '#dc3545', borderWidth: 2, borderDash: [6, 6], label: { content: 'Goal: {{ "%.2f"|format(primary_user_data.goal_weight) }} lbs', display: {{ 'false' if comparison_user else 'true' }}, position: 'end', backgroundColor: 'rgba(220, 53, 69, 0.8)' }};
        {% endif %}

        if (chart_config.y1_min !== null && chart_config.y1_max !== null) { chartOptions.scales.y1.min = chart_config.y1_min; chartOptions.scales.y1.max = chart_config.y1_max; }
        if (chart_config.y2_axis_label && chart_config.y2_min !== null && chart_config.y2_max !== null) { chartOptions.scales.y2.min = chart_config.y2_min; chartOptions.scales.y2.max = chart_config.y2_max; }
        const weightChart = new Chart(ctx, { type: 'line', data: chartData, options: chartOptions });
        {% endif %}

        // --- Body Fat Chart ---
        {% if body_fat_labels %}
        const bf_ctx = document.getElementById('bodyFatChart').getContext('2d');
        new Chart(bf_ctx, {
            type: 'line',
            data: {
                labels: {{ body_fat_labels | tojson }},
                datasets: [{
                    label: 'Body Fat (%)',
                    data: {{ body_fat_data | tojson }},
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    fill: true,
                    tension: 0.1,
                    spanGaps: true
                }]
            },
            options: { responsive: true, scales: { y: { title: { display: true, text: 'Body Fat (%)' }}}, plugins: { legend: { display: false }}}
        });
        {% endif %}

        // --- Waist Size Chart ---
        {% if waist_size_labels %}
        const ws_ctx = document.getElementById('waistSizeChart').getContext('2d');
        new Chart(ws_ctx, {
            type: 'line',
            data: {
                labels: {{ waist_size_labels | tojson }},
                datasets: [{
                    label: 'Waist Size (in)',
                    data: {{ waist_size_data | tojson }},
                    borderColor: '#fd7e14',
                    backgroundColor: 'rgba(253, 126, 20, 0.1)',
                    fill: true,
                    tension: 0.1,
                    spanGaps: true
                }]
            },
            options: { responsive: true, scales: { y: { title: { display: true, text: 'Waist Size (in)' }}}, plugins: { legend: { display: false }}}
        });
        {% endif %}

        // --- Normalized Weight Chart ---
        {% if normalized_chart_data %}
        const norm_ctx = document.getElementById('normalizedChart').getContext('2d');
        const normalizedChartData = {{ normalized_chart_data | tojson }};
        const userColors = ['#33CFFF', '#9D63FF', '#28a745', '#fd7e14', '#e83e8c', '#20c997', '#6f42c1', '#17a2b8'];
        
        // Calculate min/max across ALL datasets for proper Y-axis scaling
        let allValues = [];
        normalizedChartData.datasets.forEach(ds => {
            ds.data.forEach(val => {
                if (val !== null && val !== undefined) {
                    allValues.push(val);
                }
            });
        });
        // Always include 100% baseline in the range
        allValues.push(100);
        const yMin = Math.floor(Math.min(...allValues) - 2);
        const yMax = Math.ceil(Math.max(...allValues) + 2);
        
        const normalizedDatasets = normalizedChartData.datasets.map((ds, idx) => ({
            label: ds.label,
            data: ds.data,
            borderColor: userColors[idx % userColors.length],
            backgroundColor: userColors[idx % userColors.length] + '20',
            fill: false,
            tension: 0.1,
            spanGaps: true,
            pointRadius: 4,
            pointHoverRadius: 6
        }));

        new Chart(norm_ctx, {
            type: 'line',
            data: {
                labels: normalizedChartData.labels,
                datasets: normalizedDatasets
            },
            options: {
                responsive: true,
                interaction: { mode: 'index', intersect: false },
                scales: {
                    y: {
                        min: yMin,
                        max: yMax,
                        title: { display: true, text: '% of Starting Weight' },
                        ticks: { callback: function(value) { return value + '%'; } }
                    }
                },
                plugins: {
                    legend: { display: true, position: 'top' },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + context.parsed.y.toFixed(2) + '%';
                            }
                        }
                    },
                    annotation: {
                        annotations: {
                            startLine: {
                                type: 'line',
                                yMin: 100,
                                yMax: 100,
                                borderColor: 'rgba(100, 100, 100, 0.5)',
                                borderWidth: 2,
                                borderDash: [6, 6],
                                label: {
                                    content: 'Start (100%)',
                                    display: true,
                                    position: 'start',
                                    backgroundColor: 'rgba(100, 100, 100, 0.8)'
                                }
                            }
                        }
                    }
                }
            }
        });
        {% endif %}

        // --- Date Range Presets ---
        // preset is a day count, 'ytd' for year-to-date, or 'all' to clear the filter.
        function setDateRange(preset) {
            const form = document.getElementById('dateFilterForm');
            const startEl = document.getElementById('start_date');
            const endEl = document.getElementById('end_date');
            if (preset === 'all') {
                startEl.value = '';
                endEl.value = '';
                form.submit();
                return;
            }
            const fmt = function(d) {
                return d.getFullYear() + '-' +
                    String(d.getMonth() + 1).padStart(2, '0') + '-' +
                    String(d.getDate()).padStart(2, '0');
            };
            const today = new Date();
            let start;
            if (preset === 'ytd') {
                start = new Date(today.getFullYear(), 0, 1);
            } else {
                start = new Date(today);
                start.setDate(start.getDate() - parseInt(preset, 10));
            }
            startEl.value = fmt(start);
            endEl.value = fmt(today);
            form.submit();
        }

        // --- Modal Control Functions ---
        function openEditModal(entry_id, date, weight, body_fat, waist_size) {
            const modal = document.getElementById('editModal');
            const form = document.getElementById('editForm');
            document.getElementById('edit_date').value = date;
            document.getElementById('edit_weight').value = weight;
            document.getElementById('edit_body_fat').value = body_fat;
            document.getElementById('edit_waist_size').value = waist_size;
            form.action = `/update/${entry_id}`;
            modal.style.display = 'block';
        }

        function closeEditModal() {
            document.getElementById('editModal').style.display = 'none';
        }

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
    max-width: 1200px;
    display: flex;
    flex-direction: column;
    gap: 20px;
}
h1, h2 {
    text-align: center;
}
h1 {
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
.user-actions .btn, .user-actions form:not(.add-user-form) .btn {
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
.optional-text {
    font-weight: 400;
    color: #777;
    font-size: 0.9em;
}
input[type="number"], input[type="text"], input[type="date"], select {
    width: 100%;
    padding: 12px;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    box-sizing: border-box;
    font-size: 1rem;
}
select { padding: 10px; background-color: white; }
.btn {
    padding: 12px 20px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 1rem;
    font-family: inherit;
    font-weight: 500;
    transition: all 0.2s ease-in-out;
    text-decoration: none;
    display: inline-block;
    text-align: center;
}
.inline-form {
    display: inline-block;
    margin: 0;
}
.btn:hover { opacity: 0.9; }
.btn-primary { background-color: var(--primary-color); color: white; }
.btn-primary:hover { transform: translateY(-2px); }
.btn-secondary { background-color: var(--secondary-color); color: white; }
.btn-sm { padding: 5px 10px; font-size: 0.875rem; }
.chart-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
.chart-header h2 { margin: 0; }
.goal-form .btn-secondary { width: 100%; }
.btn-danger { background-color: var(--danger-color); color: white; }
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
td { text-align: center; }
td:first-child { text-align: left; }
thead th { font-weight: 600; text-align: center; }
thead th:first-child { text-align: left; }
tbody tr:last-child td { border-bottom: none; }
.main-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    gap: 20px;
    align-items: start;
}
.left-column {
    display: flex;
    flex-direction: column;
    min-width: 0;
    gap: 20px;
}
.right-column {
    position: sticky;
    top: 20px;
    display: flex;
    flex-direction: column;
    gap: 20px;
}
.summary-table { margin-top: 0; }
.summary-table td { padding: 10px 0; }
.summary-table td:first-child { font-weight: 500; color: #555; text-align: left; }
.summary-table td:last-child { text-align: right; font-weight: 600; }
.summary-divider td { padding: 8px 0; border-bottom: 1px solid var(--border-color); }
.goal-positive { color: #155724; }
.goal-negative { color: #721c24; }
.charts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 20px;
}
.modal {
    display: none; position: fixed; z-index: 1000; left: 0; top: 0;
    width: 100%; height: 100%; overflow: auto; background-color: rgba(0,0,0,0.5);
}
.modal-content {
    background-color: #fefefe; margin: 10% auto; padding: 30px;
    border: 1px solid #888; width: 80%; max-width: 500px;
    border-radius: 12px; position: relative;
}
.close-button {
    color: #aaa; position: absolute; top: 10px; right: 20px;
    font-size: 28px; font-weight: bold; cursor: pointer;
}
.close-button:hover, .close-button:focus { color: black; text-decoration: none; }
.flash-messages { list-style: none; padding: 0; margin-bottom: 1rem; }
.flash { padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem; text-align: center; }
.flash.success { background-color: #d4edda; color: #155724; }
.flash.error { background-color: #f8d7da; color: #721c24; }
.checkbox-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
}
.checkbox-label {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background-color: var(--background-color);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
}
.checkbox-label:hover {
    border-color: var(--primary-color);
}
.checkbox-label input[type="checkbox"] {
    width: auto;
    cursor: pointer;
}
.checkbox-text {
    font-weight: 500;
}
.form-hint {
    color: #666;
    font-size: 0.9rem;
    margin-bottom: 12px;
}
.chart-subtitle {
    color: #666;
    font-size: 0.9rem;
    text-align: center;
    margin-top: -10px;
    margin-bottom: 15px;
}
.normalized-chart-card {
    margin-top: 20px;
}
.date-filter-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}
.date-filter-grid .form-group {
    margin-bottom: 15px;
}
.date-presets {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 15px;
}
.date-presets .btn {
    flex: 1 1 auto;
    min-width: 52px;
}
.btn-block {
    width: 100%;
}
.filter-note {
    margin-bottom: 0;
    margin-top: 12px;
    text-align: center;
}
.filter-badge {
    background-color: var(--primary-color);
    color: white;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 600;
    white-space: nowrap;
}
.chart-header-controls {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
}
.view-toggle {
    display: inline-flex;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    overflow: hidden;
}
.view-option {
    padding: 6px 14px;
    font-size: 0.85rem;
    font-weight: 500;
    color: #555;
    background-color: var(--background-color);
    text-decoration: none;
    white-space: nowrap;
    transition: all 0.2s ease-in-out;
}
.view-option + .view-option {
    border-left: 1px solid var(--border-color);
}
.view-option:hover {
    background-color: #e8eeed;
}
.view-option.active {
    background-color: var(--primary-color);
    color: white;
}
.view-option.active:hover {
    background-color: var(--primary-color);
}
"""

# Fixed column positions in the workbook. The ID column was added later, so it
# sits after the original five to keep existing files readable.
COL_DATE, COL_WEIGHT, COL_USER, COL_BODY_FAT, COL_WAIST, COL_ID = 1, 2, 3, 4, 5, 6
COL_USERNAME, COL_START_WEIGHT, COL_GOAL_WEIGHT, COL_HEIGHT = 1, 2, 3, 4

DATA_HEADERS = ["Date", "Weight (lbs)", "User", "Body Fat %", "Waist Size (in)", "ID"]
USER_HEADERS = ["Username", "Start Weight (lbs)", "Goal Weight (lbs)", "Height (in)"]


# 1. Setup: Create directories and files
def setup_environment():
    """Creates and validates necessary directories and files."""
    print("Validating application environment...")
    os.makedirs(STATIC_FOLDER, exist_ok=True)

    with open(CSS_FILE, 'w') as f:
        f.write(CSS_CONTENT)
    print(f"Ensured '{CSS_FILE}' is up to date.")

    if not os.path.exists(EXCEL_FILE):
        workbook = openpyxl.Workbook()
        sheet_data = workbook.active
        sheet_data.title = "Weight Data"
        sheet_data.append(DATA_HEADERS)
        sheet_users = workbook.create_sheet("Users")
        sheet_users.append(USER_HEADERS)
        sheet_users.append(["User 1", None, None, None])
        workbook.save(EXCEL_FILE)
        print(f"Created '{EXCEL_FILE}' with required sheets and headers.")
        return

    workbook = openpyxl.load_workbook(EXCEL_FILE)
    updated = False

    if "Users" not in workbook.sheetnames:
        workbook.create_sheet("Users").append(USER_HEADERS)
        updated = True
        print("Added missing 'Users' sheet.")
    if "Weight Data" not in workbook.sheetnames:
        workbook.create_sheet("Weight Data").append(DATA_HEADERS)
        updated = True
        print("Added missing 'Weight Data' sheet.")

    # Headers live at fixed column positions, so a missing one is written in
    # place rather than appended after whatever the last used column happens
    # to be.
    for sheet_name, headers in (("Weight Data", DATA_HEADERS), ("Users", USER_HEADERS)):
        sheet = workbook[sheet_name]
        for col, header in enumerate(headers, start=1):
            if sheet.cell(row=1, column=col).value != header:
                sheet.cell(row=1, column=col).value = header
                updated = True
                print(f"Set '{sheet_name}' column {col} header to '{header}'.")

    # Backfill stable IDs so edit/delete no longer address entries by their
    # Excel row number, which shifts whenever a row is inserted or removed.
    sheet_data = workbook["Weight Data"]
    used_ids = set()
    missing_id_rows = []
    for row in sheet_data.iter_rows(min_row=2):
        raw_id = row[COL_ID - 1].value
        try:
            entry_id = int(raw_id)
        except (ValueError, TypeError):
            entry_id = None
        if entry_id is None or entry_id in used_ids:
            missing_id_rows.append(row[COL_ID - 1])
        else:
            used_ids.add(entry_id)
    if missing_id_rows:
        next_id = max(used_ids) + 1 if used_ids else 1
        for cell in missing_id_rows:
            cell.value = next_id
            next_id += 1
        updated = True
        print(f"Assigned stable IDs to {len(missing_id_rows)} entr(ies).")

    if updated:
        workbook.save(EXCEL_FILE)

setup_environment()
app = Flask(__name__, static_folder=STATIC_FOLDER)
app.secret_key = 'a_secure_random_secret_key'

class WorkbookLocked(Exception):
    """weights.xlsx could not be written, usually because it is open in Excel."""

LOCKED_MESSAGE = "Could not save — weights.xlsx is open in another program (e.g., Excel). Close it and try again."

def save_workbook(workbook):
    try:
        workbook.save(EXCEL_FILE)
    except PermissionError:
        raise WorkbookLocked
    invalidate_cache()

ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def read_date_filter(source):
    """Pulls validated 'start_date'/'end_date' values off a request form or query string.

    Anything that is not a plain YYYY-MM-DD string is treated as "not set" so a
    hand-edited URL cannot break the page.
    """
    start = (source.get('start_date') or '').strip()
    end = (source.get('end_date') or '').strip()
    if not ISO_DATE_PATTERN.match(start): start = ''
    if not ISO_DATE_PATTERN.match(end): end = ''
    return start, end

def filter_entries_by_date(entries, start_date, end_date):
    """Restricts entries to the inclusive [start_date, end_date] window.

    Entry dates are normalized to ISO 'YYYY-MM-DD', so plain string comparison
    is chronological and no parsing is needed.
    """
    if start_date:
        entries = [e for e in entries if e['date'] >= start_date]
    if end_date:
        entries = [e for e in entries if e['date'] <= end_date]
    return entries

def build_date_filter(start_date, end_date, shown_count, total_count):
    """Bundles the filter state and its display strings for the template."""
    active = bool(start_date or end_date)
    if start_date and end_date:
        label = f"{start_date} to {end_date}"
    elif start_date:
        label = f"From {start_date}"
    elif end_date:
        label = f"Through {end_date}"
    else:
        label = "All dates"
    summary = (f"Showing {shown_count} of {total_count} entries."
               if active else f"Showing all {total_count} entries.")
    return {'start': start_date, 'end': end_date, 'active': active,
            'label': label, 'summary': summary}

def with_view_state(**args):
    """Adds the request's date filter and chart view mode to url_for() arguments."""
    source = request.form if request.method == 'POST' else request.args
    start, end = read_date_filter(source)
    if start: args['start_date'] = start
    if end: args['end_date'] = end
    if read_view_mode(source) == 'monthly': args['view'] = 'monthly'
    return args

def days_between(start_date, end_date):
    """Whole days between two ISO date strings, or None if either will not parse."""
    try:
        return (datetime.date.fromisoformat(end_date) - datetime.date.fromisoformat(start_date)).days
    except (ValueError, TypeError):
        return None

def read_view_mode(source):
    """'monthly' collapses the charts to one averaged point per calendar month."""
    return 'monthly' if (source.get('view') or '').strip() == 'monthly' else 'all'

def mean(values):
    """Average of the non-null values, or None when there are none."""
    numbers = [v for v in values if v is not None]
    return sum(numbers) / len(numbers) if numbers else None

def _rounded_mean(values):
    average = mean(values)
    return round(average, 2) if average is not None else None

def aggregate_monthly(entries):
    """Collapses entries into one averaged point per calendar month.

    The result keeps the shape of a raw entry so the charts can consume either
    form. 'date' holds the month key ('YYYY-MM') and 'count' records how many
    entries went into the average. Each metric averages only the entries that
    actually carry that measurement.
    """
    buckets = {}
    for entry in entries:
        buckets.setdefault(entry['date'][:7], []).append(entry)
    monthly = []
    for month in sorted(buckets):
        group = buckets[month]
        monthly.append({
            'date': month,
            'weight': _rounded_mean([e['weight'] for e in group]),
            'body_fat': _rounded_mean([e['body_fat'] for e in group]),
            'waist_size': _rounded_mean([e['waist_size'] for e in group]),
            'count': len(group),
        })
    return monthly

def chart_series(entries, view_mode):
    """Oldest-first points for the charts, averaged by month when asked."""
    ordered = sorted(entries, key=lambda e: e['date'])
    if view_mode == 'monthly':
        return [e for e in aggregate_monthly(ordered) if e['weight'] is not None]
    return [e for e in ordered if e.get('weight') is not None]

def bmi_for(weight_lbs, height_in):
    """Standard imperial BMI, or None without a usable height."""
    if not weight_lbs or not height_in or height_in <= 0:
        return None
    return 703.0 * weight_lbs / (height_in ** 2)

def bmi_category(bmi):
    """Conventional adult BMI bracket for a computed BMI."""
    if bmi is None:
        return None
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Overweight"
    return "Obese"

def body_composition(weight, body_fat_pct):
    """Splits a weight into (lean, fat) mass in lbs, or (None, None)."""
    if weight is None or body_fat_pct is None:
        return None, None
    fat_mass = weight * body_fat_pct / 100.0
    return weight - fat_mass, fat_mass

# --- Workbook cache ---------------------------------------------------------
# Rendering the page used to reload and re-parse weights.xlsx once per user per
# metric. The whole file is now parsed once and reused until it changes on disk,
# so an ordinary page load costs a single read instead of a dozen.
_CACHE_LOCK = threading.Lock()
_cache = {"stamp": None, "users": [], "user_data": {}, "rows": []}

def _workbook_stamp():
    """Cheap change detector: modification time plus size."""
    try:
        stat = os.stat(EXCEL_FILE)
        return (stat.st_mtime_ns, stat.st_size)
    except OSError:
        return None

def invalidate_cache():
    """Forces the next read to re-parse the workbook."""
    with _CACHE_LOCK:
        _cache["stamp"] = None

def _to_float(value):
    """Best-effort float conversion; blanks and junk become None."""
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def _cell(row, column):
    """Reads a 1-based column out of a values_only row tuple, tolerating short rows."""
    index = column - 1
    return row[index] if len(row) > index else None

def _parse_workbook():
    """Parses the entire workbook into plain Python structures."""
    users, user_data, rows = [], {}, []
    try:
        workbook = openpyxl.load_workbook(EXCEL_FILE, read_only=True, data_only=True)
    except FileNotFoundError:
        return users, user_data, rows
    try:
        if "Users" in workbook.sheetnames:
            for row in workbook["Users"].iter_rows(min_row=2, values_only=True):
                name = _cell(row, COL_USERNAME)
                if not name:
                    continue
                users.append(name)
                user_data[name] = {
                    "start_weight": _to_float(_cell(row, COL_START_WEIGHT)),
                    "goal_weight": _to_float(_cell(row, COL_GOAL_WEIGHT)),
                    "height": _to_float(_cell(row, COL_HEIGHT)),
                }
        if "Weight Data" in workbook.sheetnames:
            for row in workbook["Weight Data"].iter_rows(min_row=2, values_only=True):
                date_val, weight_val = _cell(row, COL_DATE), _cell(row, COL_WEIGHT)
                user = _cell(row, COL_USER)
                if date_val is None or weight_val is None or not user:
                    continue
                weight = _to_float(weight_val)
                if weight is None:
                    continue
                try:
                    entry_id = int(_cell(row, COL_ID))
                except (ValueError, TypeError):
                    entry_id = None
                normalized_date = (date_val.strftime("%Y-%m-%d")
                                   if isinstance(date_val, datetime.datetime)
                                   else str(date_val).split(' ')[0])
                rows.append({
                    "id": entry_id,
                    "user": user,
                    "date": normalized_date,
                    "weight": weight,
                    "body_fat": _to_float(_cell(row, COL_BODY_FAT)),
                    "waist_size": _to_float(_cell(row, COL_WAIST)),
                })
    finally:
        workbook.close()
    return users, user_data, rows

def get_workbook_data():
    """Returns (users, user_data, rows), re-parsing only when the file changed."""
    stamp = _workbook_stamp()
    with _CACHE_LOCK:
        if _cache["stamp"] is not None and _cache["stamp"] == stamp:
            return _cache["users"], _cache["user_data"], _cache["rows"]
    users, user_data, rows = _parse_workbook()
    with _CACHE_LOCK:
        _cache.update({"stamp": stamp, "users": users, "user_data": user_data, "rows": rows})
    return users, user_data, rows

def get_users():
    """Reads the list of users from the 'Users' sheet."""
    users, _, _ = get_workbook_data()
    return users or ["User 1"]

def get_user_data(user):
    """Reads start weight, goal weight and height for a specific user."""
    _, user_data, _ = get_workbook_data()
    record = user_data.get(user)
    if not record:
        return {"start_weight": None, "goal_weight": None, "height": None}
    return dict(record)

def get_weight_entries(active_user):
    """Reads all entries for a specific user, newest first."""
    _, _, rows = get_workbook_data()
    entries = [{"id": r["id"], "date": r["date"], "weight": r["weight"],
                "body_fat": r["body_fat"], "waist_size": r["waist_size"]}
               for r in rows if r["user"] == active_user]
    return sorted(entries, key=lambda x: x['date'], reverse=True)

def find_entry_row(sheet, entry_id):
    """Finds the Excel row holding a given entry ID, or None."""
    for row in sheet.iter_rows(min_row=2):
        cell = row[COL_ID - 1]
        try:
            if int(cell.value) == entry_id:
                return cell.row
        except (ValueError, TypeError):
            continue
    return None

def next_entry_id(sheet):
    """Returns one past the highest ID currently in the sheet."""
    highest = 0
    for row in sheet.iter_rows(min_row=2, values_only=True):
        try:
            highest = max(highest, int(_cell(row, COL_ID)))
        except (ValueError, TypeError):
            continue
    return highest + 1

def add_weight_entry(date_str, weight, user, body_fat, waist_size):
    """Adds a new entry to the Excel file."""
    workbook = openpyxl.load_workbook(EXCEL_FILE)
    sheet = workbook["Weight Data"]
    sheet.append([date_str, weight, user, body_fat, waist_size, next_entry_id(sheet)])
    save_workbook(workbook)

def update_weight_entry(entry_id, new_date, new_weight, new_body_fat, new_waist_size):
    """Updates an existing entry by its stable ID."""
    workbook = openpyxl.load_workbook(EXCEL_FILE)
    sheet = workbook["Weight Data"]
    row_index = find_entry_row(sheet, entry_id)
    if row_index is None:
        return False
    sheet.cell(row=row_index, column=COL_DATE).value = new_date
    sheet.cell(row=row_index, column=COL_WEIGHT).value = new_weight
    sheet.cell(row=row_index, column=COL_BODY_FAT).value = new_body_fat
    sheet.cell(row=row_index, column=COL_WAIST).value = new_waist_size
    save_workbook(workbook)
    return True

def delete_weight_entry(entry_id):
    """Deletes an entry by its stable ID."""
    workbook = openpyxl.load_workbook(EXCEL_FILE)
    sheet = workbook["Weight Data"]
    row_index = find_entry_row(sheet, entry_id)
    if row_index is None:
        return False
    sheet.delete_rows(row_index)
    save_workbook(workbook)
    return True

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user, date_str = request.form.get('user'), request.form.get('date')
        try:
            weight = float(request.form['weight'])
            body_fat = float(s) if (s := request.form.get('body_fat')) else None
            waist_size = float(s) if (s := request.form.get('waist_size')) else None
            if weight > 0 and date_str:
                add_weight_entry(date_str, weight, user, body_fat, waist_size)
                flash('Entry added successfully!', 'success')
            else:
                flash('Weight must be a positive number.', 'error')
        except (ValueError, TypeError):
            flash('Invalid input. Please enter valid numbers.', 'error')
        except WorkbookLocked:
            flash(LOCKED_MESSAGE, 'error')
        return redirect(url_for('index', **with_view_state(user1=user)))

    all_users = get_users()
    if not all_users:
        return render_template_string(HTML_CONTENT, all_users=[], primary_user=None, entries=[],
                                      primary_user_data={}, selected_compare_users=[], view_mode='all',
                                      date_filter=build_date_filter('', '', 0, 0))

    primary_user = request.args.get('user1', all_users[0])
    comparison_user = request.args.get('user2')
    filter_start, filter_end = read_date_filter(request.args)
    view_mode = read_view_mode(request.args)
    all_entries = get_weight_entries(primary_user)
    entries = filter_entries_by_date(all_entries, filter_start, filter_end)
    date_filter = build_date_filter(filter_start, filter_end, len(entries), len(all_entries))
    primary_user_data = get_user_data(primary_user)
    comparison_user_data = get_user_data(comparison_user) if comparison_user else {}
    today_date = datetime.datetime.now().strftime("%Y-%m-%d")

    # --- Weight Chart Data ---
    # entries1 stays raw (oldest-first) and backs the summary stats. series1 is
    # what the charts plot: the same points in "all" view, or one averaged point
    # per calendar month in "monthly" view.
    entries1 = sorted([e for e in entries if e.get('weight') is not None], key=lambda x: x['date'])
    series1 = chart_series(entries, view_mode)
    data1_map = {e['date']: e['weight'] for e in series1}
    y1_values = list(data1_map.values())
    # With a filter active the axis tracks only the visible data, so a distant
    # start or goal weight cannot flatten the stretch you zoomed in on.
    if not date_filter['active']:
        if primary_user_data.get('start_weight') is not None: y1_values.append(primary_user_data['start_weight'])
        if primary_user_data.get('goal_weight') is not None: y1_values.append(primary_user_data['goal_weight'])
    y1_min, y1_max = (None, None)
    if y1_values:
        padding = 5
        y1_min, y1_max = min(y1_values) - padding, max(y1_values) + padding
    chart_config = {"y1_min": y1_min, "y1_max": y1_max, "y2_axis_label": None, "y2_min": None, "y2_max": None}
    combined_labels, chart_data_1, chart_data_2_to_plot = [], [], []

    if comparison_user:
        series2 = chart_series(
            filter_entries_by_date(get_weight_entries(comparison_user), filter_start, filter_end), view_mode)
        data2_map = {e['date']: e['weight'] for e in series2}
        combined_labels = sorted(list(set(data1_map.keys()) | set(data2_map.keys())))
        chart_data_1 = [data1_map.get(date) for date in combined_labels]
        chart_data_2_to_plot = [data2_map.get(date) for date in combined_labels]
        chart_config["y2_axis_label"] = f"{comparison_user} Weight (lbs)"

        # --- Aligned Y-Axis Scaling ---
        # Map the primary axis onto the comparison axis with the linear
        # transform that puts both users' start weights at the same height
        # and both goal weights at the same height, then widen the shared
        # window until the comparison user's data fits inside it too.
        p_start = primary_user_data.get('start_weight')
        p_goal = primary_user_data.get('goal_weight')
        c_start = comparison_user_data.get('start_weight')
        c_goal = comparison_user_data.get('goal_weight')

        y2_values = [v for v in chart_data_2_to_plot if v is not None]
        if c_start is not None: y2_values.append(c_start)
        if c_goal is not None: y2_values.append(c_goal)

        # Alignment only works when both users have start/goal weights and
        # both are trending the same direction (scale > 0).
        scale = None
        if (y1_max is not None and p_start and p_goal and c_start and c_goal
                and p_start != p_goal):
            scale = (c_start - c_goal) / (p_start - p_goal)

        if scale is not None and scale > 0 and y2_values:
            def to_y2(v): return c_goal + (v - p_goal) * scale
            def to_y1(v): return p_goal + (v - c_goal) / scale
            padding = 5
            y1_min = min(y1_min, to_y1(min(y2_values) - padding))
            y1_max = max(y1_max, to_y1(max(y2_values) + padding))
            chart_config['y1_min'], chart_config['y1_max'] = y1_min, y1_max
            chart_config['y2_min'], chart_config['y2_max'] = to_y2(y1_min), to_y2(y1_max)
        elif y2_values:
            padding = 5
            chart_config['y2_min'], chart_config['y2_max'] = min(y2_values) - padding, max(y2_values) + padding
    else:
        combined_labels, chart_data_1 = [e['date'] for e in series1], [e['weight'] for e in series1]


    # --- Summary Data ---
    summary_data = {'current': None, 'highest': None, 'lowest': None}
    if entries:
        all_weights = [e['weight'] for e in entries]
        summary_data.update({'current': all_weights[0], 'highest': max(all_weights), 'lowest': min(all_weights)})
    summary_data.update({'start': primary_user_data.get('start_weight'), 'goal': primary_user_data.get('goal_weight')})
    if summary_data.get('current') and summary_data.get('goal'):
        to_goal = summary_data['current'] - summary_data['goal']
        if to_goal > 0.05: summary_data.update({'to_goal': f"{to_goal:.2f} lbs to lose", 'goal_class': 'goal-negative'})
        elif to_goal < -0.05: summary_data.update({'to_goal': f"{-to_goal:.2f} lbs below goal", 'goal_class': 'goal-positive'})
        else: summary_data.update({'to_goal': "Goal reached!", 'goal_class': 'goal-positive'})

    # --- Trend Indicators ---
    # entries is sorted newest-first, entries1 oldest-first.
    if len(entries) >= 2:
        change = entries[0]['weight'] - entries[1]['weight']
        summary_data['change_text'] = f"{change:+.2f} lbs"
        summary_data['change_class'] = ''
        goal = summary_data.get('goal')
        if goal is not None and abs(change) > 0.005:
            toward_goal = abs(entries[0]['weight'] - goal) < abs(entries[1]['weight'] - goal)
            summary_data['change_class'] = 'goal-positive' if toward_goal else 'goal-negative'
        recent = entries[:4]
        summary_data['avg_recent_n'] = len(recent)
        summary_data['avg_recent_text'] = f"{sum(e['weight'] for e in recent) / len(recent):.2f} lbs"

    # --- Change Across the Displayed Range ---
    # entries1 is oldest-first and already restricted to the active date filter.
    if len(entries1) >= 2:
        span_change = entries1[-1]['weight'] - entries1[0]['weight']
        days = days_between(entries1[0]['date'], entries1[-1]['date'])
        summary_data['range_change_text'] = f"{span_change:+.2f} lbs"
        summary_data['range_span_text'] = f"{days} days" if days else "range"
        summary_data['range_change_class'] = ''
        goal = summary_data.get('goal')
        if goal is not None and abs(span_change) > 0.005:
            toward_goal = abs(entries1[-1]['weight'] - goal) < abs(entries1[0]['weight'] - goal)
            summary_data['range_change_class'] = 'goal-positive' if toward_goal else 'goal-negative'
        if days:
            summary_data['range_rate_text'] = f"{span_change / days * 7:+.2f} lbs/week"

    # --- BMI & Body Composition ---
    height = primary_user_data.get('height')
    current_weight = summary_data.get('current')
    current_bmi = bmi_for(current_weight, height)
    if current_bmi is not None:
        summary_data['bmi'] = f"{current_bmi:.1f}"
        summary_data['bmi_category'] = bmi_category(current_bmi)
    latest_bf = next((e for e in entries if e.get('body_fat') is not None), None)
    if latest_bf:
        lean_mass, fat_mass = body_composition(latest_bf['weight'], latest_bf['body_fat'])
        summary_data['lean_mass'] = f"{lean_mass:.2f} lbs"
        summary_data['fat_mass'] = f"{fat_mass:.2f} lbs"

    # --- Goal Projection ---
    # Extrapolates the rate measured across the displayed range. Shown only when
    # that rate actually moves toward the goal and lands within about a decade,
    # so a flat or wrong-direction stretch does not produce a nonsense date.
    goal = summary_data.get('goal')
    if goal is not None and current_weight is not None and len(entries1) >= 2:
        rate_days = days_between(entries1[0]['date'], entries1[-1]['date'])
        remaining = goal - current_weight
        if rate_days and abs(remaining) > 0.05:
            weekly_rate = (entries1[-1]['weight'] - entries1[0]['weight']) / rate_days * 7
            if abs(weekly_rate) > 0.01 and remaining * weekly_rate > 0:
                weeks_out = remaining / weekly_rate
                if 0 < weeks_out <= 520:
                    try:
                        eta = (datetime.date.fromisoformat(entries1[-1]['date'])
                               + datetime.timedelta(weeks=weeks_out))
                        summary_data['goal_eta'] = eta.strftime("%b %d, %Y")
                        summary_data['goal_eta_weeks'] = f"~{weeks_out:.0f} weeks at this pace"
                    except (ValueError, TypeError, OverflowError):
                        pass

    # --- Optional Charts & Summary Stats ---
    # Stats read the raw entries (entries is newest-first); the charts follow the
    # active view mode so every chart on the page smooths together.
    body_fat_entries = [e for e in entries if e.get('body_fat') is not None]
    body_fat_points = [e for e in series1 if e.get('body_fat') is not None]
    body_fat_labels = [e['date'] for e in body_fat_points]
    body_fat_data = [e['body_fat'] for e in body_fat_points]
    if body_fat_entries:
        all_bf = [e['body_fat'] for e in body_fat_entries]
        summary_data.update({'current_bf': body_fat_entries[0]['body_fat'], 'highest_bf': max(all_bf), 'lowest_bf': min(all_bf)})

    waist_size_entries = [e for e in entries if e.get('waist_size') is not None]
    waist_points = [e for e in series1 if e.get('waist_size') is not None]
    waist_size_labels = [e['date'] for e in waist_points]
    waist_size_data = [e['waist_size'] for e in waist_points]
    if waist_size_entries:
        all_ws = [e['waist_size'] for e in waist_size_entries]
        summary_data.update({'current_ws': waist_size_entries[0]['waist_size'], 'highest_ws': max(all_ws), 'lowest_ws': min(all_ws)})

    # --- Multi-User Normalized Chart Data ---
    selected_compare_users = request.args.getlist('compare_users')
    normalized_chart_data = None
    
    if selected_compare_users:
        # Build normalized data for each selected user
        all_dates = set()
        user_normalized_data = {}
        
        for user in selected_compare_users:
            user_data = get_user_data(user)
            start_weight = user_data.get('start_weight')
            
            if not start_weight or start_weight <= 0:
                continue  # Skip users without valid start weight
            
            user_entries = chart_series(
                filter_entries_by_date(get_weight_entries(user), filter_start, filter_end), view_mode)
            if not user_entries:
                continue  # Skip users with no entries
            
            # Calculate normalized weight for each entry
            normalized_map = {}
            for entry in user_entries:
                if entry.get('weight'):
                    normalized_pct = (entry['weight'] / start_weight) * 100
                    normalized_map[entry['date']] = round(normalized_pct, 2)
                    all_dates.add(entry['date'])
            
            if normalized_map:
                user_normalized_data[user] = normalized_map
        
        # Build chart data structure if we have data
        if user_normalized_data:
            sorted_dates = sorted(list(all_dates))
            datasets = []
            
            for user, norm_map in user_normalized_data.items():
                data_points = [norm_map.get(date) for date in sorted_dates]
                datasets.append({
                    'label': user,
                    'data': data_points
                })
            
            normalized_chart_data = {
                'labels': sorted_dates,
                'datasets': datasets
            }

    # Links that carry the current users and date filter across the view toggle
    # and into the CSV export.
    link_args = {'user1': primary_user}
    if comparison_user: link_args['user2'] = comparison_user
    if filter_start: link_args['start_date'] = filter_start
    if filter_end: link_args['end_date'] = filter_end
    export_url = url_for('export_csv', **link_args)
    if selected_compare_users: link_args['compare_users'] = selected_compare_users
    view_links = {'all': url_for('index', **link_args),
                  'monthly': url_for('index', view='monthly', **link_args)}

    # Point counts let the tooltip say how many entries a monthly average covers.
    counts1 = {e['date']: e.get('count') for e in series1}
    chart_counts_1 = [counts1.get(d) for d in combined_labels]
    chart_counts_2 = []
    if comparison_user and chart_data_2_to_plot:
        counts2 = {e['date']: e.get('count') for e in series2}
        chart_counts_2 = [counts2.get(d) for d in combined_labels]

    return render_template_string(
        HTML_CONTENT, entries=entries, primary_user=primary_user, comparison_user=comparison_user,
        all_users=all_users, primary_user_data=primary_user_data, comparison_user_data=comparison_user_data,
        combined_labels=combined_labels, chart_data_1=chart_data_1, chart_data_2_to_plot=chart_data_2_to_plot,
        chart_config=chart_config, today_date=today_date, summary_data=summary_data,
        body_fat_labels=body_fat_labels, body_fat_data=body_fat_data,
        waist_size_labels=waist_size_labels, waist_size_data=waist_size_data,
        date_filter=date_filter, view_mode=view_mode, view_links=view_links, export_url=export_url,
        chart_counts_1=chart_counts_1, chart_counts_2=chart_counts_2,
        selected_compare_users=selected_compare_users, normalized_chart_data=normalized_chart_data
    )

@app.route('/update_goals', methods=['POST'])
def update_goals():
    user = request.form.get('user')
    if not user:
        flash("No user selected.", "error")
        return redirect(url_for('index'))
    try:
        start_weight_val = float(s) if (s := request.form.get('start_weight')) else None
        goal_weight_val = float(s) if (s := request.form.get('goal_weight')) else None
        height_val = float(s) if (s := request.form.get('height')) else None
        workbook = openpyxl.load_workbook(EXCEL_FILE)
        sheet = workbook["Users"]
        user_found = False
        for row in sheet.iter_rows(min_row=2):
            if row[COL_USERNAME - 1].value == user:
                sheet.cell(row=row[0].row, column=COL_START_WEIGHT).value = start_weight_val
                sheet.cell(row=row[0].row, column=COL_GOAL_WEIGHT).value = goal_weight_val
                sheet.cell(row=row[0].row, column=COL_HEIGHT).value = height_val
                user_found = True
                break
        if user_found:
            save_workbook(workbook)
            flash(f"Goals for {user} updated successfully!", "success")
        else:
            flash(f"Could not find user {user} to update.", "error")
    except ValueError: flash("Invalid input for weights.", "error")
    except WorkbookLocked: flash(LOCKED_MESSAGE, "error")
    except Exception as e: flash(f"An error occurred: {e}", "error")
    return redirect(url_for('index', **with_view_state(user1=user)))

@app.route('/add_user', methods=['POST'])
def add_user():
    new_user_name = request.form.get('new_user_name', '').strip()
    if not new_user_name:
        flash("User name cannot be empty.", "error")
        return redirect(url_for('index'))
    if new_user_name in get_users():
        flash(f"User '{new_user_name}' already exists.", "error")
        return redirect(url_for('index'))
    workbook = openpyxl.load_workbook(EXCEL_FILE)
    sheet = workbook["Users"]
    sheet.append([new_user_name, None, None, None])
    try:
        save_workbook(workbook)
    except WorkbookLocked:
        flash(LOCKED_MESSAGE, "error")
        return redirect(url_for('index'))
    flash(f"User '{new_user_name}' added successfully!", "success")
    return redirect(url_for('index', user1=new_user_name))

@app.route('/update/<int:entry_id>', methods=['POST'])
def update_entry(entry_id):
    new_date = request.form.get('date')
    try:
        new_weight = float(request.form.get('weight'))
        new_body_fat = float(s) if (s := request.form.get('body_fat')) else None
        new_waist_size = float(s) if (s := request.form.get('waist_size')) else None
        if new_weight > 0 and new_date:
            if update_weight_entry(entry_id, new_date, new_weight, new_body_fat, new_waist_size):
                flash('Entry updated successfully!', 'success')
            else:
                flash('Could not find entry to update. It may have been removed.', 'error')
        else:
            flash('Invalid weight or date.', 'error')
    except (ValueError, TypeError):
        flash('Invalid input for weight.', 'error')
    except WorkbookLocked:
        flash(LOCKED_MESSAGE, 'error')
    return redirect(request.referrer or url_for('index'))

@app.route('/delete/<int:entry_id>', methods=['POST'])
def delete_entry(entry_id):
    try:
        if delete_weight_entry(entry_id):
            flash('Entry deleted successfully!', 'success')
        else:
            flash('Could not find the entry to delete. It may have been removed.', 'error')
    except WorkbookLocked:
        flash(LOCKED_MESSAGE, 'error')
    except Exception as e:
        flash(f'An error occurred: {e}', 'error')
    return redirect(request.referrer or url_for('index'))

@app.route('/export.csv')
def export_csv():
    """Downloads the primary user's entries for the active date range."""
    users = get_users()
    user = request.args.get('user1') or (users[0] if users else '')
    filter_start, filter_end = read_date_filter(request.args)
    entries = filter_entries_by_date(get_weight_entries(user), filter_start, filter_end)
    height = get_user_data(user).get('height')

    def fmt(value):
        return f"{value:.2f}" if value is not None else ''

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Date", "Weight (lbs)", "Body Fat %", "Waist Size (in)",
                     "BMI", "Lean Mass (lbs)", "Fat Mass (lbs)"])
    for entry in sorted(entries, key=lambda e: e['date']):
        lean_mass, fat_mass = body_composition(entry['weight'], entry['body_fat'])
        writer.writerow([entry['date'], fmt(entry['weight']), fmt(entry['body_fat']),
                         fmt(entry['waist_size']), fmt(bmi_for(entry['weight'], height)),
                         fmt(lean_mass), fmt(fat_mass)])

    slug = re.sub(r'[^A-Za-z0-9_-]+', '_', user).strip('_') or 'user'
    span = f"_{filter_start or 'start'}_to_{filter_end or 'latest'}" if (filter_start or filter_end) else ''
    # The BOM makes Excel open the file as UTF-8 instead of the system codepage.
    return Response('\ufeff' + buffer.getvalue(), content_type='text/csv; charset=utf-8',
                    headers={'Content-Disposition': f'attachment; filename="weights_{slug}{span}.csv"'})

@app.route('/delete_user', methods=['POST'])
def delete_user():
    user_to_delete = request.form.get('user')
    if len(get_users()) <= 1:
        flash("Cannot delete the last user.", "error")
        return redirect(url_for('index', user1=user_to_delete))
    try:
        workbook = openpyxl.load_workbook(EXCEL_FILE)
        for sheet_name in ["Weight Data", "Users"]:
            sheet = workbook[sheet_name]
            col_idx = 3 if sheet_name == "Weight Data" else 1
            rows_to_delete = [r.row for r in sheet.iter_rows(min_row=2) if r[col_idx - 1].value == user_to_delete]
            for r_idx in sorted(rows_to_delete, reverse=True):
                sheet.delete_rows(r_idx)
        save_workbook(workbook)
        flash(f"User '{user_to_delete}' and all data have been deleted.", "success")
    except WorkbookLocked:
        flash(LOCKED_MESSAGE, "error")
        return redirect(url_for('index', user1=user_to_delete))
    except Exception as e:
        flash(f"An error occurred: {e}", "error")
        return redirect(url_for('index', user1=user_to_delete))
    return redirect(url_for('index'))

if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        print("\n--- Starting Flask Server ---")
        print("Open your web browser and go to: http://127.0.0.1:5020")
    app.run(host='0.0.0.0', port=5020, debug=True)


