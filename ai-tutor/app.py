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
# QUIZ PAGE
# =========================
@app.route("/quiz")
def quiz():
    return render_template("quiz.html")


# =========================
# QUIZ RESULT
# =========================
@app.route("/submit_quiz", methods=["POST"])
def submit_quiz():

    score = 0
    weak_topics = []
    recommendations = []

    q1 = request.form.get("q1")
    q2 = request.form.get("q2")

    if q1 == "4":
        score += 1
    else:
        weak_topics.append("Basic Math")
        recommendations.append("Practice arithmetic")

    if q2 == "Islamabad":
        score += 1
    else:
        weak_topics.append("General Knowledge")
        recommendations.append("Learn capitals")

    # ML prediction safety
    prediction = model.predict([[score]])[0]

    level_map = {
        0: "Very Weak",
        1: "Weak",
        2: "Strong"
    }

    level = level_map.get(prediction, "Unknown")

    email = session.get("email")

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
        recommendations=recommendations
    )


# =========================
# 📊 ANALYTICS DASHBOARD (FINAL FIXED)
# =========================
@app.route("/analytics")
def analytics():

    email = session.get("email")

    conn = sqlite3.connect("database/ai_tutor.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM quiz_history
        WHERE email=?
        ORDER BY id
    """, (email,))

    history = cursor.fetchall()
    conn.close()

    # =========================
    # SCORE EXTRACTION
    # =========================
    scores = [row[2] for row in history]

    # =========================
    # AVG SCORE
    # =========================
    avg_score = round(sum(scores) / len(scores), 2) if scores else 0

    # =========================
    # SMART GRAPH GENERATION (FIXED + CLEAN)
    # =========================
    graph_path = None

    if scores:

        import matplotlib.pyplot as plt
        import os

        attempts = list(range(1, len(scores) + 1))

        # AI TREND (SMOOTH LINE)
        smooth_scores = []

        for i in range(len(scores)):
            window = scores[max(0, i-2):i+1]
            smooth_scores.append(sum(window) / len(window))

        plt.figure(figsize=(7,4))

        # Raw score line
        plt.plot(attempts, scores, marker='o', linestyle='--', alpha=0.4, label="Raw Score")

        # AI trend line
        plt.plot(attempts, smooth_scores, marker='o', linewidth=3, label="AI Learning Trend")

        plt.title("📊 AI Student Progress Analysis")
        plt.xlabel("Quiz Attempts")
        plt.ylabel("Score")
        plt.ylim(0, 1.2)
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

        # Basic AI Tutor Logic
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

# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)