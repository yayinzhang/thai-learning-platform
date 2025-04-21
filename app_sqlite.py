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
    
    # 加入字數與文法數量查詢
    article_data = []
    for article in articles:
        article_id = article['id']
        word_count = conn.execute('SELECT COUNT(*) FROM Word WHERE articleId = ?', (article_id,)).fetchone()[0]
        grammar_count = conn.execute('SELECT COUNT(*) FROM GrammarPoint WHERE articleId = ?', (article_id,)).fetchone()[0]
        article_data.append({**dict(article), 'wordCount': word_count, 'grammarCount': grammar_count})
    
    conn.close()
    return render_template('index.html', articles=article_data)

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

    if article:
        return render_template(
            'article_detail.html',
            article=article,
            words=words,
            grammars=grammars
        )
    else:
        return "文章不存在", 404

@app.route('/vocabulary')
def vocabulary():
    conn = get_db_connection()
    words = conn.execute('SELECT * FROM Word ORDER BY createdAt DESC').fetchall()
    conn.close()
    return render_template('vocabulary.html', words=words)

@app.route('/grammar')
def grammar():
    conn = get_db_connection()
    grammar_points = conn.execute('SELECT * FROM GrammarPoint ORDER BY createdAt DESC').fetchall()
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
    return render_template('grammar.html', grammar_points=grammar_data)



if __name__ == "__main__":
    app.run(debug=True, port=5050)