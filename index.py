from flask import Flask, render_template, request, redirect, url_for, flash, send_file, Response
from flask_sqlalchemy import SQLAlchemy
import os
import pandas as pd


app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///entries.db'
db = SQLAlchemy(app)

# Define the Entry model
class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_date = db.Column(db.String(100))
    department = db.Column(db.String(100))
    requester = db.Column(db.String(100))
    task = db.Column(db.String(100))
    completed = db.Column(db.Boolean, default=False)



# Create the database tables
with app.app_context():
    db.create_all()



@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        request_date = request.form['request_date']
        department = request.form['department']
        requester = request.form['requester'].strip()
        task = request.form['task']
        new_entry = Entry(request_date=request_date, department=department, requester=requester, task=task)
        db.session.add(new_entry)
        db.session.commit()
    # Retrieve entries from the database
    entries = Entry.query.all()
    
    return render_template('helpdesk.html', entries=entries)


@app.route('/entries', methods=['GET'])
def entries():
    page = request.args.get('page', 1, type=int)  # Get the current page number from the URL query parameters
    entries_per_page = 10  # 최대 표시 페이지

    entries = Entry.query.all()
    entries.sort(key=lambda x: x.completed)

    # Pagination logic
    total_entries = len(entries)
    total_pages = (total_entries - 1) // entries_per_page + 1
    start_index = (page - 1) * entries_per_page
    end_index = start_index + entries_per_page
    paginated_entries = entries[start_index:end_index]

    return render_template('entries.html', entries=paginated_entries, current_page=page, total_pages=total_pages)


@app.route('/download')
def download_page():
    return render_template('download.html')


@app.route('/download_files/<filename>', methods=['GET'])
def download_file(filename):
    file_path = 'download_files/' + filename  # Replace with the actual file path on your server
    with open(file_path, 'rb') as f:
        file_data = f.read()
    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"'
    }
    return Response(file_data, headers=headers, content_type='application/octet-stream')



@app.route('/complete', methods=['POST'])
def complete():
    completed_entries = request.form.getlist('completed[]')
    delete_entries = request.form.getlist('delete[]')
    entries = Entry.query.all()

    # Check if the "delete" button was clicked
    if 'delete_btn' in request.form:
        # Delete the selected entries
        for entry_id in delete_entries:
            entry = Entry.query.get(entry_id)
            if entry:
                db.session.delete(entry)
    else:
        # Update the completed state for each entry
        for entry in entries:
            if str(entry.id) in completed_entries:
                entry.completed = True
            else:
                entry.completed = False

    db.session.commit()

    # Show flash message
    flash("Entries marked as completed and deleted successfully!", "success")

    # Redirect to entries page
    return redirect(url_for('entries'))



@app.route('/export', methods=['GET'])
def export_entries():
    entries = Entry.query.all()
    data = {
        'Completed': [entry.completed for entry in entries],
        'Request Date': [entry.request_date for entry in entries],
        'Department': [entry.department for entry in entries],
        'Requester': [entry.requester for entry in entries],
        'Task': [entry.task for entry in entries]
    }
    df = pd.DataFrame(data)
    filename = '요청현황.xlsx'
    file_path = os.path.join(app.root_path, filename)  # Absolute file path
    df.to_excel(file_path, index=False)
    return send_file(file_path, as_attachment=True)



if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5000) #web open
    # app.run(host='your_ip_address', port=5000) #web open



