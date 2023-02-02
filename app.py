# -*- coding: utf-8 -*-
"""
Created on Wed Feb  1 15:28:48 2023

@author: Lorenzo
"""

from flask import Flask, request, render_template, redirect, send_file, make_response
import subprocess
import io
import pandas as pd
from time import sleep
from GSOMGame import main

app = Flask(__name__)

global result
global excel_input
result = pd.DataFrame([0])

@app.route('/')
def hello_world():
    #subprocess.call(["python", "chfsm.py"])
    return render_template("home.html")

@app.route("/upload", methods=["POST"])
def upload():
    global excel_input
    file = request.files["file"]
    file_content = file.read()
    excel_input = io.BytesIO(file_content)
    return redirect('/ready')
    
@app.route('/load_results',methods=["POST"])
def run():
    global result
    result = main(excel_input)
    sleep(2)
    return redirect('/result')

@app.route("/ready")
def ready():
    return render_template("ready.html")

@app.route('/result')
def display():
    return render_template("result.html")
  
@app.route("/download",methods=["POST"])
def download():
    # Generate a sample Pandas DataFrame
    global result
    global excel_input
    # Write the DataFrame to a BytesIO object
    buffer = io.BytesIO()
    writer = pd.ExcelWriter(buffer,engine='xlsxwriter')
    result['U'].to_excel(writer, sheet_name='U')
    result['Uop'].to_excel(writer, sheet_name='U (operators)')
    result['TH'].to_excel(writer, sheet_name='TH')

    writer.save()
    buffer.seek(0)
    # Create a response with the Excel file
    response = make_response(buffer.read())
    response.headers["Content-Disposition"] = "attachment; filename=result.xlsx"
    response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return response



'''
@app.route('/result')
def result():
    sleep(5)
    return 'ciaooo'

@app.route('/result/back')
def back_home():
    pass
'''

if __name__ == "__main__":
    app.run()