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
    articles = conn.execute('SELECT * FROM Article WHERE status = "published" ORDER BY createdAt DESC').fetchall()
    
    # 加入字數與文法數量查詢
    article_data = []
    for article in articles:
        article_id = article['id']
        word_count = conn.execute('SELECT COUNT(*) FROM Word WHERE articleId = ?', (article_id,)).fetchone()[0]
        grammar_count = conn.execute('SELECT COUNT(*) FROM GrammarPoint WHERE articleId = ?', (article_id,)).fetchone()[0]
        article_data.append({**dict(article), 'wordCount': word_count, 'grammarCount': grammar_count})
    
    conn.close()
    return render_template('index_adjust.html', articles=article_data)

@app.route('/article/<int:article_id>')
def article_detail(article_id):
    conn = get_db_connection()

    article = conn.execute('SELECT * FROM Article WHERE id = ?', (article_id,)).fetchone()
    words = conn.execute('SELECT * FROM Word WHERE articleId = ?', (article_id,)).fetchall()

    grammar_points = conn.execute(
        'SELECT * FROM GrammarPoint WHERE articleId = ?', (article_id,)
    ).fetchall()

    grammars = []
    for gp in grammar_points:
        examples = conn.execute(
            'SELECT * FROM GrammarExample WHERE grammarPointId = ?', (gp['id'],)
        ).fetchall()
        grammars.append({
            'id': gp['id'],
            'title': gp['title'],
            'explanation': gp['explanation'],
            'examples': examples
        })

    conn.close()

    if article and article['status'] == 'published':
        return render_template(
            'article_detail_adjust.html',
            article=article,
            words=words,
            grammars=grammars
        )
    else:
        return "文章不存在", 404

@app.route('/vocabulary')
def vocabulary():
    conn = get_db_connection()
    words = conn.execute("""
        SELECT * FROM Word
        WHERE articleId IN (
            SELECT id FROM Article WHERE status = 'published'
        )
        ORDER BY createdAt DESC
    """).fetchall()
    conn.close()
    return render_template('vocabulary_adjust.html', words=words)

@app.route('/grammar')
def grammar():
    conn = get_db_connection()
    grammar_points = conn.execute("""
        SELECT * FROM GrammarPoint
        WHERE articleId IN (
            SELECT id FROM Article WHERE status = 'published'
        )
        ORDER BY createdAt DESC
    """).fetchall()
    grammar_data = []
    for point in grammar_points:
        examples = conn.execute('SELECT * FROM GrammarExample WHERE grammarPointId = ?', (point['id'],)).fetchall()
        grammar_data.append({
            'id': point['id'],
            'title': point['title'],
            'explanation': point['explanation'],
            'examples': examples,
            'articleId': point['articleId']
        })

    conn.close()
    return render_template('grammar_adjust.html', grammar_points=grammar_data)

@app.route('/admin')
def admin():
    conn = get_db_connection()
    # 加入 status 欄位
    articles = conn.execute('SELECT id, title, createdAt, status FROM Article ORDER BY createdAt DESC').fetchall()
    conn.close()
    return render_template('admin.html', articles=articles)

# 編輯文章頁面，支援 status 欄位更新
from flask import request, redirect
@app.route('/admin/edit-article/<int:article_id>', methods=['GET', 'POST'])
def edit_article(article_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        new_title = request.form['title']
        new_chinese_title = request.form['chineseTitle']
        new_content = request.form['content']
        new_chinese = request.form['chineseContent']
        new_status = request.form['status']

        cursor.execute("""
            UPDATE Article
            SET title = ?, chineseTitle = ?, content = ?, chineseContent = ?, status = ?
            WHERE id = ?
        """, (new_title, new_chinese_title, new_content, new_chinese, new_status, article_id))

        conn.commit()
        conn.close()
        return redirect('/admin')

    article = conn.execute("SELECT * FROM Article WHERE id = ?", (article_id,)).fetchone()
    conn.close()
    return render_template("edit_article.html", article=article)

# 狀態切換路由
@app.route('/admin/toggle-status/<int:article_id>', methods=['POST'])
def toggle_status(article_id):
    conn = get_db_connection()
    article = conn.execute('SELECT status FROM Article WHERE id = ?', (article_id,)).fetchone()
    new_status = 'draft' if article['status'] == 'published' else 'published'

    conn.execute('UPDATE Article SET status = ? WHERE id = ?', (new_status, article_id))
    conn.commit()
    conn.close()
    return redirect('/admin')

if __name__ == "__main__":
    app.run(debug=True, port=5050)
