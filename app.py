from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from peewee import *
from datetime import datetime
import subprocess, os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generates a random 24-byte key

# Database setup
database_name = "database.db"
sqlite_db = SqliteDatabase(database_name, pragmas={'journal_mode': 'wal'})

class BaseModel(Model):
    class Meta:
        database = sqlite_db

class Person(BaseModel):
    id = AutoField()
    fname = CharField()
    lname = CharField()
    company = CharField()
    contact = CharField()

class Event(BaseModel):
    id = AutoField()
    name = CharField()
    descr = TextField()
    date = DateTimeField()
    active = IntegerField(default=0)  # 1 for active, 0 for inactive

    @classmethod
    def set_active_event(cls, event_id):
        cls.update(active=0).execute()
        cls.update(active=1).where(cls.id == event_id).execute()

class PersonEvent(BaseModel):
    person = ForeignKeyField(Person, backref='events')
    event = ForeignKeyField(Event, backref='attendees')

    class Meta:
        database = sqlite_db
        primary_key = CompositeKey('person', 'event')

sqlite_db.connect()
sqlite_db.create_tables([Person, Event, PersonEvent])


import base64, io
from PIL import Image, ImageDraw, ImageFont

def create_conference_badge(fname, lname, company):
    # Load the original background image
    template_path = 'template_badge.bmp'  # Replace with the path to your template image
    badge = Image.open(template_path)
    width, height = badge.size

    # Set up drawing context
    draw = ImageDraw.Draw(badge)

    # Load fonts (adjust paths if needed)
    try:
        font_large = ImageFont.truetype("arial.ttf", 96)
        font_small = ImageFont.truetype("arial.ttf", 56)
    except IOError:
        # Fallback to default font if specific font not found
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Define text and colors
    name_text = f"{fname} {lname}"
    company_text = company
    text_color = (0, 0, 0)  # Black

    # Calculate centered positions based on text bounding box (using textbbox)
    name_bbox = draw.textbbox((0, 0), name_text, font=font_large)
    name_position = ((width - (name_bbox[2] - name_bbox[0])) // 2, 150)

    company_bbox = draw.textbbox((0, 0), company_text, font=font_small)
    company_position = ((width - (company_bbox[2] - company_bbox[0])) // 2, 370)

    # Draw the text on the badge
    draw.text(name_position, name_text, fill=text_color, font=font_large)
    draw.text(company_position, company_text, fill=text_color, font=font_small)

    # Save the image to an in-memory file and encode it as base64
    image_io = io.BytesIO()
    badge.save(image_io, 'PNG')
    image_io.seek(0)
    base64_image = base64.b64encode(image_io.getvalue()).decode('utf-8')

    return base64_image

@app.route('/person_card_view')
def person_card_view():
    # Generate the badge image as a base64 string
    base64_image = create_conference_badge("John", "Doe", "Company LLC")

    # Pass the base64 image to the template
    return render_template('person_card_view.html', base64_image=base64_image)


@app.route('/activate_event/<int:event_id>')
def activate_event(event_id):
    # Set all events to inactive
    Event.update(active=0).execute()
    
    # Set the specified event to active
    Event.update(active=1).where(Event.id == event_id).execute()
    
    flash("Event activated successfully.")
    return redirect(url_for('events_list'))


@app.route('/generate_badge/<int:person_id>')
def generate_badge(person_id):
    # Retrieve person details by ID
    person = Person.get_or_none(Person.id == person_id)
    if not person:
        return "Person not found", 404

    # Generate the badge
    badge_file = create_conference_badge(person.fname, person.lname, person.company)

    # Send the generated image as a downloadable file
    return send_file(badge_file, as_attachment=True, download_name=f"{person.fname}_{person.lname}_badge.png")


@app.route('/person_card')
def person_card():
    # Sample data for the person card
    fname = "John"
    lname = "Doe"
    company = "Company LLC"

    # Generate the badge as an in-memory image file
    image_file = create_conference_badge(fname, lname, company)

    # Send the image file directly to the browser
    return send_file(image_file, mimetype='image/png')


@app.route('/print_badge/<int:person_id>')
def print_badge(person_id):
    # Retrieve person details by ID
    person = Person.get_or_none(Person.id == person_id)
    if not person:
        return "Person not found", 404

    # Generate the badge
    badge_file = create_conference_badge(person.fname, person.lname, person.company)

    # Define the print command
    command = f"brother_ql -p tcp://10.4.6.76 -m QL-820NWB print -l 62x100 {badge_file}"
    
    # Execute the command in the console
    try:
        # subprocess.run(command, shell=True, check=True)
        flash("Print command executed successfully.")
    except subprocess.CalledProcessError as e:
        flash(f"An error occurred: {e}")
    
    # Redirect back to the event details page
    return redirect(url_for('event_detail', event_id=person.events[0].event.id))


@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/events_list')
def events_list():
    # Retrieve all events ordered by event ID and date with count of registered persons
    events = (
        Event
        .select(Event, fn.COUNT(PersonEvent.person).alias('registration_count'))
        .join(PersonEvent, JOIN.LEFT_OUTER, on=(Event.id == PersonEvent.event))
        .group_by(Event)
        .order_by(Event.id, Event.date.desc())
    )
    return render_template('events_list.html', events=events)

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        # Retrieve data from the form
        fname = request.form['fname']
        lname = request.form['lname']
        contact = request.form['contact']
        company = request.form['company']
        
        # Create or get person record
        person, created = Person.get_or_create(fname=fname, lname=lname, contact=contact, company=company)
        
        # Retrieve the active event
        active_event = Event.get_or_none(Event.active == 1)
        
        # Ensure there's an active event before proceeding
        if active_event:
            # Register the person to the active event
            PersonEvent.get_or_create(person=person, event=active_event)
            
            # Optional: Badge generation logic
            badge_text = f"Name: {person.fname} {person.lname}\nCompany: {person.company}\nContact: {person.contact}\nEvent: {active_event.name}"
            print(badge_text)  # Replace with actual badge generation

            # Redirect to the event detail page with the active event's ID
            return redirect(url_for('event_detail', event_id=active_event.id))
        else:
            return "No active event to register for", 400  # Error response if no active event exists


@app.route('/person/<int:person_id>')
def person_detail(person_id):
    person = Person.get_or_none(Person.id == person_id)
    if person:
        events = person.events
        return render_template('person_detail.html', person=person, events=events)
    else:
        return "Person not found", 404
    

@app.route('/event/create', methods=['GET', 'POST'])
def create_event():
    if request.method == 'POST':
        name = request.form['name']
        descr = request.form['descr']
        date_str = request.form['date']
        date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')  # Parse the date string to a datetime object
        active = int(request.form.get('active', 0))

        new_event = Event.create(name=name, descr=descr, date=date, active=0)
        
        if active == 1:
            Event.set_active_event(new_event.id)
        
        return redirect(url_for('events_list'))
    
    return render_template('event_create.html')


@app.route('/persons')
def persons_list():
    # Query to get all persons and their associated events
    persons_with_events = {}

    persons = (
        Person
        .select(Person, Event)
        .join(PersonEvent, on=(Person.id == PersonEvent.person))
        .join(Event, on=(PersonEvent.event == Event.id))
        .order_by(Person.fname, Person.lname)
    )

    # Populate the dictionary by grouping persons by fname and lname
    for person in persons:
        name_key = (person.fname, person.lname)  # Grouping key

        # Initialize the entry if not exists
        if name_key not in persons_with_events:
            persons_with_events[name_key] = {
                "person": person,
                "events": []
            }

        # Append the event to the person's events list
        persons_with_events[name_key]["events"].append(person.events.get().event)

    return render_template('persons_list.html', persons_with_events=persons_with_events)




@app.route('/event/<int:event_id>')
def event_detail(event_id):
    # Retrieve the event by its ID
    event = Event.get_or_none(Event.id == event_id)
    
    if event:
        # Get all attendees for this event, ordered by fname and lname
        attendees = (
            Person
            .select()
            .join(PersonEvent, on=(Person.id == PersonEvent.person))
            .where(PersonEvent.event == event)
            .order_by(Person.fname.asc(), Person.lname.asc())
        )
        return render_template('event_detail.html', event=event, attendees=attendees)
    else:
        return "Event not found", 404




@app.route('/reset')
def reset():
    # List of all models
    models = [Person, Event, PersonEvent]

    # Drop all tables
    sqlite_db.connect()
    sqlite_db.drop_tables(models)

    # Recreate all tables
    sqlite_db.create_tables(models)




@app.teardown_appcontext
def close_db(exception):
    if not sqlite_db.is_closed():
        sqlite_db.close()

if __name__ == '__main__':
    app.run(debug=True)
