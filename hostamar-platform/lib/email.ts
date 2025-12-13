
import { trackEvent } from '@/lib/analytics'

interface EmailPayload {
  to: string;
  subject: string;
  body: string;
}

export async function sendEmail({ to, subject, body }: EmailPayload) {
  // In a real app, use Resend, SendGrid, or Nodemailer here.
  // For MVP/Dev, we log to console to ensure logic flows.
  
  console.log(`\n📧 === EMAIL SENT ===`);
  console.log(`To: ${to}`);
  console.log(`Subject: ${subject}`);
  console.log(`Body: ${body.substring(0, 50)}...`);
  console.log(`=====================\n`);

  return true;
}

export async function sendWelcomeEmail(name: string, email: string) {
  const subject = "Welcome to Hostamar! 🚀";
  const body = `
    Hi ${name},
    
    Welcome to Hostamar - the all-in-one platform for Cloud Hosting and AI Marketing Videos.
    
    We're thrilled to have you on board.
    
    To get started:
    1. Log in to your dashboard: https://hostamar.com/login
    2. Create your first video in under 60 seconds.
    
    Need help? Just reply to this email.
    
    Cheers,
    The Hostamar Team
  `;

  await sendEmail({ to: email, subject, body });
  await trackEvent(undefined, 'EMAIL_SENT', { type: 'welcome', email });
}
