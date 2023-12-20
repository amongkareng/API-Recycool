# import required modules
from flask import Flask, render_template, request
import numpy as np
import tensorflow as tf
import cv2
from keras.models import load_model
import jsonify
from flask import jsonify, make_response
from datetime import datetime
import uuid
from PIL import Image
import io




# Model to Use
predictions = {}
model_path = './models/MulticlassRecycool.h5'
loaded_model = load_model(model_path)


# create flask app
app = Flask(__name__)

# Function to validate UUID
def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


#Building API
@app.route('/')
def index():
    return render_template('index.html', message='Welcome to API.')

# Post Method
@app.route('/recycool', methods=['POST'])
def predict():
    try:
        # Error Handling
        if 'file' not in request.files:
            error_response = {
                'status': 'ERROR',
                'message': 'No file request'
            }
            return make_response(jsonify(error_response), 400)

        file = request.files['file']
        if file.filename == '':
            error_response = {
                'status': 'ERROR',
                'message': 'No selected file'
            }
            return make_response(jsonify(error_response), 400)

        allowed_extensions = {'png', 'jpg', 'jpeg'}
        if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            error_response = {
                'status': 'ERROR',
                'message': 'Invalid file format. Please upload an image (PNG, JPG, JPEG)'
            }
            return make_response(jsonify(error_response), 400)
        
        
        # Processing Logic
        file = request.files['file']
        img = Image.open(io.BytesIO(file.read()))

        # Process the image directly from memory
        img_rgb = img.convert('RGB')
        img_resized = img_rgb.resize((256, 256))
        img_array = np.array(img_resized) / 255.0
        img_normalized = np.expand_dims(img_array, axis=0)

        prediction = loaded_model.predict(img_normalized)
        predicted_class_index = np.argmax(prediction)
        confidence_score = np.max(prediction)

        class_names = ['Kaca', 'Kardus', 'Kertas', 'Organik', 'Plastik']
        predicted_class_name = class_names[predicted_class_index]
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Generate a unique ID
        unique_id = str(uuid.uuid4())

        # Prepare response JSON
        prediction_result = {
            'ID': unique_id,
            'predicted_class': predicted_class_name,
            'confidence_score': float(confidence_score),
            'insertedAt': timestamp
        }

        # Store prediction in the predictions dictionary
        predictions[unique_id] = prediction_result
        
        response = {
            'status': 'success',
            'message': 'Image upload successfully'
        }

        return make_response(jsonify(response), 201)
    
    except Exception as e:
        error_response = {
            'status': 'ERROR 400',
            'message': 'Failed to upload image'
        }
        return make_response(jsonify(error_response), 400)

# Get Method
@app.route('/recycool', methods=['GET'])
def get_results():
    if predictions:
        response = {
            'status': 'Success',
            'data': list(predictions.values())  # Convert dictionary values to a list
        }
        return make_response(jsonify(response), 200)
    else:
        error_response = {
            'status': 'ERROR 404',
            'message': 'No data available'
        }
        return make_response(jsonify(error_response), 404)

# Get Method by ID
@app.route('/recycool/<string:unique_id>', methods=['GET'])
def get_prediction(unique_id):
    if not is_valid_uuid(unique_id):
        error_response = {
            'status': 'ERROR 400',
            'message': 'Invalid ID format'
        }
        return make_response(jsonify(error_response), 400)

    if unique_id in predictions:
        response = {
            'status': 'Success',
            'data': predictions[unique_id]
        }
        return make_response(jsonify(response), 200)
    
    error_response = {
        'status': 'ERROR 404',
        'message': 'Not found for the given ID'
    }
    return make_response(jsonify(error_response), 404)

# Delete Method
@app.route('/recycool/<string:unique_id>', methods=['DELETE'])
def delete_prediction(unique_id):
    global predicted_results

    initial_length = len(predicted_results)
    predicted_results = [prediction for prediction in predicted_results if prediction['ID'] != unique_id]
    final_length = len(predicted_results)

    if final_length < initial_length:
        response = {
            'status': 'Success',
            'message': 'Deleted successfully'
        }
        return make_response(jsonify(response), 200)
    else:
        error_response = {
            'status': 'ERROR 404',
            'message': 'Not found for the given ID'
        }
        return make_response(jsonify(error_response), 404)


# Run flask server
if __name__ == '__main__':
    app.run(debug=True)