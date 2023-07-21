import json

from flask import Flask, render_template, request
app = Flask(__name__)

import requests


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/voting/<int:voting_id>', methods=['GET', 'POST'])
def vote(voting_id):
    if request.method == 'POST':
        option = request.form['voting_option']
        data = {'option': option}
        result = requests.post(
            'http://localhost:8080/vote',
            data=json.dumps(data)
        )
        if result.status_code == 204:
            return render_template('success.html')
    return render_template('vote.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
