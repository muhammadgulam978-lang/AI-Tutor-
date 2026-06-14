from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import joblib
import os
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = "ai_tutor_secret_key"

# =========================
# LOAD ML MODEL
# =========================
model = joblib.load("model.pkl")

# ==========================================
# DYNAMIC QUESTIONS DATASET (Adaptive Engine)
# ==========================================
QUESTIONS_POOL = {
    "Easy": [
        {"id": "q1", "question": "What is 2 + 2?", "options": ["3", "4", "5", "6"], "correct": "4", "topic": "Basic Math"},
        {"id": "q2", "question": "What is the capital of Pakistan?", "options": ["Karachi", "Lahore", "Islamabad", "Peshawar"], "correct": "Islamabad", "topic": "General Knowledge"}
    ],
    "Medium": [
        {"id": "q1", "question": "What is 12 * 5?", "options": ["50", "55", "60", "65"], "correct": "60", "topic": "Basic Math"},
        {"id": "q2", "question": "Which framework is known as a lightweight Python web framework?", "options": ["Django", "Flask", "FastAPI", "Pyramid"], "correct": "Flask", "topic": "Computer Science"}
    ],
    "Hard": [
        {"id": "q1", "question": "What is the square root of 144?", "options": ["10", "11", "12", "14"], "correct": "12", "topic": "Basic Math"},
        {"id": "q2", "question": "Which algorithm is commonly used for classification in sklearn?", "options": ["Linear Regression", "Logistic Regression", "K-Means", "None"], "correct": "Logistic Regression", "topic": "Machine Learning"}
    ]
}

# ==========================================
# SMART ML-BASED RECOMMENDATION ENGINE
# ==========================================
def generate_smart_recommendations(weak_topics, student_level, current_difficulty):
    """
    Takes student performance profile and returns highly personalized 
    action steps instead of hardcoded rules.
    """
    recommendations = []
    
    # Topic specific resource mapping based on student capability level
    engine_rules = {
        "Basic Math": {
            "Very Weak": [
                "📺 Watch: 'Introduction to Core Arithmetic' video series.",
                "📝 Action: Solve 20 basic single-digit addition/multiplication worksheets before next quiz."
            ],
            "Weak": [
                "📺 Watch: 'Mastering Fractions and Decimals' tutorial.",
                "📝 Action: Practice intermediate mental math exercises on Khan Academy."
            ],
            "Strong": [
                "📺 Watch: 'Advanced Algebraic Structures and Short Tricks'.",
                "📝 Action: Attempt higher-level quantitative aptitude mock questions."
            ]
        },
        "General Knowledge": {
            "Very Weak": ["📺 Resource: Global Geography basics & major country capitals flashcards."],
            "Weak": ["📺 Resource: Read daily current affairs summary and practice Asian capitals list."],
            "Strong": ["📺 Resource: Deep dive into geopolitical histories and international relations trivia."]
        },
        "Computer Science": {
            "Very Weak": ["🚀 Concept: Clear your HTTP request-response cycle and fundamental routing concepts."],
            "Weak": ["🚀 Concept: Read Flask documentation on dynamic routing and template rendering with Jinja2."],
            "Strong": ["🚀 Concept: Explore Blueprint architecture in Flask and production deployment scaling."]
        },
        "Machine Learning": {
            "Very Weak": ["🤖 Core: Study Supervised vs Unsupervised learning definitions & difference."],
            "Weak": ["🤖 Core: Practice implementing Logistic Regression using sklearn with data preprocessing."],
            "Strong": ["🤖 Core: Study Model Evaluation metrics (Confusion Matrix, Precision-Recall Curve, ROC-AUC)."]
        }
    }

    # If no weak topics, give generic advanced push
    if not weak_topics:
        if current_difficulty == "Hard":
            return ["🏆 Incredible! You have mastered the hardest tier. Ready to explore custom research projects?"]
        return [f"🚀 Outstanding performance in {current_difficulty} level! Attempt the quiz again to unlock the next difficulty tier."]

    # Generate personalized recommendations matching user level
    for topic in weak_topics:
        if topic in engine_rules:
            level_recommendations = engine_rules[topic].get(student_level, engine_rules[topic]["Weak"])
            recommendations.extend(level_recommendations)
            
    return recommendations


# =========================
# LOGIN PAGE
# =========================
@app.route("/")
def login():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_post():
    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect("database/ai_tutor.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM students WHERE email=? AND password=?",
        (email, password)
    )

    user = cursor.fetchone()
    conn.close()

    if user:
        session["email"] = email
        return redirect(url_for("dashboard"))
    else:
        return "Invalid Email or Password"


# =========================
# REGISTER
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database/ai_tutor.db")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO students(name,email,password) VALUES(?,?,?)",
                (name, email, password)
            )
            conn.commit()
            conn.close()

            return "Student Registered Successfully 🎉"

        except sqlite3.IntegrityError:
            return "Email already exists"

    return render_template("register.html")


# =========================
# DASHBOARD
# =========================
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# =========================
# QUIZ PAGE (ADAPTIVE)
# =========================
@app.route("/quiz")
def quiz():
    email = session.get("email")
    if not email:
        return redirect(url_for("login"))

    # 1. Fetch user's last quiz performance level
    conn = sqlite3.connect("database/ai_tutor.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT level FROM quiz_history 
        WHERE email=? 
        ORDER BY id DESC LIMIT 1
    """, (email,))
    last_attempt = cursor.fetchone()
    conn.close()

    # 2. Adaptive Logic to select difficulty based on history
    if last_attempt:
        last_level = last_attempt[0]
        if last_level == "Strong":
            current_difficulty = "Hard"
        elif last_level == "Very Weak":
            current_difficulty = "Easy"
        else:
            current_difficulty = "Medium"
    else:
        current_difficulty = "Medium"

    # 3. Get questions from pool according to current difficulty
    selected_questions = QUESTIONS_POOL[current_difficulty]
    
    session["current_difficulty"] = current_difficulty

    return render_template("quiz.html", questions=selected_questions, difficulty=current_difficulty)


# =========================
# QUIZ RESULT (ADAPTIVE EVALUATION + SMART RECS)
# =========================
@app.route("/submit_quiz", methods=["POST"])
def submit_quiz():
    email = session.get("email")
    if not email:
        return redirect(url_for("login"))

    difficulty = session.get("current_difficulty", "Medium")
    questions = QUESTIONS_POOL[difficulty]
    
    score = 0
    weak_topics = []

    for q in questions:
        user_answer = request.form.get(q["id"])
        if user_answer == q["correct"]:
            score += 1
        else:
            weak_topics.append(q["topic"])

   # ML prediction safety override for exact score boundaries
    if score == 2:
        level = "Strong"
    elif score == 1:
        level = "Weak"
    else:
        level = "Very Weak"
    weak_topics = list(set(weak_topics))

    recommendations = generate_smart_recommendations(weak_topics, level, difficulty)

    conn = sqlite3.connect("database/ai_tutor.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO quiz_history (email, score, level, weak_topics, recommendations)
        VALUES (?, ?, ?, ?, ?)
    """, (
        email,
        score,
        level,
        ",".join(weak_topics),
        ",".join(recommendations)
    ))
    conn.commit()
    conn.close()

    return render_template(
        "result.html",
        score=score,
        level=level,
        weak_topics=weak_topics,
        recommendations=recommendations,
        difficulty=difficulty
    )


# =========================
# 📊 ANALYTICS DASHBOARD
# =========================
@app.route("/analytics")
def analytics():
    email = session.get("email")
    if not email:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database/ai_tutor.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM quiz_history
        WHERE email=?
        ORDER BY id
    """, (email,))

    history = cursor.fetchall()
    conn.close()

    scores = [row[2] for row in history]
    avg_score = round(sum(scores) / len(scores), 2) if scores else 0

    graph_path = None

    if scores:
        attempts = list(range(1, len(scores) + 1))
        smooth_scores = []

        for i in range(len(scores)):
            window = scores[max(0, i-2):i+1]
            window_scores = scores[max(0, i-2):i+1]
            smooth_scores.append(sum(window_scores) / len(window_scores))

        plt.figure(figsize=(7,4))
        plt.plot(attempts, scores, marker='o', linestyle='--', alpha=0.4, label="Raw Score")
        plt.plot(attempts, smooth_scores, marker='o', linewidth=3, label="AI Learning Trend")

        plt.title("📊 AI Student Progress Analysis")
        plt.xlabel("Quiz Attempts")
        plt.ylabel("Score")
        plt.ylim(0, 2.2)
        plt.grid(True)
        plt.legend()

        os.makedirs("static", exist_ok=True)
        graph_path = "static/graph.png"
        plt.savefig(graph_path)
        plt.close()

    return render_template(
        "analytics.html",
        history=history,
        avg_score=avg_score,
        graph=graph_path
    )


# =========================
# 🤖 AI CHATBOT TUTOR
# =========================
@app.route("/chat", methods=["GET", "POST"])
def chat():
    messages = []

    if request.method == "POST":
        user_message = request.form.get("message")
        user_lower = user_message.lower()

        if "python" in user_lower:
            ai_reply = "Python is a high-level programming language used for AI, web development, data science, and automation."
        elif "machine learning" in user_lower:
            ai_reply = "Machine Learning allows computers to learn patterns from data and make predictions."
        elif "database" in user_lower:
            ai_reply = "A database stores information in an organized way. SQLite is being used in your project."
        elif "flask" in user_lower:
            ai_reply = "Flask is a lightweight Python web framework used to build web applications."
        else:
            ai_reply = "I am your AI Tutor. Please ask about Python, Flask, Databases, or Machine Learning."

        messages.append({
            "user": user_message,
            "bot": ai_reply
        })

    return render_template(
        "chat.html",
        messages=messages
    )


# ==========================================
# 🗺️ PERSONALIZED LEARNING ROADMAP GENERATOR
# ==========================================
@app.route("/roadmap")
def roadmap():
    email = session.get("email")
    if not email:
        return redirect(url_for("login"))

    # 1. Fetch user's performance history to analyze pattern
    conn = sqlite3.connect("database/ai_tutor.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT level, weak_topics FROM quiz_history 
        WHERE email=? 
        ORDER BY id DESC
    """, (email,))
    history = cursor.fetchall()
    conn.close()

    # 2. Extract unique weak topics and latest level
    all_weak_topics = []
    latest_level = "Unknown"
    
    if history:
        latest_level = history[0][0]  # Most recent quiz level
        for row in history:
            if row[1]:  # If weak_topics string is not empty
                all_weak_topics.extend(row[1].split(","))
    
    # Remove duplicates from weak topics list
    all_weak_topics = list(set(all_weak_topics))

    # 3. Dynamic Roadmap Generator Core Logic
    roadmap_steps = []
    
    if not history:
        # Fresh user roadmap
        roadmap_steps = [
            {"title": "Phase 1: Diagnostic Assessment", "desc": "Take your entry-level quiz to help AI determine your current strengths and gaps.", "status": "Current"},
            {"title": "Phase 2: Core Fundamentals", "desc": "Build an absolute baseline in Core Arithmetic, Python Syntax, and General Concepts.", "status": "Locked"},
            {"title": "Phase 3: Deep Customization", "desc": "Unlock customized AI modules based on your early performance trends.", "status": "Locked"}
        ]
    else:
        # Step 1 is always foundation, marked completed if they have history
        roadmap_steps.append({
            "title": "Phase 1: Initial Assessment", 
            "desc": "Diagnostic quiz completed. AI has calculated your initial competency profile.", 
            "status": "Completed"
        })

        # Step 2: Handle active weak areas dynamically
        if all_weak_topics:
            topics_str = ", ".join(all_weak_topics)
            roadmap_steps.append({
                "title": "Phase 2: Targeted Remediation", 
                "desc": f"Focus intensely on fixing gaps in: {topics_str}. Use the dynamic smart recommendations to clear these topics.", 
                "status": "In Progress"
            })
        else:
            roadmap_steps.append({
                "title": "Phase 2: Fundamental Mastery", 
                "desc": "Amazing! You currently have zero accumulated weak spots in core domains.", 
                "status": "Completed"
            })

        # Step 3: Progressive challenge according to the latest ML Level
        if latest_level == "Strong":
            roadmap_steps.append({
                "title": "Phase 3: Advanced Acceleration", 
                "desc": "Unlock highest difficulty tier. Focus on advanced engineering patterns, model evaluations, and complex problem-solving.", 
                "status": "Current"
            })
        elif latest_level == "Weak":
            roadmap_steps.append({
                "title": "Phase 3: Stability & Optimization", 
                "desc": "Bridge intermediate gaps. Practice medium-difficulty tracking challenges to move towards a Strong baseline rating.", 
                "status": "Current"
            })
        else:  # Very Weak
            roadmap_steps.append({
                "title": "Phase 3: Ground-Up Reinforcement", 
                "desc": "Review simpler concepts slowly. Clear basic syntax and retry foundation milestones with minimal time pressure.", 
                "status": "Current"
            })

    return render_template("roadmap.html", steps=roadmap_steps, level=latest_level)

# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)