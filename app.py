from flask import Flask, render_template, request, jsonify
import pandas as pd
import spacy
import datetime
import nltk
from nltk.corpus import names
from genderize import Genderize

app = Flask(__name__)

# Load data into DataFrame
df = pd.read_csv('sales_data_sample.csv', encoding='latin1')


# Load Spacy model
# You have to run this command on the terminal: "python -m spacy download en_core_web_sm"
nlp = spacy.load('en_core_web_sm')

# Function to extract keywords from a given text
def extract_keywords(text):
    doc = nlp(text.lower())
    keywords = [token.text for token in doc if not token.is_stop and not token.is_punct]
    return keywords

# Render the homepage with buttons
@app.route('/')
def index():
    return render_template('index.html')

# Answer Question route
@app.route('/answer_question', methods=['GET', 'POST'])
def answer_question():
    if request.method == 'POST':
        question = request.form['question']
        keywords = extract_keywords(question)

        if any(word in keywords for word in ['top', 'earn', 'sale', 'item']):
            top_item = df.loc[df['SALES'].idxmax()]
            return render_template('result.html', result={"Top Earning Sale Item": top_item.to_dict()})

        elif any(word in keywords for word in ['best', 'sales', 'city']):
            best_sales_city = df.groupby('CITY')['SALES'].sum().idxmax()
            return render_template('result.html', result={"Best Sales City": best_sales_city})

        elif any(word in keywords for word in ['customer', 'client']):
            top_customer = df.loc[df['SALES'].idxmax()]
            return render_template('result.html', result={"Top Customer": top_customer})

        elif any(word in keywords for word in ['product']):
            most_sold_product = df.groupby('PRODUCTCODE')['QUANTITYORDERED'].sum().idxmax()
            return render_template('result.html', result={"Most Sold Product": most_sold_product})

        elif any(word in keywords for word in ['month', 'period']):
            monthly_sales = df.groupby('MONTH_ID')['SALES'].sum()
            highest_sales_month = monthly_sales.idxmax()
            return render_template('result.html', result={"Month with Highest Sales": highest_sales_month})


        elif any(word in keywords for word in ['quantity']):
            highest_quantity = df.loc[df['QUANTITYORDERED'].idxmax()]
            return render_template('result.html', result={"Highest Quantity Ordered": highest_quantity})

        # Add more condition checks based on keywords for additional query types

        else:
            return render_template('result.html', result={"message": "Question not recognized"})

# Get Gender route
@app.route('/get_gender', methods=['GET', 'POST'])
def get_gender():
    ##################### nltk method ###################
    # nltk.download('names')
    # male_names = names.words('male.txt')
    # female_names = names.words('female.txt')
    ##################### nltk method ###################


    if request.method == 'POST':
        order_id = int(request.form['order_id'])
        orders = len(df.loc[df['ORDERNUMBER'] == order_id])

        if orders > 0:
            customer_row = df.loc[df['ORDERNUMBER'] == order_id]
            contact_first_name = customer_row['CONTACTFIRSTNAME'].values[0]
            name = contact_first_name.lower()

            ##################### nltk method ###################

            # if name in male_names:
            #     gender = 'Male'
            # elif name in female_names:
            #     gender = 'Female'
            # else:
            #     # Basic assumption: if the first name ends with 'e', assume it's female, otherwise male
            #     gender = 'Female' if name[-1] == 'e' else 'Male'

            ##################### nltk method ###################

            genderize = Genderize()
            gender = genderize.get([name])[0]['gender']
        else:
            contact_first_name = "Not Found"
            gender = "Not detected. You put wrong Order ID"
        return render_template('result.html', result={"First Name": contact_first_name, "Gender": gender})


# Function to convert string date to datetime object
def convert_to_datetime(date_str):
    return datetime.datetime.strptime(date_str, '%d/%M/%Y')

# Calculate average daily sales for the given month
def calculate_monthly_sales(month):
    month_data = df[df['MONTH_ID'] == month]
    daily_average_sales = month_data.groupby('ORDERDATE')['SALES'].sum().mean()
    return daily_average_sales


# Get Recommendation route
@app.route('/get_recommendation', methods=['GET', 'POST'])
def get_recommendation():
    if request.method == 'POST':
        month = int(request.form['month'])
        daily_average_sales = calculate_monthly_sales(month)

        month_data = df[df['MONTH_ID'] == month]
        anomalies = month_data.groupby('ORDERDATE')['SALES'].sum() > (2 * daily_average_sales)
        anomaly_dates = anomalies[anomalies].index.tolist()

        if not anomaly_dates:
            recommendation = "No anomalies or significant trends found in the given month."
        else:
            recommendation = f"Potential anomalies or significant trends found on the following dates: {', '.join(anomaly_dates)}"

        return render_template('result.html', result={"Recommendation": recommendation})


if __name__ == '__main__':
    app.run(debug=True)
