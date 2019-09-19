from flask import request
from flask import Flask
import json
import numpy as np
from model import Localization
import os
os.environ['CUDA_VISIBLE_DEVICES']='0'
app = Flask(__name__)
model = Localization(gpu=True)


@app.route('/POST/localization', methods=['POST'])
def localization():
    if request.method == 'POST':
        if 'file' not in request.files:
            pass
        file = request.files['file'].read()
        width = request.files['width'].read().decode('utf-8')
        height = request.files['height'].read().decode('utf-8')
        depth = request.files['depth'].read().decode('utf-8')
        image = np.fromstring(file, dtype=np.uint8)
        image = np.reshape(image, (int(height), int(width), int(depth)))
        r = model.predict(image)
        return json.dumps(r.tolist())


if __name__ == '__main__':
    app.debug = False
    app.run(port=5001,host='0.0.0.0')
