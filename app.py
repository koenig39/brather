from flask import Flask, render_template, request, redirect
import csv
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from flask_cors import CORS  # Import CORS
import subprocess

app = Flask(__name__)
CORS(app)

# Function to generate badge with user data
def getBadge(fname, lname, cname):
    # Create a new image with a white background
    height = 696
    width = 1109
    background_color = (255, 255, 255)  # white color
    background = Image.new('RGB', (width, height), background_color)

    # Open and resize the logo image to overlay as background
    try:
        background_image = Image.open('./t3.bmp')  # Logo should be in the project folder
        # background_image = background_image.resize((400, 400))
    except IOError:
        return "Error: Logo file not found!"

    # Paste the logo onto the new image
    background.paste(background_image, (0, 0))

    # Add text (first name, last name, company) to the image
    draw = ImageDraw.Draw(background)
    
    left_margin = 450
    
    # Add fname
    name_text = f"{fname}"
    name_font = ImageFont.truetype("roboto.ttf", 96)  # Specify font and size
    name_color = (0, 0, 0)  # black color
    name_position = (left_margin-70, 65)  # Position for name text
    draw.text(name_position, name_text, fill=name_color, font=name_font)
    
    # Add lname
    name_text = f"{lname}"
    name_font = ImageFont.truetype("roboto.ttf", 96)  # Specify font and size
    name_color = (0, 0, 0)  # black color
    name_position = (left_margin-70, 210)  # Position for name text
    draw.text(name_position, name_text, fill=name_color, font=name_font)
    
    # Add company name
    company_text = f"{cname}"
    company_font = ImageFont.truetype("roboto.ttf", 45)  # Specify font and size
    company_color = (111, 111, 111)  # grey color
    company_position = (left_margin, 470)  # Position for company text
    draw.text(company_position, company_text, fill=company_color, font=company_font)

    # Save the generated badge image
    image_file = 'badge.png'
    background.save(image_file)
    
    return image_file

# Function to send the generated image to the printer
def sendToPrint(image_file):
    # Define the print command using subprocess
    ip1='192.168.24.241'
    command = f"brother_ql -p tcp://{ip1} -m QL-820NWB print -l 62x100 {image_file}"
    
    try:
        # Execute the print command
        # subprocess.run(command, shell=True, check=True)
        return "Print command executed successfully."
    except subprocess.CalledProcessError as e:
        return f"Error: Failed to execute print command. {e}"

# Route for the form page
@app.route('/')
def index():
    response = app.response_class()
    response.headers.set("ngrok-skip-browser-warning", "true")
    return render_template('form.html'), 200, response.headers

# Route to handle form submission and print the badge
@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        # Retrieve data from the form
        fname = request.form['fname']
        lname = request.form['lname']
        contact = request.form['contact']
        company = request.form['company']

        # Save data to CSV
        with open('data.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([fname, lname, company, contact, 0])

        # Generate the badge image
        image_file = getBadge(fname, lname, company)

        # If badge generation was successful, send it to print
        if image_file:
            print_status = sendToPrint("./badge.png")
            print(f"f-{fname}")
            print(f"l-{lname}")
            print(f"c-{company}")
            print(f"con-{contact}")
            print("YES!!!!!!!!!!!!!!!!=========>")
        else:
            print_status = "Error: Badge generation failed."

        return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
