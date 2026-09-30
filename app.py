import json
import os
import re
import uuid
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None

try:
    from docx import Document
except ImportError:  # pragma: no cover
    Document = None

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover
    genai = None

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = str(BASE_DIR / "uploads")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "career-guide-demo")

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
ALLOWED_EXTENSIONS = {"pdf", "docx"}

if not os.path.exists(BASE_DIR / "uploads"):
    (BASE_DIR / "uploads").mkdir(exist_ok=True)


def load_json_file(filename):
    path = BASE_DIR / "data" / filename
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


CAREER_ROLES = load_json_file("career_roles.json")
LEARNING_RESOURCES = load_json_file("learning_resources.json")
CERTIFICATIONS = load_json_file("certifications.json")
PAID_COURSES = load_json_file("paid_courses.json")
JOB_PORTALS = load_json_file("job_portals.json")


def normalize_skill(value):
    if value is None:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def parse_skill_input(raw_value):
    if not raw_value:
        return []
    skills = []
    for chunk in re.split(r"[,\n]+", raw_value):
        skill = normalize_skill(chunk)
        if skill and skill not in skills:
            skills.append(skill)
    return skills


def get_role_data(role_name):
    for role in CAREER_ROLES:
        if normalize_skill(role.get("Role")) == normalize_skill(role_name):
            return role
    return {
        "Role": role_name,
        "required_skills": [
            "Python",
            "SQL",
            "Problem Solving",
            "Git/GitHub",
            "Communication",
            "Project Work"
        ],
        "optional_skills": [],
        "tools": [],
        "common_certifications": [],
        "learning_areas": []
    }


def get_gemini_response(prompt):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or genai is None:
        return None
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text if getattr(response, "text", None) else str(response)
    except Exception:
        return None


def find_missing_skills(current_skills, required_skills):
    current_norm = {normalize_skill(skill) for skill in current_skills}
    missing = []
    for skill in required_skills:
        if normalize_skill(skill) not in current_norm:
            missing.append(skill)
    return missing


def skill_search_keywords(skill):
    return [normalize_skill(skill), normalize_skill(skill).replace(" ", "")]


def get_resources_for_topics(topics, limit=3):
    results = []
    seen = set()
    for topic in topics:
        for resource in LEARNING_RESOURCES:
            topic_norm = normalize_skill(resource.get("Topic", ""))
            if topic_norm in skill_search_keywords(topic):
                item = {
                    "name": resource.get("Resource", resource.get("Topic", "Resource")),
                    "platform": resource.get("Platform", "Platform"),
                    "topic": resource.get("Topic", topic),
                    "description": resource.get("Description", "Great learning resource for this topic."),
                    "url": resource.get("URL", "https://example.com"),
                    "type": resource.get("Type", "Free")
                }
                key = (item["name"], item["url"])
                if key not in seen:
                    seen.add(key)
                    results.append(item)
                if len(results) >= limit:
                    return results
    return results


def get_day_objectives(topic):
    topic_map = {
        "Python": ["Variables and control flow", "Functions and modules", "Practice with mini exercises"],
        "SQL": ["SELECT, WHERE, ORDER BY", "GROUP BY and joins", "Practice with a sample database"],
        "Flask": ["Routes and templates", "Request handling", "Basic API logic"],
        "REST APIs": ["HTTP methods", "JSON payloads", "API design patterns"],
        "Git/GitHub": ["Version control basics", "Commits and branches", "Pull requests and collaboration"],
        "Docker": ["Container basics", "Images and commands", "Containerized app workflow"],
        "Java": ["Core syntax", "Collections and OOP", "Practice exercises"],
        "JavaScript": ["DOM and events", "Functions and arrays", "Modern ES6 usage"],
        "React": ["Components", "State and props", "Reusable UI patterns"],
        "Data Structures": ["Lists, stacks, queues", "Maps and sets", "Algorithmic thinking"],
        "Machine Learning": ["Concepts and data prep", "Model evaluation", "Practical notebook work"],
        "Cloud Fundamentals": ["Core services", "Architecture basics", "Hands-on deployment"],
        "Cybersecurity": ["Threat basics", "Secure practices", "Risk awareness"],
        "Testing": ["Unit testing basics", "Assertions and fixtures", "Coverage basics"],
        "Database Integration": ["Connections and queries", "ORM basics", "Schema design"],
        "Deployment": ["Environment setup", "Hosting basics", "Production configuration"],
        "Problem Solving": ["Patterns and logic", "Debugging", "Structured thinking"],
        "Communication": ["Technical writing", "Project explanation", "Stakeholder clarity"]
    }
    return topic_map.get(topic, ["Review fundamentals", "Practice with small scenarios", "Apply to a mini project"])


def get_day_practice(topic):
    practice_map = {
        "Python": "Write 10 small Python exercises covering loops, functions, and files.",
        "SQL": "Write 10 SQL queries using a sample employee or sales dataset.",
        "Flask": "Build a small Flask app with one route and one form to practice request flow.",
        "REST APIs": "Create a small API endpoint that returns JSON and test it with a client.",
        "Git/GitHub": "Create a simple project repository, commit changes, and review the history.",
        "Docker": "Containerize a simple app and run it locally in a Docker container.",
        "Java": "Solve 5 Java coding problems using classes, loops, and collections.",
        "JavaScript": "Build a small DOM-based page that updates UI state on interaction.",
        "React": "Create a reusable component with props and state management",
        "Data Structures": "Solve 5 algorithmic problems involving arrays, maps, and searching.",
        "Machine Learning": "Train a simple model on a small dataset and review accuracy metrics.",
        "Cloud Fundamentals": "Explore one cloud service and document its use case and architecture.",
        "Cybersecurity": "Review one common vulnerability and document mitigation steps.",
        "Testing": "Write unit tests for a small function and validate the pass/fail flow.",
        "Database Integration": "Connect an app to a lightweight database and run basic CRUD operations.",
        "Deployment": "Prepare and deploy a simple app to a cloud or local runtime.",
        "Problem Solving": "Solve one algorithmic challenge and explain your approach clearly.",
        "Communication": "Rewrite a project description in a concise, recruiter-friendly format."
    }
    return practice_map.get(topic, "Practice a focused challenge related to this topic and document your takeaway.")


def build_roadmap(target_role, current_skills, available_time, missing_skills):
    role_data = get_role_data(target_role)
    skills = missing_skills or role_data.get("required_skills", [])
    if len(skills) < 5:
        skills = skills + [
            "Git/GitHub",
            "Testing",
            "Deployment",
            "SQL"
        ]

    time_map = {
        "1 hour/day": "1 hour",
        "2 hours/day": "2 hours",
        "3 hours/day": "3 hours",
        "4 hours/day": "4 hours",
        "5+ hours/day": "4-5 hours"
    }

    roadmap = []
    for day in range(1, 31):
        topic = skills[(day - 1) % len(skills)]
        roadmap.append({
            "day": day,
            "topic": topic,
            "objectives": get_day_objectives(topic),
            "practice": get_day_practice(topic),
            "time": time_map.get(available_time, "2 hours"),
            "resources": get_resources_for_topics([topic], limit=2)
        })
    return roadmap


def extract_resume_text(file_path):
    ext = file_path.suffix.lower().replace(".", "")
    text = ""

    if ext == "pdf":
        if PdfReader is None:
            raise RuntimeError("pypdf is not installed.")
        reader = PdfReader(str(file_path))
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"
    elif ext == "docx":
        if Document is None:
            raise RuntimeError("python-docx is not installed.")
        doc = Document(str(file_path))
        for para in doc.paragraphs:
            text += para.text + "\n"
    return text


def detect_email(text):
    match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return bool(match)


def detect_phone(text):
    return bool(re.search(r"(?:\+?\d[\d\s().-]{8,}\d)", text))


def get_resume_strengths(text):
    strengths = []
    lower = text.lower()
    if re.search(r"\b(python|java|javascript|sql|react|flask|api|aws|docker)\b", lower):
        strengths.append("Technical skills are identifiable in the resume.")
    if "project" in lower or "projects" in lower:
        strengths.append("Project experience is mentioned.")
    if "education" in lower or "b.tech" in lower or "bachelor" in lower:
        strengths.append("Education section is clearly present.")
    if "github" in lower or "portfolio" in lower:
        strengths.append("GitHub or portfolio presence is mentioned.")
    if detect_email(text):
        strengths.append("Contact information appears to be available.")
    return strengths[:5]


def build_resume_analysis(resume_text, target_role):
    role_data = get_role_data(target_role)
    required_skills = role_data.get("required_skills", [])
    lower = resume_text.lower()
    matched = []
    missing = []
    for skill in required_skills:
        if normalize_skill(skill) in lower or any(token in lower for token in [normalize_skill(skill), normalize_skill(skill).replace(" ", "").replace("/", "")]):
            matched.append(skill)
        else:
            missing.append(skill)

    if not matched:
        matched = []
    if not missing:
        missing = required_skills[:5]

    sections_present = {
        "Contact": detect_email(resume_text) or detect_phone(resume_text),
        "Summary": any(token in lower for token in ["summary", "professional summary", "profile"]),
        "Skills": "skills" in lower,
        "Education": any(token in lower for token in ["education", "b.tech", "bachelor", "master"]),
        "Projects": "project" in lower,
        "Experience": any(token in lower for token in ["experience", "work experience", "internship"]),
        "Certifications": "certification" in lower or "certified" in lower,
    }

    keyword_match = round((len(matched) / max(len(required_skills), 1)) * 100)
    skills_match = round((len(matched) / max(len(required_skills), 1)) * 100)
    role_relevance = min(100, round((keyword_match + (80 if sections_present["Summary"] else 50) + (85 if sections_present["Projects"] else 60)) / 3))
    structure_score = round((sum(100 if present else 60 for present in sections_present.values()) / len(sections_present)))
    project_relevance = max(55, min(95, round(70 + (10 if sections_present["Projects"] else 0) + (10 if matched else 0))))
    ats_score = max(40, min(99, round((keyword_match * 0.35) + (skills_match * 0.25) + (role_relevance * 0.20) + (structure_score * 0.10) + (project_relevance * 0.10))))

    suggestions = {
        "skills": {
            "present": matched[:5],
            "missing": missing[:5]
        },
        "keywords": missing[:6],
        "projects": [
            "Rewrite project bullets to highlight the tech stack, your role, and measurable outcomes using action verbs.",
            "Add project metrics where truthful, such as performance, scale, or user impact.",
            "Explain how each project connects directly to the target role and business problem."
        ],
        "experience": [
            "Use action verbs such as built, optimized, analyzed, designed, and deployed.",
            "Link your responsibilities to the target role by naming tools, workflows, and outcomes.",
            "Include one or two measurable achievements if they reflect the actual work you completed."
        ],
        "summary": [
            f"Write a professional summary focused on {target_role} and emphasize your strongest relevant skills, tools, and project work.",
            "Keep the summary concise, role-specific, and aligned with the job description you are targeting."
        ],
        "certifications": [
            "Add certifications related to your target role where they reinforce your most important missing skills.",
            "Choose credentials with strong practical relevance and official provider pages."
        ]
    }

    strengths = get_resume_strengths(resume_text)
    if not strengths:
        strengths = ["The resume includes some relevant technical detail, but it would benefit from clearer role alignment."]

    learning_next = missing[:5] if missing else required_skills[:5]
    return {
        "target_role": target_role,
        "required_skills": required_skills,
        "matched_skills": matched,
        "missing_skills": missing,
        "keyword_match": keyword_match,
        "skills_match": skills_match,
        "role_relevance": role_relevance,
        "resume_structure": structure_score,
        "project_relevance": project_relevance,
        "ats_score": ats_score,
        "strengths": strengths,
        "suggestions": suggestions,
        "learning_next": learning_next,
        "sections_present": sections_present,
        "resume_text": resume_text
    }


def get_skill_resources_for_role(role_name, missing_skills):
    results = []
    for skill in missing_skills:
        for resource in LEARNING_RESOURCES:
            if normalize_skill(resource.get("Topic", "")) == normalize_skill(skill):
                results.append({
                    "skill": skill,
                    "resource": resource
                })
    if not results:
        for skill in missing_skills[:3]:
            results.append({
                "skill": skill,
                "resource": {
                    "Resource": f"{skill} practice guide",
                    "Platform": "Official Documentation",
                    "Description": f"Learn the core concepts behind {skill} and connect them to your target role.",
                    "URL": "https://www.google.com/search?q=" + quote_plus(skill + " tutorial"),
                    "Type": "Free"
                }
            })
    return results


def get_relevant_certifications(role_name, missing_skills):
    filtered = []
    role_norm = normalize_skill(role_name)
    for cert in CERTIFICATIONS:
        if cert.get("Role") and normalize_skill(cert["Role"]) == role_norm:
            filtered.append(cert)
        else:
            for skill in cert.get("Skills", []) if isinstance(cert.get("Skills", []), list) else [cert.get("Skills")]:
                if normalize_skill(str(skill)) in {normalize_skill(i) for i in missing_skills}:
                    filtered.append(cert)
                    break
    if not filtered and CERTIFICATIONS:
        filtered = CERTIFICATIONS[:3]
    return filtered[:4]


def get_relevant_paid_courses(role_name, missing_skills):
    filtered = []
    target = normalize_skill(role_name)
    for course in PAID_COURSES:
        if normalize_skill(course.get("Role", "")) == target:
            filtered.append(course)
        else:
            skills = course.get("Skills", [])
            if any(normalize_skill(str(skill)) in {normalize_skill(item) for item in missing_skills} for skill in skills):
                filtered.append(course)
    if not filtered:
        filtered = PAID_COURSES[:3]
    return filtered[:4]


def get_role_search_links(target_role):
    role_query = quote_plus(target_role)
    links = []
    for portal in JOB_PORTALS:
        search_url = portal["Search URL pattern"].format(query=role_query)
        links.append({
            "portal": portal["Portal"],
            "description": portal["Description"],
            "search_url": search_url,
            "base_url": portal["Base URL"]
        })
    return links


def is_allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def create_temp_resume_path(filename):
    safe_name = secure_filename(filename)
    unique = f"{uuid.uuid4()}_{safe_name}"
    return BASE_DIR / "uploads" / unique


@app.route("/")
def index():
    return render_template("index.html", roles=[role["Role"] for role in CAREER_ROLES])


@app.route("/career-guide")
def career_guide():
    return render_template("career-guide.html", roles=[role["Role"] for role in CAREER_ROLES])


@app.route("/generate-roadmap", methods=["POST"])
def generate_roadmap():
    name = request.form.get("name", "User").strip() or "User"
    role = request.form.get("target_role", "Python Developer")
    current_text = request.form.get("current_skills", "")
    available_time = request.form.get("available_time", "2 hours/day")

    current_skills = [skill.title() for skill in parse_skill_input(current_text)]
    role_data = get_role_data(role)
    required_skills = role_data.get("required_skills", [])
    missing_skills = find_missing_skills(current_skills, required_skills)

    if not missing_skills:
        missing_skills = required_skills[:5]

    roadmap = build_roadmap(role, current_skills, available_time, missing_skills)
    resources = get_skill_resources_for_role(role, missing_skills)
    certifications = get_relevant_certifications(role, missing_skills)
    courses = get_relevant_paid_courses(role, missing_skills)

    ai_prompt = (
        f"You are a career coach. Suggest a brief, practical guidance summary for a {role} candidate with "
        f"current skills {current_skills}. Missing skills: {', '.join(missing_skills)}. "
        "Keep the output concise and professional."
    )
    ai_guidance = get_gemini_response(ai_prompt)

    return render_template(
        "career-result.html",
        name=name,
        target_role=role,
        current_skills=current_skills,
        required_skills=required_skills,
        missing_skills=missing_skills,
        roadmap=roadmap,
        resources=resources,
        certifications=certifications,
        courses=courses,
        available_time=available_time,
        ai_guidance=ai_guidance
    )


@app.route("/resume-analyzer")
def resume_analyzer():
    return render_template("resume-analyzer.html", roles=[role["Role"] for role in CAREER_ROLES])


@app.route("/analyze-resume", methods=["POST"]) 
def analyze_resume():
    target_role = request.form.get("target_role", "Python Developer")
    file = request.files.get("resume_file")

    if not file or file.filename == "":
        return render_template("resume-analyzer.html", roles=[role["Role"] for role in CAREER_ROLES], error="Please upload a PDF or DOCX resume."), 400

    if not is_allowed_file(file.filename):
        return render_template("resume-analyzer.html", roles=[role["Role"] for role in CAREER_ROLES], error="Only PDF and DOCX resume files are allowed."), 400

    file_path = create_temp_resume_path(file.filename)
    try:
        file.save(str(file_path))
        resume_text = extract_resume_text(file_path)
    except Exception as exc:
        return render_template("resume-analyzer.html", roles=[role["Role"] for role in CAREER_ROLES], error=f"Resume could not be processed: {exc}"), 400

    if not resume_text.strip():
        return render_template("resume-analyzer.html", roles=[role["Role"] for role in CAREER_ROLES], error="The uploaded file did not contain readable text."), 400

    analysis = build_resume_analysis(resume_text, target_role)
    role_data = get_role_data(target_role)
    recommended_certifications = get_relevant_certifications(target_role, analysis["missing_skills"])
    recommended_courses = get_relevant_paid_courses(target_role, analysis["missing_skills"])
    job_portals = get_role_search_links(target_role)
    free_resources = get_skill_resources_for_role(target_role, analysis["missing_skills"])

    ai_prompt = (
        f"Analyze this resume for a {target_role} application. Provide concise career advice based on these resume findings: "
        f"matched skills={analysis['matched_skills']}; missing skills={analysis['missing_skills']}; strengths={analysis['strengths']}. "
        "Keep it actionable and short."
    )
    ai_guidance = get_gemini_response(ai_prompt)

    return render_template(
        "resume-result.html",
        target_role=target_role,
        role_data=role_data,
        analysis=analysis,
        certifications=recommended_certifications,
        paid_courses=recommended_courses,
        free_resources=free_resources,
        job_portals=job_portals,
        ai_guidance=ai_guidance
    )


@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
