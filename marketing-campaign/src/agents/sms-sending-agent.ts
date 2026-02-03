import { SMSContent } from '../types/campaign';
import { Contact } from '../types/database';

/**
 * SMS Sending Agent using Twilio
 * 
 * Twilio Free Trial:
 * - Sign up at https://www.twilio.com/try-twilio
 * - Get $15 credit (enough for ~500 SMS)
 * - Verify your phone number
 */

export interface TwilioConfig {
  accountSid: string;
  authToken: string;
  fromNumber: string;
}

export class SMSSendingAgent {
  private accountSid: string;
  private authToken: string;
  private fromNumber: string;
  private twilioClient: any;

  constructor(config?: TwilioConfig) {
    this.accountSid = config?.accountSid || process.env.TWILIO_ACCOUNT_SID || '';
    this.authToken = config?.authToken || process.env.TWILIO_AUTH_TOKEN || '';
    this.fromNumber = config?.fromNumber || process.env.TWILIO_PHONE_NUMBER || '';

    // Only initialize Twilio if credentials are provided
    if (this.accountSid && this.authToken) {
      try {
        // Dynamic import to avoid errors if twilio is not installed
        const twilio = require('twilio');
        this.twilioClient = twilio(this.accountSid, this.authToken);
      } catch (error) {
        console.warn('⚠️  Twilio not installed. Run: npm install twilio');
      }
    }
  }

  /**
   * Send SMS to a single recipient
   */
  async sendSMS(
    to: Contact,
    message: string
  ): Promise<{ success: boolean; messageId?: string; error?: string }> {
    try {
      if (!to.phone || !to.optInSMS) {
        return {
          success: false,
          error: 'Recipient has no phone or has not opted in to SMS',
        };
      }

      if (!this.twilioClient) {
        console.log(`📱 [DRY RUN] Would send SMS to ${to.phone}: ${message}`);
        return {
          success: true,
          messageId: `dry-run-${Date.now()}`,
        };
      }

      // Normalize phone number (must include country code)
      const normalizedPhone = this.normalizePhoneNumber(to.phone);

      const result = await this.twilioClient.messages.create({
        body: message,
        from: this.fromNumber,
        to: normalizedPhone,
      });

      console.log(`✅ SMS sent to ${to.phone}: ${result.sid}`);

      return {
        success: true,
        messageId: result.sid,
      };
    } catch (error) {
      console.error(`❌ Failed to send SMS to ${to.phone}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Send SMS to multiple recipients (batch)
   */
  async sendBulkSMS(
    recipients: Contact[],
    smsContent: SMSContent
  ): Promise<{
    sent: number;
    failed: number;
    results: Array<{ contact: Contact; success: boolean; error?: string }>;
  }> {
    console.log(`\n📱 SMS SENDING AGENT: Sending to ${recipients.length} recipients...`);

    const results: Array<{ contact: Contact; success: boolean; error?: string }> = [];
    let sent = 0;
    let failed = 0;

    for (const recipient of recipients) {
      if (!recipient.phone || !recipient.optInSMS) {
        results.push({
          contact: recipient,
          success: false,
          error: 'No phone or not opted in to SMS',
        });
        failed++;
        continue;
      }

      // Personalize message
      const personalizedMessage = this.personalizeContent(smsContent.message, recipient);

      const result = await this.sendSMS(recipient, personalizedMessage);

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

      // Rate limiting: wait 1 second between SMS to avoid rate limits
      await this.delay(1000);
    }

    console.log(`\n📊 SMS Results: ${sent} sent, ${failed} failed`);

    return { sent, failed, results };
  }

  /**
   * Personalize SMS content with recipient data
   */
  private personalizeContent(content: string, recipient: Contact): string {
    let personalized = content;

    personalized = personalized.replace(/\{\{firstName\}\}/g, recipient.firstName || 'there');
    personalized = personalized.replace(/\{\{lastName\}\}/g, recipient.lastName || '');
    personalized = personalized.replace(/\{\{company\}\}/g, recipient.company || '');

    return personalized;
  }

  /**
   * Normalize phone number to E.164 format
   */
  private normalizePhoneNumber(phone: string): string {
    // Remove all non-digit characters
    let normalized = phone.replace(/\D/g, '');

    // Add country code if missing (assuming US +1)
    if (!normalized.startsWith('1') && normalized.length === 10) {
      normalized = '1' + normalized;
    }

    return '+' + normalized;
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Check if Twilio is configured
   */
  isConfigured(): boolean {
    return !!(this.accountSid && this.authToken && this.fromNumber);
  }
}
