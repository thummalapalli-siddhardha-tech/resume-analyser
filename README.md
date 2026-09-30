# AI Career Guide & Resume Builder

## Project Objective
This project helps students, fresh graduates, and job seekers create an actionable 30-day learning roadmap for a target job role and analyze their resume for ATS compatibility, missing skills, certifications, and job opportunities.

## Features
- AI-powered career guidance
- Personalized 30-day learning plans
- Skill-gap analysis for target job roles
- Resume upload and ATS compatibility analysis
- Role-specific improvement suggestions
- Certification and paid-course recommendations
- Job portal search recommendations
- Responsive dark-themed interface

## Technology Stack
- Python
- Flask
- HTML5
- CSS3
- JavaScript
- JSON for structured data
- Google Gemini API (optional, configured via `.env`)
- PyPDF2 and python-docx for resume parsing

## Project Architecture
- `app.py`: Flask application entry point
- `data/`: JSON datasets for job roles, learning resources, certifications, paid courses, and portals
- `templates/`: HTML pages for the application UI
- `static/css/style.css`: styling for the dark modern design
- `static/js/script.js`: front-end interactions
- `uploads/`: temporary storage for uploaded resumes

## Installation
1. Open a terminal in the project folder.
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Gemini API Configuration
1. Create a Google AI Studio account.
2. Generate an API key.
3. Open the `.env` file and replace the placeholder:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
4. Keep the key in `.env` only. Do not expose it in the frontend.

## Run the Application
```bash
python app.py
```
The app will run at:
```text
http://localhost:5000
```

## How to Use Career Guide
1. Go to the AI Career Guide page.
2. Enter your name, target role, current skills, and time available per day.
3. Click Generate My Career Plan.
4. Review the AI-based skill gap analysis and 30-day roadmap.

## How to Use Resume Analyzer
1. Go to the Resume Analyzer page.
2. Upload a PDF or DOCX resume.
3. Select the target job role.
4. Click Analyze Resume.
5. Review the ATS estimate, strengths, missing skills, keywords, and improvement suggestions.

## Project Structure
```text
AI-Career-Guide-Resume-Builder/
├── app.py
├── requirements.txt
├── .env
├── .gitignore
├── README.md
├── data/
│   ├── career_roles.json
│   ├── learning_resources.json
│   ├── certifications.json
│   ├── paid_courses.json
│   └── job_portals.json
├── templates/
│   ├── index.html
│   ├── career-guide.html
│   ├── career-result.html
│   ├── resume-analyzer.html
│   ├── resume-result.html
│   └── about.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
├── uploads/
└── .venv/
```

## Security Considerations
- API keys are stored only in `.env`.
- Uploaded resumes are stored temporarily in the `uploads/` folder.
- File type validation restricts uploads to PDF and DOCX only.
- File size is limited to 5 MB.
- Resume files are not executed; they are parsed as text only.
- Input is sanitized before use.

## Notes
- ATS scores are AI-generated estimates for guidance.
- Actual ATS results depend on the employer, the job description, and the scanning software.
- Certification and course information should be verified on official provider websites before purchasing or applying.
