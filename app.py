# -*- coding: utf-8 -*-
"""
Created on Wed Feb  1 15:28:48 2023

@author: Lorenzo
"""

from flask import Flask, request, render_template
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/run_script', methods=['POST'])
def run_script():
    subprocess.call(["python", "chfsm.py"])
    return "Script executed successfully!"

if __name__ == '__main__':
    app.run()
