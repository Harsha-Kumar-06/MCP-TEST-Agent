import { SMSContent } from '../types/campaign';
import { Contact } from '../types/database';

/**
 * SMS Sending Agent - Multi-Provider Support
 * 
 * Supported providers (set SMS_PROVIDER in .env):
 * 
 * 1. TWILIO (default) - Most popular, requires paid account for full functionality
 *    - Sign up: https://www.twilio.com/try-twilio
 *    - Free trial: $15 credit, verified numbers only
 * 
 * 2. VONAGE (Nexmo) - Good international coverage, fewer restrictions
 *    - Sign up: https://dashboard.nexmo.com/sign-up
 *    - Free trial: €2 credit
 * 
 * 3. PLIVO - Best pricing, especially for high volume
 *    - Sign up: https://console.plivo.com/accounts/register/
 *    - Free trial: $0.50 credit
 * 
 * 4. TEXTBELT - Simplest option, no account needed
 *    - Free tier: 1 SMS/day (use key: "textbelt")
 *    - Paid tier: ~$0.05/SMS, no restrictions
 *    - Get key: https://textbelt.com/
 */

// Provider types
export type SMSProvider = 'twilio' | 'vonage' | 'plivo' | 'textbelt';

// Provider configurations
export interface TwilioConfig {
  accountSid: string;
  authToken: string;
  fromNumber: string;
}

export interface VonageConfig {
  apiKey: string;
  apiSecret: string;
  fromNumber: string;
}

export interface PlivoConfig {
  authId: string;
  authToken: string;
  fromNumber: string;
}

export interface TextbeltConfig {
  apiKey: string; // Use 'textbelt' for free tier or your paid key
}

interface SMSResult {
  success: boolean;
  messageId?: string;
  error?: string;
}

export class SMSSendingAgent {
  private provider: SMSProvider;
  private twilioClient: any = null;
  private vonageConfig: VonageConfig | null = null;
  private plivoConfig: PlivoConfig | null = null;
  private textbeltApiKey: string = '';
  private fromNumber: string = '';
  private isConfiguredFlag: boolean = false;

  constructor() {
    this.provider = (process.env.SMS_PROVIDER as SMSProvider) || 'twilio';
    console.log(`📱 SMS Provider: ${this.provider.toUpperCase()}`);
    
    this.initializeProvider();
  }

  private initializeProvider(): void {
    switch (this.provider) {
      case 'twilio':
        this.initializeTwilio();
        break;
      case 'vonage':
        this.initializeVonage();
        break;
      case 'plivo':
        this.initializePlivo();
        break;
      case 'textbelt':
        this.initializeTextbelt();
        break;
      default:
        console.log(`⚠️ Unknown SMS provider: ${this.provider}. Defaulting to dry-run mode.`);
    }
  }

  private initializeTwilio(): void {
    const accountSid = process.env.TWILIO_ACCOUNT_SID || '';
    const authToken = process.env.TWILIO_AUTH_TOKEN || '';
    this.fromNumber = process.env.TWILIO_PHONE_NUMBER || '';

    if (accountSid && authToken && this.fromNumber) {
      try {
        const twilio = require('twilio');
        this.twilioClient = twilio(accountSid, authToken);
        this.isConfiguredFlag = true;
        console.log('✅ Twilio client initialized');
      } catch (error) {
        console.warn('⚠️  Twilio not installed. Run: npm install twilio');
      }
    } else {
      console.log('⚠️ Twilio credentials not configured. SMS will be in dry-run mode.');
    }
  }

  private initializeVonage(): void {
    const apiKey = process.env.VONAGE_API_KEY || '';
    const apiSecret = process.env.VONAGE_API_SECRET || '';
    this.fromNumber = process.env.VONAGE_FROM_NUMBER || '';

    if (apiKey && apiSecret && this.fromNumber) {
      this.vonageConfig = { apiKey, apiSecret, fromNumber: this.fromNumber };
      this.isConfiguredFlag = true;
      console.log('✅ Vonage (Nexmo) configured');
    } else {
      console.log('⚠️ Vonage credentials not configured. SMS will be in dry-run mode.');
    }
  }

  private initializePlivo(): void {
    const authId = process.env.PLIVO_AUTH_ID || '';
    const authToken = process.env.PLIVO_AUTH_TOKEN || '';
    this.fromNumber = process.env.PLIVO_FROM_NUMBER || '';

    if (authId && authToken && this.fromNumber) {
      this.plivoConfig = { authId, authToken, fromNumber: this.fromNumber };
      this.isConfiguredFlag = true;
      console.log('✅ Plivo configured');
    } else {
      console.log('⚠️ Plivo credentials not configured. SMS will be in dry-run mode.');
    }
  }

  private initializeTextbelt(): void {
    // 'textbelt' is the free API key (1 SMS per day)
    // For production, use a paid key from textbelt.com
    this.textbeltApiKey = process.env.TEXTBELT_API_KEY || 'textbelt';
    this.isConfiguredFlag = true;
    console.log(`✅ Textbelt configured (key: ${this.textbeltApiKey === 'textbelt' ? 'FREE tier - 1 SMS/day' : 'Paid key'})`);
  }

  /**
   * Send SMS to a single recipient
   */
  async sendSMS(
    to: Contact,
    message: string
  ): Promise<SMSResult> {
    try {
      if (!to.phone || !to.optInSMS) {
        return {
          success: false,
          error: 'Recipient has no phone or has not opted in to SMS',
        };
      }

      if (!this.isConfiguredFlag) {
        console.log(`📱 [DRY RUN] Would send SMS to ${to.phone}: ${message}`);
        return {
          success: true,
          messageId: `dry-run-${Date.now()}`,
        };
      }

      const normalizedPhone = this.normalizePhoneNumber(to.phone);

      switch (this.provider) {
        case 'twilio':
          return await this.sendViaTwilio(normalizedPhone, message);
        case 'vonage':
          return await this.sendViaVonage(normalizedPhone, message);
        case 'plivo':
          return await this.sendViaPlivo(normalizedPhone, message);
        case 'textbelt':
          return await this.sendViaTextbelt(normalizedPhone, message);
        default:
          return { success: false, error: `Unknown provider: ${this.provider}` };
      }
    } catch (error) {
      console.error(`❌ Failed to send SMS to ${to.phone}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Send via Twilio
   */
  private async sendViaTwilio(phone: string, message: string): Promise<SMSResult> {
    if (!this.twilioClient) {
      return { success: false, error: 'Twilio client not initialized' };
    }

    const result = await this.twilioClient.messages.create({
      body: message,
      from: this.fromNumber,
      to: phone,
    });

    console.log(`✅ [Twilio] SMS sent to ${phone}: ${result.sid}`);
    return { success: true, messageId: result.sid };
  }

  /**
   * Send via Vonage (Nexmo)
   * Uses REST API directly - no SDK needed
   */
  private async sendViaVonage(phone: string, message: string): Promise<SMSResult> {
    if (!this.vonageConfig) {
      return { success: false, error: 'Vonage not configured' };
    }

    const response = await fetch('https://rest.nexmo.com/sms/json', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        api_key: this.vonageConfig.apiKey,
        api_secret: this.vonageConfig.apiSecret,
        from: this.vonageConfig.fromNumber,
        to: phone.replace('+', ''), // Vonage doesn't want the + prefix
        text: message,
      }),
    });

    const data = await response.json() as { messages: Array<{ status: string; 'message-id'?: string; 'error-text'?: string }> };

    if (data.messages && data.messages[0]?.status === '0') {
      const messageId = data.messages[0]['message-id'];
      console.log(`✅ [Vonage] SMS sent to ${phone}: ${messageId}`);
      return { success: true, messageId };
    } else {
      const error = data.messages?.[0]?.['error-text'] || 'Unknown Vonage error';
      return { success: false, error };
    }
  }

  /**
   * Send via Plivo
   * Uses REST API directly - no SDK needed
   */
  private async sendViaPlivo(phone: string, message: string): Promise<SMSResult> {
    if (!this.plivoConfig) {
      return { success: false, error: 'Plivo not configured' };
    }

    const url = `https://api.plivo.com/v1/Account/${this.plivoConfig.authId}/Message/`;
    const auth = Buffer.from(`${this.plivoConfig.authId}:${this.plivoConfig.authToken}`).toString('base64');

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Basic ${auth}`,
      },
      body: JSON.stringify({
        src: this.plivoConfig.fromNumber,
        dst: phone.replace('+', ''), // Plivo doesn't want the + prefix
        text: message,
      }),
    });

    if (response.ok) {
      const data = await response.json() as { message_uuid: string[] };
      const messageId = data.message_uuid?.[0];
      console.log(`✅ [Plivo] SMS sent to ${phone}: ${messageId}`);
      return { success: true, messageId };
    } else {
      const errorData = await response.json() as { error?: string };
      return { success: false, error: errorData.error || `HTTP ${response.status}` };
    }
  }

  /**
   * Send via Textbelt
   * Simplest option - no account required for free tier
   * Free tier: 1 SMS per day per IP
   * Paid tier: ~$0.05 per SMS, no restrictions
   */
  private async sendViaTextbelt(phone: string, message: string): Promise<SMSResult> {
    const response = await fetch('https://textbelt.com/text', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        phone: phone,
        message: message,
        key: this.textbeltApiKey,
      }),
    });

    const data = await response.json() as { success: boolean; textId?: string; error?: string; quotaRemaining?: number };

    if (data.success) {
      console.log(`✅ [Textbelt] SMS sent to ${phone}: ${data.textId} (quota remaining: ${data.quotaRemaining})`);
      return { success: true, messageId: data.textId };
    } else {
      const error = data.error || 'Unknown Textbelt error';
      console.error(`❌ [Textbelt] Failed: ${error}`);
      return { success: false, error };
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
    console.log(`\n📱 SMS SENDING AGENT [${this.provider.toUpperCase()}]: Sending to ${recipients.length} recipients...`);

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

      // Rate limiting: wait between SMS to avoid rate limits
      // Textbelt needs more delay
      const delay = this.provider === 'textbelt' ? 2000 : 1000;
      await this.delay(delay);
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
   * Check if SMS provider is configured
   */
  isConfigured(): boolean {
    return this.isConfiguredFlag;
  }

  /**
   * Get current provider name
   */
  getProvider(): SMSProvider {
    return this.provider;
  }
}
