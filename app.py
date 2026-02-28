from flask import Flask ,render_template
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html') #open index.html from templates

if __name__=='__main__':
    app.run(debug=True) #we can see the error in the browser as well
