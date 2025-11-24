# Inventory Management System

A comprehensive Flask-based inventory management system for tracking assets, associates, and device assignments with an approval workflow for device transfers.

## Features

1. **Asset Management** - Database for device inventory with serial numbers, device types, and models
2. **Associate Management** - Database for employees with user IDs, departments, and job titles
3. **Assignment Tracking** - Main database that maps which devices are assigned to which associates
4. **Device Transfer** - Form to transfer devices between users with approval workflow
5. **Asset Entry Management** - Form to add and update assets when purchasing new devices
6. **Associate Management** - Form to add and update employee information
7. **Email Notifications** - Automatic email notifications sent to transferer, transferee, and IT department for approval

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize the database:
```bash
python database.py
```

3. Configure email settings (optional, for notifications):
```bash
export MAIL_SERVER=smtp.gmail.com
export MAIL_PORT=587
export MAIL_USE_TLS=true
export MAIL_USERNAME=your-email@gmail.com
export MAIL_PASSWORD=your-app-password
export IT_DEPARTMENT_EMAIL=it@company.com
```

## Running the Application

Start the Flask development server:
```bash
python app.py
```

The application will be available at http://localhost:5000

## Usage

### Managing Assets
- Navigate to **Assets** to view all devices
- Click **Add New Asset** to register new devices
- Click **Edit** to update device information

### Managing Associates
- Navigate to **Associates** to view all employees
- Click **Add New Associate** to register new employees
- Click **Edit** to update employee information

### Viewing Assignments
- Navigate to **Assignments** to see current device-to-employee mappings

### Transferring Devices
1. Navigate to **Transfer Device**
2. Select the device to transfer
3. Select the current owner (if any) and the new owner
4. Add optional notes
5. Submit the transfer request
6. Email notifications will be sent to all parties for approval
7. All three parties (transferer, transferee, IT) must approve
8. Once approved, the assignment is automatically updated

### Managing Transfer Requests
- Navigate to **Transfer Requests** to view all pending and completed transfers
- Use the approval buttons to approve or reject transfers

## Database Schema

### Assets Table
- `id`: Primary key
- `serial_number`: Unique serial number
- `device_type`: Type of device (e.g., Laptop, Desktop)
- `model`: Device model
- `created_at`: Timestamp

### Associates Table
- `id`: Primary key
- `user_id`: Unique user identifier
- `department`: Employee department
- `job_title`: Job title
- `email`: Email address for notifications
- `created_at`: Timestamp

### Assignments Table
- `id`: Primary key
- `asset_id`: Foreign key to assets
- `associate_id`: Foreign key to associates
- `assigned_date`: Timestamp
- `status`: active/inactive

### Transfer Requests Table
- `id`: Primary key
- `asset_id`: Foreign key to assets
- `from_associate_id`: Foreign key to current owner
- `to_associate_id`: Foreign key to new owner
- `requested_date`: Timestamp
- `transferer_approval`: pending/approved/rejected
- `transferee_approval`: pending/approved/rejected
- `it_approval`: pending/approved/rejected
- `status`: pending/completed/rejected
- `notes`: Optional notes

## Configuration

Configuration is managed in `config.py`. You can override settings using environment variables:

- `SECRET_KEY`: Flask secret key
- `MAIL_SERVER`: Email server hostname
- `MAIL_PORT`: Email server port
- `MAIL_USE_TLS`: Enable TLS (true/false)
- `MAIL_USERNAME`: Email account username
- `MAIL_PASSWORD`: Email account password
- `MAIL_DEFAULT_SENDER`: Default sender email
- `IT_DEPARTMENT_EMAIL`: IT department email for approvals