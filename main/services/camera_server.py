# camera_server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
from pyzbar.pyzbar import decode
import numpy as np
import base64
from PIL import Image
import io
import requests

app = Flask(__name__)
CORS(app)

# ✅ دالة للبحث عن المنتج في Open Food Facts
def search_product(barcode):
    try:
        response = requests.get(f'https://world.openfoodfacts.org/api/v0/product/{barcode}.json', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 1:
                product = data['product']
                nutriments = product.get('nutriments', {})
                return {
                    'name': product.get('product_name', product.get('generic_name', f'منتج ({barcode[-8:]})')),
                    'calories': nutriments.get('energy-kcal', nutriments.get('energy', 0)),
                    'protein': nutriments.get('proteins', 0),
                    'carbs': nutriments.get('carbohydrates', 0),
                    'fat': nutriments.get('fat', 0),
                    'brand': product.get('brands', ''),
                    'unit': 'غرام'
                }
    except Exception as e:
        print(f'Error searching product: {e}')
    return None

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
            barcode = code.data.decode('utf-8')
            code_type = code.type
            
            # ✅ البحث عن المنتج
            product = search_product(barcode)
            
            if product:
                results.append({
                    'type': code_type,
                    'data': barcode,
                    'name': product['name'],
                    'calories': product['calories'],
                    'protein': product['protein'],
                    'carbs': product['carbs'],
                    'fat': product['fat'],
                    'brand': product.get('brand', ''),
                    'unit': product.get('unit', 'غرام')
                })
            else:
                # ✅ إذا لم يتم العثور على المنتج، نرسل البيانات الأساسية
                results.append({
                    'type': code_type,
                    'data': barcode,
                    'name': f'منتج جديد ({barcode[-8:]})',
                    'calories': 0,
                    'protein': 0,
                    'carbs': 0,
                    'fat': 0,
                    'brand': '',
                    'unit': 'غرام'
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
        print(f'Error: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)