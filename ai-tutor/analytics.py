import sqlite3
import matplotlib.pyplot as plt


def get_data():
    conn = sqlite3.connect("database/ai_tutor.db")
    cursor = conn.cursor()

    cursor.execute("SELECT score FROM quiz_history ORDER BY id")
    data = cursor.fetchall()

    conn.close()
    return data


def plot_progress():

    data = get_data()

    if len(data) == 0:
        print("No data available")
        return

    scores = []
    attempts = []

    for i, row in enumerate(data):
        scores.append(row[0])
        attempts.append(i + 1)

    plt.plot(attempts, scores, marker='o')

    plt.title("Student Progress Over Time")
    plt.xlabel("Attempts")
    plt.ylabel("Score")

    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    plot_progress()