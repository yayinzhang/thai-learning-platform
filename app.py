from flask import Flask, render_template
import mysql.connector as mysql

app = Flask(__name__)

@app.route('/')
def index():
    # 連接資料庫
    conn = mysql.connect(
        host="localhost",
        user="root",
        password="root",
        database="thai_learning"
    )
    cursor = conn.cursor(dictionary=True)

    # 撈出所有文章
    cursor.execute("SELECT id, title, chineseTitle, chineseContent, content, url, createdAt FROM Article ORDER BY createdAt DESC")
    articles = cursor.fetchall()

    cursor.close()
    conn.close()

    # 把 articles 傳進 HTML
    return render_template('index.html', articles=articles)

@app.route('/article/<int:article_id>')
def article_detail(article_id):
    # 連接資料庫
    conn = mysql.connect(
        host="localhost",
        user="root",
        password="root",
        database="thai_learning"
    )
    cursor = conn.cursor(dictionary=True)

    # 根據 ID 撈出文章
    cursor.execute("SELECT id, title, chineseTitle, chineseContent, content, url, createdAt FROM Article WHERE id = %s", (article_id,))
    article = cursor.fetchone()

    # 新增：撈出對應單字
    cursor.execute("""
        SELECT thai, chinese, type, pronunciation
        FROM Word
        WHERE articleId = %s
    """, (article_id,))
    words = cursor.fetchall()
    
    cursor.close()
    conn.close()

    if article:
        return render_template('article_detail.html', article=article, words=words)
    else:
        return "文章不存在", 404

@app.route("/vocabulary")
def vocabulary():
    conn = mysql.connect(
        host="localhost",
        user="root",
        password="root",
        database="thai_learning"
    )
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, thai, chinese, type, pronunciation, articleId FROM Word ORDER BY createdAt DESC")
    words = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("vocabulary.html", words=words)

if __name__ == "__main__":
    app.run(debug=True, port=5050)