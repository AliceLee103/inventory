"""Main Flask application for inventory management system."""
from flask import Flask, render_template, request, redirect, url_for, flash, g
from flask_mail import Mail, Message
from config import Config
from database import get_db, close_connection, init_db
import os
import sqlite3

app = Flask(__name__)
app.config.from_object(Config)
mail = Mail(app)

# Register database teardown
app.teardown_appcontext(close_connection)


@app.route('/')
def index():
    """Home page."""
    return render_template('index.html')


@app.route('/assets')
def list_assets():
    """List all assets."""
    db = get_db()
    assets = db.execute('SELECT * FROM assets ORDER BY created_at DESC').fetchall()
    return render_template('assets.html', assets=assets)


@app.route('/assets/add', methods=['GET', 'POST'])
def add_asset():
    """Form to add a new asset."""
    if request.method == 'POST':
        serial_number = request.form['serial_number']
        device_type = request.form['device_type']
        model = request.form['model']
        
        db = get_db()
        try:
            db.execute(
                'INSERT INTO assets (serial_number, device_type, model) VALUES (?, ?, ?)',
                (serial_number, device_type, model)
            )
            db.commit()
            flash('Asset added successfully!', 'success')
            return redirect(url_for('list_assets'))
        except sqlite3.IntegrityError:
            flash('Error: Serial number already exists!', 'error')
    
    return render_template('add_asset.html')


@app.route('/assets/update/<int:asset_id>', methods=['GET', 'POST'])
def update_asset(asset_id):
    """Form to update an existing asset."""
    db = get_db()
    
    if request.method == 'POST':
        device_type = request.form['device_type']
        model = request.form['model']
        
        db.execute(
            'UPDATE assets SET device_type = ?, model = ? WHERE id = ?',
            (device_type, model, asset_id)
        )
        db.commit()
        flash('Asset updated successfully!', 'success')
        return redirect(url_for('list_assets'))
    
    asset = db.execute('SELECT * FROM assets WHERE id = ?', (asset_id,)).fetchone()
    return render_template('update_asset.html', asset=asset)


@app.route('/associates')
def list_associates():
    """List all associates."""
    db = get_db()
    associates = db.execute('SELECT * FROM associates ORDER BY created_at DESC').fetchall()
    return render_template('associates.html', associates=associates)


@app.route('/associates/add', methods=['GET', 'POST'])
def add_associate():
    """Form to add a new associate."""
    if request.method == 'POST':
        user_id = request.form['user_id']
        department = request.form['department']
        job_title = request.form['job_title']
        email = request.form['email']
        
        db = get_db()
        try:
            db.execute(
                'INSERT INTO associates (user_id, department, job_title, email) VALUES (?, ?, ?, ?)',
                (user_id, department, job_title, email)
            )
            db.commit()
            flash('Associate added successfully!', 'success')
            return redirect(url_for('list_associates'))
        except sqlite3.IntegrityError:
            flash('Error: User ID already exists!', 'error')
    
    return render_template('add_associate.html')


@app.route('/associates/update/<int:associate_id>', methods=['GET', 'POST'])
def update_associate(associate_id):
    """Form to update an existing associate."""
    db = get_db()
    
    if request.method == 'POST':
        department = request.form['department']
        job_title = request.form['job_title']
        email = request.form['email']
        
        db.execute(
            'UPDATE associates SET department = ?, job_title = ?, email = ? WHERE id = ?',
            (department, job_title, email, associate_id)
        )
        db.commit()
        flash('Associate updated successfully!', 'success')
        return redirect(url_for('list_associates'))
    
    associate = db.execute('SELECT * FROM associates WHERE id = ?', (associate_id,)).fetchone()
    return render_template('update_associate.html', associate=associate)


@app.route('/assignments')
def list_assignments():
    """List all device assignments."""
    db = get_db()
    assignments = db.execute('''
        SELECT 
            assignments.id,
            assets.serial_number,
            assets.device_type,
            assets.model,
            associates.user_id,
            associates.department,
            associates.job_title,
            assignments.assigned_date,
            assignments.status
        FROM assignments
        JOIN assets ON assignments.asset_id = assets.id
        JOIN associates ON assignments.associate_id = associates.id
        WHERE assignments.status = 'active'
        ORDER BY assignments.assigned_date DESC
    ''').fetchall()
    return render_template('assignments.html', assignments=assignments)


@app.route('/transfer', methods=['GET', 'POST'])
def transfer_device():
    """Form to transfer a device between users."""
    db = get_db()
    
    if request.method == 'POST':
        asset_id = request.form['asset_id']
        from_associate_id = request.form.get('from_associate_id')
        to_associate_id = request.form['to_associate_id']
        notes = request.form.get('notes', '')
        
        # Create transfer request
        db.execute('''
            INSERT INTO transfer_requests 
            (asset_id, from_associate_id, to_associate_id, notes)
            VALUES (?, ?, ?, ?)
        ''', (asset_id, from_associate_id if from_associate_id else None, to_associate_id, notes))
        db.commit()
        
        transfer_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        # Send notification emails
        send_transfer_notifications(transfer_id)
        
        flash('Transfer request created! Notification emails have been sent.', 'success')
        return redirect(url_for('list_transfers'))
    
    # Get available assets and associates for the form
    assets = db.execute('SELECT * FROM assets ORDER BY serial_number').fetchall()
    associates = db.execute('SELECT * FROM associates ORDER BY user_id').fetchall()
    
    # Get current assignments to show who currently has each device
    current_assignments = db.execute('''
        SELECT 
            assets.id as asset_id,
            associates.id as associate_id,
            associates.user_id
        FROM assignments
        JOIN assets ON assignments.asset_id = assets.id
        JOIN associates ON assignments.associate_id = associates.id
        WHERE assignments.status = 'active'
    ''').fetchall()
    
    assignment_map = {a['asset_id']: a for a in current_assignments}
    
    return render_template('transfer_device.html', 
                         assets=assets, 
                         associates=associates,
                         assignment_map=assignment_map)


@app.route('/transfers')
def list_transfers():
    """List all transfer requests."""
    db = get_db()
    transfers = db.execute('''
        SELECT 
            transfer_requests.id,
            assets.serial_number,
            assets.device_type,
            from_assoc.user_id as from_user,
            to_assoc.user_id as to_user,
            transfer_requests.requested_date,
            transfer_requests.transferer_approval,
            transfer_requests.transferee_approval,
            transfer_requests.it_approval,
            transfer_requests.status
        FROM transfer_requests
        JOIN assets ON transfer_requests.asset_id = assets.id
        LEFT JOIN associates as from_assoc ON transfer_requests.from_associate_id = from_assoc.id
        JOIN associates as to_assoc ON transfer_requests.to_associate_id = to_assoc.id
        ORDER BY transfer_requests.requested_date DESC
    ''').fetchall()
    return render_template('transfers.html', transfers=transfers)


@app.route('/transfer/approve/<int:transfer_id>/<approval_type>/<action>')
def approve_transfer(transfer_id, approval_type, action):
    """Approve or reject a transfer request."""
    db = get_db()
    
    # Use a whitelist mapping to prevent SQL injection
    approval_columns = {
        'transferer': 'transferer_approval',
        'transferee': 'transferee_approval',
        'it': 'it_approval'
    }
    
    if approval_type in approval_columns:
        column = approval_columns[approval_type]
        db.execute(
            f'UPDATE transfer_requests SET {column} = ? WHERE id = ?',
            (action, transfer_id)
        )
        db.commit()
        
        # Check if all approvals are complete
        transfer = db.execute(
            'SELECT * FROM transfer_requests WHERE id = ?', 
            (transfer_id,)
        ).fetchone()
        
        if (transfer['transferer_approval'] == 'approved' and 
            transfer['transferee_approval'] == 'approved' and 
            transfer['it_approval'] == 'approved'):
            
            # Complete the transfer
            complete_transfer(transfer_id)
            flash('Transfer completed successfully!', 'success')
        elif action == 'rejected':
            db.execute(
                'UPDATE transfer_requests SET status = ? WHERE id = ?',
                ('rejected', transfer_id)
            )
            db.commit()
            flash('Transfer request rejected.', 'info')
        else:
            flash(f'{approval_type.capitalize()} approval recorded.', 'success')
    
    return redirect(url_for('list_transfers'))


def complete_transfer(transfer_id):
    """Complete a transfer after all approvals."""
    db = get_db()
    transfer = db.execute(
        'SELECT * FROM transfer_requests WHERE id = ?', 
        (transfer_id,)
    ).fetchone()
    
    # Deactivate old assignment if exists
    if transfer['from_associate_id']:
        db.execute(
            'UPDATE assignments SET status = ? WHERE asset_id = ? AND status = ?',
            ('inactive', transfer['asset_id'], 'active')
        )
    
    # Create new assignment
    db.execute(
        'INSERT INTO assignments (asset_id, associate_id) VALUES (?, ?)',
        (transfer['asset_id'], transfer['to_associate_id'])
    )
    
    # Update transfer request status
    db.execute(
        'UPDATE transfer_requests SET status = ? WHERE id = ?',
        ('completed', transfer_id)
    )
    
    db.commit()


def send_transfer_notifications(transfer_id):
    """Send notification emails for transfer approval."""
    db = get_db()
    
    # Get transfer details
    transfer = db.execute('''
        SELECT 
            transfer_requests.*,
            assets.serial_number,
            assets.device_type,
            assets.model,
            from_assoc.user_id as from_user,
            from_assoc.email as from_email,
            to_assoc.user_id as to_user,
            to_assoc.email as to_email
        FROM transfer_requests
        JOIN assets ON transfer_requests.asset_id = assets.id
        LEFT JOIN associates as from_assoc ON transfer_requests.from_associate_id = from_assoc.id
        JOIN associates as to_assoc ON transfer_requests.to_associate_id = to_assoc.id
        WHERE transfer_requests.id = ?
    ''', (transfer_id,)).fetchone()
    
    device_info = f"{transfer['device_type']} {transfer['model']} (SN: {transfer['serial_number']})"
    # Use url_for with _external=True to avoid Host header injection
    base_url = url_for('index', _external=True).rstrip('/')
    
    # Email to transferer (current owner)
    if transfer['from_email']:
        msg = Message(
            'Device Transfer Request - Approval Needed',
            recipients=[transfer['from_email']]
        )
        msg.body = f'''
A transfer request has been created for device: {device_info}

From: {transfer['from_user']}
To: {transfer['to_user']}

Please approve or reject this transfer:
Approve: {base_url}/transfer/approve/{transfer_id}/transferer/approved
Reject: {base_url}/transfer/approve/{transfer_id}/transferer/rejected

Notes: {transfer['notes'] or 'None'}
'''
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Failed to send email to transferer: {e}")
    
    # Email to transferee (new owner)
    if transfer['to_email']:
        msg = Message(
            'Device Transfer Request - Approval Needed',
            recipients=[transfer['to_email']]
        )
        msg.body = f'''
A device is being transferred to you: {device_info}

From: {transfer['from_user'] or 'Unassigned'}
To: {transfer['to_user']}

Please approve or reject this transfer:
Approve: {base_url}/transfer/approve/{transfer_id}/transferee/approved
Reject: {base_url}/transfer/approve/{transfer_id}/transferee/rejected

Notes: {transfer['notes'] or 'None'}
'''
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Failed to send email to transferee: {e}")
    
    # Email to IT department
    msg = Message(
        'Device Transfer Request - IT Approval Needed',
        recipients=[app.config['IT_DEPARTMENT_EMAIL']]
    )
    msg.body = f'''
A device transfer request requires IT approval: {device_info}

From: {transfer['from_user'] or 'Unassigned'}
To: {transfer['to_user']}

Please approve or reject this transfer:
Approve: {base_url}/transfer/approve/{transfer_id}/it/approved
Reject: {base_url}/transfer/approve/{transfer_id}/it/rejected

Notes: {transfer['notes'] or 'None'}
'''
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send email to IT: {e}")


if __name__ == '__main__':
    # Initialize database if it doesn't exist
    if not os.path.exists(app.config['DATABASE']):
        init_db()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
