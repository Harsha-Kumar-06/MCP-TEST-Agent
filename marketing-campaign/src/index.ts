import {
    CoordinatorAgent,
    EmailSendingAgent,
    InstagramPostingAgent,
    SMSSendingAgent
} from './agents';
import { CampaignRequest } from './types/campaign';
import { Contact } from './types/database';

/**
 * Main entry point for the Multi-Agent Coordinator System
 */
export class MarketingCampaignOrchestrator {
  private coordinator: CoordinatorAgent;

  constructor() {
    this.coordinator = new CoordinatorAgent();
  }

  /**
   * Execute a marketing campaign using the multi-agent coordinator pattern
   */
  async executeCampaign(request: CampaignRequest): Promise<void> {
    console.log('\n' + '='.repeat(60));
    console.log('🚀 MULTI-AGENT COORDINATOR SYSTEM');
    console.log('   Marketing Campaign Automation');
    console.log('='.repeat(60));
    console.log(`\nCampaign: ${request.campaignName}`);
    console.log(`ID: ${request.campaignId}`);
    console.log(`Channels: ${request.channels.join(', ').toUpperCase()}`);
    console.log(`Budget: $${request.budget.toLocaleString()}`);
    console.log(`Timeline: ${request.timeline.startDate} to ${request.timeline.endDate}`);
    console.log('='.repeat(60));

    try {
      // Execute campaign through coordinator
      const results = await this.coordinator.coordinate(request);

      // Display results
      this.displayResults(results);

      console.log('\n' + this.coordinator.getSummary());

    } catch (error) {
      console.error('\n❌ Campaign execution failed:', error);
      throw error;
    }
  }

  /**
   * Display campaign results in a user-friendly format
   */
  private displayResults(results: Map<string, any>): void {
    console.log('\n' + '='.repeat(60));
    console.log('📋 CAMPAIGN RESULTS');
    console.log('='.repeat(60));

    // Audience Segmentation Results
    const audienceResult = results.get('audience-segmentation');
    if (audienceResult?.success) {
      console.log('\n👥 Audience Segments:');
      audienceResult.data.segments.forEach((seg: any) => {
        console.log(`   • ${seg.segmentName}: ${seg.estimatedSize.toLocaleString()} contacts`);
      });
    }

    // Email Content Results
    const emailResult = results.get('email-content');
    if (emailResult?.success) {
      console.log('\n✉️  Email Campaign:');
      console.log(`   Subject: ${emailResult.data.emailContent.subjectLine}`);
      console.log(`   CTA: ${emailResult.data.emailContent.cta.text}`);
      console.log(`   A/B Variants: ${emailResult.data.emailContent.variants.length}`);
    }

    // SMS Content Results
    const smsResult = results.get('sms-content');
    if (smsResult?.success) {
      console.log('\n📱 SMS Campaign:');
      console.log(`   Message: ${smsResult.data.smsContent.message}`);
      console.log(`   Length: ${smsResult.data.smsContent.characterCount} chars`);
      console.log(`   Segments: ${smsResult.data.smsContent.segmentCount} SMS`);
    }

    // Compliance Results
    const complianceResult = results.get('compliance');
    if (complianceResult?.success) {
      const check = complianceResult.data.complianceCheck;
      console.log(`\n⚖️  Compliance: ${check.passed ? '✅ PASSED' : '⚠️ ISSUES FOUND'}`);
      console.log(`   Issues: ${check.issues.length}`);
      console.log(`   Recommendations: ${check.recommendations.length}`);
    }

    // Analytics Results
    const analyticsResult = results.get('analytics-setup');
    if (analyticsResult?.success) {
      console.log('\n📊 Analytics:');
      console.log(`   UTM Campaign: ${analyticsResult.data.analyticsSetup.utmParameters.campaign}`);
      console.log(`   Conversion Goals: ${analyticsResult.data.analyticsSetup.conversionGoals.length}`);
      console.log(`   Dashboard: ${analyticsResult.data.analyticsSetup.dashboardUrl}`);
    }

    console.log('\n' + '='.repeat(60));
  }

  /**
   * Execute campaign with actual contacts and send emails/SMS
   */
  async executeCampaignWithContacts(
    request: CampaignRequest,
    contacts: Contact[]
  ): Promise<any> {
    console.log('\n' + '='.repeat(60));
    console.log('🚀 EXECUTING CAMPAIGN WITH CONTACTS');
    console.log('='.repeat(60));
    console.log(`Campaign: ${request.campaignName}`);
    console.log(`Recipients: ${contacts.length}`);
    console.log(`Channels: ${request.channels.join(', ')}`);
    console.log('='.repeat(60));

    try {
      // Step 1: Generate content and prepare campaign
      const results = await this.coordinator.coordinate(request);

      // Step 2: Send to actual recipients
      const sendingResults: any = {
        emailResults: null,
        smsResults: null,
      };

      // Filter contacts by opt-in
      const emailRecipients = contacts.filter(c => c.email && c.optInEmail);
      const smsRecipients = contacts.filter(c => c.phone && c.optInSMS);

      console.log(`\n📊 Recipient Summary:`);
      console.log(`   Email recipients: ${emailRecipients.length}`);
      console.log(`   SMS recipients: ${smsRecipients.length}`);

      // Send Emails
      if (request.channels.includes('email') && emailRecipients.length > 0) {
        const emailContent = results.get('email-content')?.data?.emailContent;
        if (emailContent) {
          const emailAgent = new EmailSendingAgent();
          
          // Verify connection first
          const connected = await emailAgent.verifyConnection();
          if (connected) {
            sendingResults.emailResults = await emailAgent.sendBulkEmails(
              emailRecipients,
              emailContent,
              request.campaignId // Pass campaignId for tracking
            );
          } else {
            console.warn('⚠️  Email sending skipped - SMTP not configured');
          }
        }
      }

      // Send SMS
      if (request.channels.includes('sms') && smsRecipients.length > 0) {
        const smsContent = results.get('sms-content')?.data?.smsContent;
        if (smsContent) {
          const smsAgent = new SMSSendingAgent();
          
          if (smsAgent.isConfigured()) {
            sendingResults.smsResults = await smsAgent.sendBulkSMS(
              smsRecipients,
              smsContent
            );
          } else {
            console.warn('⚠️  SMS sending skipped - Twilio not configured');
            console.log('   To enable SMS: Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER');
          }
        }
      }

      // Post to Instagram
      if (request.channels.includes('instagram')) {
        const instagramAgent = new InstagramPostingAgent();
        
        if (instagramAgent.isConfigured()) {
          console.log('\n📸 Executing Instagram campaign...');
          sendingResults.instagramResults = await instagramAgent.executeCampaign(request);
        } else {
          console.warn('⚠️  Instagram posting skipped - Not configured');
          console.log('   To enable Instagram: Set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID');
          sendingResults.instagramResults = {
            feedPost: { success: false, error: 'Not configured' },
            story: { success: false, error: 'Not configured' },
          };
        }
      }

      console.log('\n' + '='.repeat(60));
      console.log('📊 CAMPAIGN EXECUTION SUMMARY');
      console.log('='.repeat(60));
      
      if (sendingResults.emailResults) {
        console.log(`\n✉️  Email Results:`);
        console.log(`   Sent: ${sendingResults.emailResults.sent}`);
        console.log(`   Failed: ${sendingResults.emailResults.failed}`);
      }
      
      if (sendingResults.smsResults) {
        console.log(`\n📱 SMS Results:`);
        console.log(`   Sent: ${sendingResults.smsResults.sent}`);
        console.log(`   Failed: ${sendingResults.smsResults.failed}`);
      }

      if (sendingResults.instagramResults) {
        console.log(`\n📸 Instagram Results:`);
        if (sendingResults.instagramResults.feedPost?.success) {
          console.log(`   ✅ Feed Post: Published`);
        }
        if (sendingResults.instagramResults.story?.success) {
          console.log(`   ✅ Story: Published`);
        }
      }

      console.log('\n' + '='.repeat(60));

      return {
        campaignResults: results,
        sendingResults,
      };

    } catch (error) {
      console.error('\n❌ Campaign execution failed:', error);
      throw error;
    }
  }
}

// Export for use in other modules
export * from './agents/coordinator-agent';
export * from './types/campaign';
export * from './types/database';

