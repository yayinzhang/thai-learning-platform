from flask import Flask, render_template
import os
import sqlite3

app = Flask(__name__)

# 共用的資料查詢函數
def get_db_connection():
    base_path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_path, 'data.db')
    conn = sqlite3.connect(db_path)  # SQLite 檔名
    conn.row_factory = sqlite3.Row     # 讓取出的資料像字典一樣操作
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    articles = conn.execute('SELECT * FROM Article ORDER BY createdAt DESC').fetchall()
    conn.close()
    return render_template('index.html', articles=articles)

@app.route('/article/<int:article_id>')
def article_detail(article_id):
    conn = get_db_connection()
    article = conn.execute('SELECT * FROM Article WHERE id = ?', (article_id,)).fetchone()
    words = conn.execute('SELECT * FROM Word WHERE articleId = ?', (article_id,)).fetchall()
    conn.close()
    if article:
        return render_template('article_detail.html', article=article, words=words)
    else:
        return "文章不存在", 404

@app.route('/vocabulary')
def vocabulary():
    conn = get_db_connection()
    words = conn.execute('SELECT * FROM Word ORDER BY createdAt DESC').fetchall()
    conn.close()
    return render_template('vocabulary.html', words=words)

if __name__ == "__main__":
    app.run(debug=True, port=5050)