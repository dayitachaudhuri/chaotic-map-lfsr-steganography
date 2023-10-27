from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from modes.image.image import image

app = Flask(__name__)

Bootstrap(app)

UPLOAD_IMAGE_FOLDER = 'modes\\image\\static'
# IMAGE_CACHE_FOLDER = 'modes\\Image\\__pycache__'

app.config['UPLOAD_IMAGE_FOLDER'] = UPLOAD_IMAGE_FOLDER
# app.config['IMAGE_CACHE_FOLDER'] = IMAGE_CACHE_FOLDER
app.register_blueprint(image, url_prefix="/image")

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == '__main__':
   app.run(debug=True)