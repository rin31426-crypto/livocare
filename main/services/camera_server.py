# camera_server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
from pyzbar.pyzbar import decode
import numpy as np
import base64
from PIL import Image
import io

app = Flask(__name__)
CORS(app)

@app.route('/scan-barcode', methods=['POST'])
def scan_barcode():
    try:
        data = request.json
        image_data = data.get('image', '')
        
        # فك تشفير الصورة
        if 'base64,' in image_data:
            image_data = image_data.split('base64,')[1]
        
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        frame = np.array(image)
        
        # تحويل الألوان إذا لزم الأمر
        if len(frame.shape) == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # مسح الباركود
        results = []
        for code in decode(frame):
            data = code.data.decode('utf-8')
            code_type = code.type
            results.append({
                'type': code_type,
                'data': data
            })
        
        if results:
            return jsonify({
                'success': True,
                'results': results
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No barcode found'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)