import os
from flask import Flask, render_template, request, redirect, url_for
import chromadb

app = Flask(__name__)
client = chromadb.PersistentClient(path="C:/Users/K Tarun/Desktop/Search engine")
collection = client.get_or_create_collection(name="search_engine")

@app.route('/', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form['query']
        return redirect(url_for('results', query=query))
    return render_template('search.html')

@app.route('/results', methods=['GET', 'POST'])
def results():
    if request.method == 'POST':
        query = request.form['query']
        results = collection.query(query_texts=[query], n_results=10)
        titles = [d['source'] for sublist in results['metadatas'] for d in sublist]
        information = results['documents'][0]
        return render_template('results.html', results=zip(titles, information))
    return redirect(url_for('search'))

if __name__ == '__main__':
    app.run(debug=True)