import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def lambda_handler(event, context):
    try:
        body = json.loads(event['body']) if 'body' in event else event
        action = body.get('action')
        
        smtp_user = os.environ.get('SMTP_USER', '')
        smtp_password = os.environ.get('SMTP_PASSWORD', '')
        
        if action == 'SIGNUP_WELCOME':
            send_email(
                body['email'],
                f"Welcome to HMS, {body['name']}!",
                f"<h2>Welcome {body['name']}!</h2><p>You registered as a {body['user_type']}.</p>"
            )
        elif action == 'BOOKING_CONFIRMATION':
            send_email(
                body['patient_email'],
                f"Appointment Confirmed",
                f"<h2>Appointment Confirmed</h2><p>With Dr. {body['doctor_name']} on {body['appointment_date']}</p>"
            )
        
        return {'statusCode': 200, 'body': json.dumps({'success': True})}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}

def send_email(to_email, subject, html):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = os.environ.get('FROM_EMAIL')
    msg['To'] = to_email
    msg.attach(MIMEText(html, 'html'))
    
    server = smtplib.SMTP(os.environ.get('SMTP_HOST'), int(os.environ.get('SMTP_PORT')))
    server.starttls()
    server.login(os.environ.get('SMTP_USER'), os.environ.get('SMTP_PASSWORD'))
    server.send_message(msg)
    server.quit()