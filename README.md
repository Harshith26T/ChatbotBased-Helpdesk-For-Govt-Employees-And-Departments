# ChatbotBased-Helpdesk-For-Govt-Employees-And-Departments
This project is built to provide a structured and modular application environment with a clean separation between backend logic, user interface components, and utility scripts. The application is driven by app.py, which serves as the main entry point and coordinates rendering of templates, handling requests, and managing backend processes.

The templates directory contains the HTML files responsible for the UI layout, while the static folder stores all required frontend assets such as CSS, JavaScript, and images. Additional functionality, background tasks, or processing workflows are organized within the Scripts directory to keep the core application lightweight and maintainable.

This structure ensures easy scalability, clear organization, and adaptability as the project grows in complexity. It also allows developers to update UI elements, backend logic, or standalone scripts independently without affecting other components of the system.

# Structure
Scripts/        Utility and backend scripts
static/         Frontend assets (CSS, JS, images)
templates/      HTML templates
app.py          Application entry point
pyvenv.cfg      Virtual environment configuration
README.md       Project documentation

# Setup
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux
