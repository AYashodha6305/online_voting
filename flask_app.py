from flask import Flask, request, redirect, session, render_template_string
import sqlite3

app = Flask(__name__)
app.secret_key = "secret_key_123"

def get_db():
    conn = sqlite3.connect("voting.db")
    conn.row_factory = sqlite3.Row
    return conn

conn = get_db()
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT UNIQUE,
password TEXT,
voted INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS candidates (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
votes INTEGER DEFAULT 0
)
""")

cursor.execute("SELECT COUNT(*) FROM candidates")
if cursor.fetchone()[0] == 0:
    cursor.executemany(
        "INSERT INTO candidates (name, votes) VALUES (?,?)",
        [("A",0),("B",0),("C",0)]
    )

conn.commit()
conn.close()

login_page = """
<h2>Online Voting System</h2>

<h3>Register</h3>
<form method="post" action="/register">
<label>Enter Username:</label><br>
<input name="username" placeholder="Enter username" required><br><br>

<label>Enter Password:</label><br>
<input name="password" type="password" placeholder="Enter password" required><br><br>

<button type="submit">Register</button>
</form>

<br><hr><br>

<h3>Login</h3>
<form method="post" action="/login">
<label>Enter Username:</label><br>
<input name="username" placeholder="Enter username" required><br><br>

<label>Enter Password:</label><br>
<input name="password" type="password" placeholder="Enter password" required><br><br>

<button type="submit">Login</button>
</form>
"""

@app.route('/')
def home():
    return render_template_string(login_page)

@app.route('/register', methods=['POST'])
def register():
    u = request.form['username']
    p = request.form['password']

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO users (username,password) VALUES (?,?)",(u,p))
        conn.commit()
        conn.close()
        return """
        <script>
        alert('Registration successful! Please login.');
        window.location.href='/';
        </script>
        """
    except:
        conn.close()
        return """
        <script>
        alert('Username already exists!');
        window.location.href='/';
        </script>
        """

@app.route('/login', methods=['POST'])
def login():
    u = request.form['username']
    p = request.form['password']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=? AND password=?",(u,p))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['user'] = user['id']
        return redirect('/vote')

    return "<h3>Invalid login</h3><a href='/'>Go Back</a>"

@app.route('/vote')
def vote():
    if 'user' not in session:
        return redirect('/')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT voted FROM users WHERE id=?",(session['user'],))
    if cursor.fetchone()['voted'] == 1:
        return redirect('/results')

    cursor.execute("SELECT * FROM candidates")
    data = cursor.fetchall()
    conn.close()

    html = "<h2>Vote Now</h2><form method='post' action='/submit_vote'>"

    for c in data:
        html += f"<input type='radio' name='cid' value='{c['id']}' required> {c['name']}<br>"

    html += "<br><button type='submit'>Vote</button></form>"
    return html

@app.route('/submit_vote', methods=['POST'])
def submit_vote():
    if 'user' not in session:
        return redirect('/')

    cid = request.form['cid']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("UPDATE candidates SET votes=votes+1 WHERE id=?",(cid,))
    cursor.execute("UPDATE users SET voted=1 WHERE id=?",(session['user'],))

    conn.commit()
    conn.close()

    return redirect('/results')

@app.route('/results')
def results():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM candidates")
    data = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM users WHERE voted=1")
    total = cursor.fetchone()[0]

    conn.close()

    html = "<h2>Results</h2>"

    for c in data:
        html += f"{c['name']} : {c['votes']} votes<br>"

    html += f"<br><b>Total voters: {total}</b>"
    html += "<br><br><a href='/logout'>Logout</a>"

    return html

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
