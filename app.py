from flask import Flask, request, jsonify, render_template
import os
from werkzeug.utils import secure_filename
import PIL.Image
import google.generativeai as genai
import json
import csv

# Initialize Flask app
app = Flask(__name__)

# Configure upload folder and allowed extensions
UPLOAD_FOLDER = '/home/annone/ai/flipkart_final/data/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
api_key = "AIzaSyBhd_aSdO_qz_C0y5oLYB1pstE0XC0-6nM"
prompt = "how many products are there in this image, name them, type of product (only among these: vegetable, fruit, or packet product), expiry datee if visible, days left of expiration, and rate their freshness between 1-10. Return the response in JSON format exactly like this '[{ 'product_name': 'Coconut', 'type': 'fruit', 'expiry_date': 'Not visible', 'expected_life_span': 'Not applicable', 'freshness': '7' }, { 'product_name': 'Cauliflower', 'type': 'vegetable', 'expiry_date': 'Not visible', 'expected_life_span': '20 days', 'freshness': '8' }]'"
genai.configure(api_key=api_key)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_image(image_path, prompt=prompt):
    try:
        image = PIL.Image.open(image_path)
        model = genai.GenerativeModel(model_name="gemini-1.5-pro")
        response = model.generate_content([prompt, image])
        return response.text
    except Exception as e:
        return f"An error occurred: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

# Route for uploading and processing the image
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Process the image
        try:
            raw_response = analyze_image(image_path=filepath, prompt=prompt)
            print(raw_response)
            cleaned_response = raw_response.strip('`').replace("```json", "").replace("```", "").replace("json", "").strip()
            text = json.loads(cleaned_response)
            csv_file = os.path.join(app.config['UPLOAD_FOLDER'], 'results.csv')
            clean_text = f"{text}"
            print(text)
            if isinstance(text, dict):
                for product in text.get("products", []):
                    with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
                        writer = csv.writer(file)
                        writer.writerow([
                            product.get("product_name", ""),
                            product.get("type", ""),
                            product.get("expiry_date", ""),
                            product.get("days_left", ""),
                            product.get("freshness", "")
                        ])
                    # text += f"{product.get("name", ""),}"
            else:
                for product in text:
                    with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
                        writer = csv.writer(file)
                        writer.writerow([
                            product.get("product_name", ""),
                            product.get("type", ""),
                            product.get("expiry_date", ""),
                            product.get("days_left", ""),
                            product.get("freshness", "")
                        ])
            return text
        except Exception as e:
            return jsonify({'error': f'Error processing image: {str(e)}'}), 500
    else:
        return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    app.run(debug=True)