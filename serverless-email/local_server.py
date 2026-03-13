from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import threading
import time
import socket
import sys

# Load environment variables
load_dotenv()

class EmailHandler(BaseHTTPRequestHandler):
    # Disable logging DNS lookups
    def address_string(self):
        return str(self.client_address[0])
    
    def log_message(self, format, *args):
        print(f"{self.client_address[0]} - {format % args}")
    
    def do_POST(self):
        response_data = {}
        status_code = 200
        
        try:
            # Get content length
            content_length = int(self.headers.get('Content-Length', 0))
            
            if content_length == 0:
                response_data = {'success': False, 'error': 'Empty request body'}
                status_code = 400
            else:
                # Read and parse data
                post_data = self.rfile.read(content_length)
                body = json.loads(post_data.decode('utf-8'))
                
                print(f"📧 Received request: {body.get('action')}")
                
                # Get email configuration
                smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
                smtp_port = int(os.getenv('SMTP_PORT', 587))
                smtp_user = os.getenv('SMTP_USER', '')
                smtp_password = os.getenv('SMTP_PASSWORD', '')
                from_email = os.getenv('FROM_EMAIL', smtp_user)
                
                # Validate credentials
                if not smtp_user or not smtp_password:
                    response_data = {'success': False, 'error': 'SMTP credentials not configured'}
                    status_code = 500
                else:
                    action = body.get('action')
                    
                    if action == 'SIGNUP_WELCOME':
                        # Send welcome email
                        to_email = body.get('email')
                        name = body.get('name')
                        user_type = body.get('user_type')
                        
                        subject = f"Welcome to HMS, {name}!"
                        html_content = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <style>
                                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                                .header {{ background-color: #3498db; color: white; padding: 20px; text-align: center; }}
                                .content {{ padding: 20px; background-color: #f9f9f9; }}
                                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <div class="header">
                                    <h1>Welcome to HMS!</h1>
                                </div>
                                <div class="content">
                                    <h2>Hello {name},</h2>
                                    <p>Thank you for registering as a <strong>{user_type}</strong>.</p>
                                    <p>You can now log in and start using the Hospital Management System.</p>
                                </div>
                                <div class="footer">
                                    <p>© 2024 Hospital Management System</p>
                                </div>
                            </div>
                        </body>
                        </html>
                        """
                        
                        result = self.send_email(smtp_host, smtp_port, smtp_user, smtp_password, 
                                               from_email, to_email, subject, html_content)
                        
                        if result['success']:
                            print(f"✅ Welcome email sent to {to_email}")
                            response_data = {'success': True, 'message': 'Welcome email sent'}
                        else:
                            print(f"❌ Failed to send welcome email: {result['error']}")
                            response_data = {'success': False, 'error': result['error']}
                            status_code = 500
                        
                    elif action == 'BOOKING_CONFIRMATION':
                        # Send confirmation email to patient
                        to_email = body.get('patient_email')
                        patient_name = body.get('patient_name')
                        doctor_name = body.get('doctor_name')
                        date = body.get('appointment_date')
                        time = body.get('appointment_time')
                        booking_id = body.get('booking_id')
                        
                        subject = f"Appointment Confirmed with Dr. {doctor_name}"
                        html_content = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <style>
                                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                                .header {{ background-color: #27ae60; color: white; padding: 20px; text-align: center; }}
                                .content {{ padding: 20px; background-color: #f9f9f9; }}
                                .details {{ background-color: white; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <div class="header">
                                    <h1>Appointment Confirmed!</h1>
                                </div>
                                <div class="content">
                                    <h2>Hello {patient_name},</h2>
                                    <p>Your appointment has been confirmed.</p>
                                    <div class="details">
                                        <h3>Details:</h3>
                                        <p><strong>Doctor:</strong> Dr. {doctor_name}</p>
                                        <p><strong>Date:</strong> {date}</p>
                                        <p><strong>Time:</strong> {time}</p>
                                        <p><strong>Booking ID:</strong> {booking_id}</p>
                                    </div>
                                </div>
                            </div>
                        </body>
                        </html>
                        """
                        
                        # Send to patient
                        result = self.send_email(smtp_host, smtp_port, smtp_user, smtp_password, 
                                               from_email, to_email, subject, html_content)
                        
                        if result['success']:
                            print(f"✅ Confirmation email sent to patient {to_email}")
                            
                            # Also send notification to doctor
                            doctor_email = body.get('doctor_email')
                            if doctor_email:
                                doctor_subject = f"New Appointment: {patient_name}"
                                doctor_html = f"""
                                <h2>New Appointment Booked</h2>
                                <p><strong>Patient:</strong> {patient_name}</p>
                                <p><strong>Date:</strong> {date}</p>
                                <p><strong>Time:</strong> {time}</p>
                                <p><strong>Booking ID:</strong> {booking_id}</p>
                                """
                                
                                doctor_result = self.send_email(smtp_host, smtp_port, smtp_user, smtp_password,
                                                              from_email, doctor_email, doctor_subject, doctor_html)
                                
                                if doctor_result['success']:
                                    print(f"✅ Notification sent to doctor {doctor_email}")
                                else:
                                    print(f"❌ Failed to send doctor notification: {doctor_result['error']}")
                            
                            response_data = {'success': True, 'message': 'Confirmation emails sent'}
                        else:
                            print(f"❌ Failed to send confirmation email: {result['error']}")
                            response_data = {'success': False, 'error': result['error']}
                            status_code = 500
                    else:
                        response_data = {'success': False, 'error': f'Unknown action: {action}'}
                        status_code = 400
        
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            response_data = {'success': False, 'error': 'Invalid JSON'}
            status_code = 400
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            response_data = {'success': False, 'error': str(e)}
            status_code = 500
        
        # Send response
        try:
            self.send_response(status_code)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Content-Length', str(len(json.dumps(response_data).encode())))
            self.end_headers()
            
            # Send response body
            self.wfile.write(json.dumps(response_data).encode())
            self.wfile.flush()
            
        except Exception as e:
            print(f"⚠️ Error sending response: {e}")
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()
    
    def send_email(self, host, port, user, password, from_email, to_email, subject, html_content):
        """Send email using SMTP with proper error handling"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = to_email
            msg.attach(MIMEText(html_content, 'html'))
            
            # Connect and send
            server = smtplib.SMTP(host, port, timeout=30)
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
            server.quit()
            
            return {'success': True}
            
        except smtplib.SMTPAuthenticationError as e:
            return {'success': False, 'error': f'SMTP Authentication failed: Check your email and app password'}
        except smtplib.SMTPException as e:
            return {'success': False, 'error': f'SMTP error: {str(e)}'}
        except socket.timeout:
            return {'success': False, 'error': 'Connection timeout'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

def run_server(port=3000):
    """Run the email server"""
    server_address = ('', port)
    
    # Allow address reuse
    httpd = HTTPServer(server_address, EmailHandler)
    httpd.allow_reuse_address = True
    
    print(f"📧 Email server running on http://localhost:{port}")
    print(f"Press Ctrl+C to stop")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
        httpd.server_close()

if __name__ == '__main__':
    run_server()