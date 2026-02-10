import * as nodemailer from 'nodemailer';
import { EmailContent } from '../types/campaign';
import { Contact } from '../types/database';

/**
 * Email Sending Agent using Gmail SMTP
 */

export interface EmailConfig {
  host: string;
  port: number;
  secure: boolean;
  auth: {
    user: string;
    pass: string;
  };
}

export class EmailSendingAgent {
  private transporter: nodemailer.Transporter;
  private fromEmail: string;
  private fromName: string;

  constructor(config?: EmailConfig) {
    const emailConfig = config || {
      host: 'smtp.gmail.com',
      port: 587,
      secure: false,
      auth: {
        user: process.env.GMAIL_USER || '',
        pass: process.env.GMAIL_APP_PASSWORD || '', // Use App Password, not regular password
      },
    };

    this.fromEmail = emailConfig.auth.user;
    this.fromName = process.env.FROM_NAME || 'Marketing Team';

    this.transporter = nodemailer.createTransport(emailConfig);
  }

  /**
   * Send email to a single recipient
   */
  async sendEmail(
    to: Contact,
    subject: string,
    htmlContent: string,
    textContent: string
  ): Promise<{ success: boolean; messageId?: string; error?: string }> {
    try {
      if (!to.email || !to.optInEmail) {
        return {
          success: false,
          error: 'Recipient has no email or has not opted in',
        };
      }

      const info = await this.transporter.sendMail({
        from: `"${this.fromName}" <${this.fromEmail}>`,
        replyTo: this.fromEmail, // Enable direct replies
        to: to.email,
        subject: subject,
        text: textContent,
        html: htmlContent,
      });

      console.log(`✅ Email sent to ${to.email}: ${info.messageId}`);

      return {
        success: true,
        messageId: info.messageId,
      };
    } catch (error) {
      console.error(`❌ Failed to send email to ${to.email}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Send emails to multiple recipients (batch) with tracking
   */
  async sendBulkEmails(
    recipients: Contact[],
    emailContent: EmailContent,
    campaignId?: string
  ): Promise<{
    sent: number;
    failed: number;
    results: Array<{ contact: Contact; success: boolean; error?: string }>;
  }> {
    console.log(`\n📧 EMAIL SENDING AGENT: Sending to ${recipients.length} recipients...`);

    const results: Array<{ contact: Contact; success: boolean; error?: string }> = [];
    let sent = 0;
    let failed = 0;

    // Import EmailContentAgent for tracking injection
    const { EmailContentAgent } = await import('./email-content-agent');
    const emailContentAgent = new EmailContentAgent();

    // Send emails with rate limiting (to avoid Gmail limits)
    for (const recipient of recipients) {
      if (!recipient.email || !recipient.optInEmail) {
        results.push({
          contact: recipient,
          success: false,
          error: 'No email or not opted in',
        });
        failed++;
        continue;
      }

      // Personalize subject and text
      const personalizedSubject = this.personalizeContent(emailContent.subjectLine, recipient);
      const personalizedText = this.personalizeContent(emailContent.bodyText, recipient);
      
      // Generate tracking-enabled HTML for this specific recipient
      let personalizedHtml = this.personalizeContent(emailContent.bodyHtml, recipient);
      if (campaignId && recipient.id) {
        // Use EmailContentAgent to inject tracking
        personalizedHtml = emailContentAgent.injectTrackingIntoHtml(
          personalizedHtml,
          recipient.email,
          campaignId,
          recipient.id
        );
      }
      
      // Apply standard personalization tokens
      personalizedHtml = this.personalizeContent(personalizedHtml, recipient);

      const result = await this.sendEmail(
        recipient,
        personalizedSubject,
        personalizedHtml,
        personalizedText
      );

      results.push({
        contact: recipient,
        success: result.success,
        error: result.error,
      });

      if (result.success) {
        sent++;
      } else {
        failed++;
      }

      // Rate limiting: wait 100ms between emails to avoid Gmail rate limits
      await this.delay(100);
    }

    console.log(`\n📊 Email Results: ${sent} sent, ${failed} failed`);

    return { sent, failed, results };
  }

  /**
   * Personalize email content with recipient data
   */
  private personalizeContent(content: string, recipient: Contact): string {
    let personalized = content;

    personalized = personalized.replace(/\{\{firstName\}\}/g, recipient.firstName || 'there');
    personalized = personalized.replace(/\{\{lastName\}\}/g, recipient.lastName || '');
    personalized = personalized.replace(/\{\{email\}\}/g, recipient.email || '');
    personalized = personalized.replace(/\{\{company\}\}/g, recipient.company || '');

    return personalized;
  }

  /**
   * Verify SMTP connection
   */
  async verifyConnection(): Promise<boolean> {
    try {
      await this.transporter.verify();
      console.log('✅ SMTP connection verified');
      return true;
    } catch (error) {
      console.error('❌ SMTP connection failed:', error);
      return false;
    }
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
