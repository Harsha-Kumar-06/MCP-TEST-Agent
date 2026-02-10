/**
 * Campaign Scheduler
 * Checks for scheduled campaigns and executes them at the right time
 */

import { campaignDB } from '../database/campaign-database';
import { contactDB } from '../database/contact-database';
import { MarketingCampaignOrchestrator } from '../index';

export class CampaignScheduler {
  private intervalId: NodeJS.Timeout | null = null;
  private isRunning = false;

  /**
   * Start the scheduler
   * Checks every minute for campaigns to execute
   */
  start() {
    if (this.isRunning) {
      console.log('⚠️  Scheduler already running');
      return;
    }

    this.isRunning = true;
    console.log('🕐 Campaign Scheduler started - checking every minute');

    // Check immediately on start
    this.checkScheduledCampaigns();

    // Then check every minute
    this.intervalId = setInterval(() => {
      this.checkScheduledCampaigns();
    }, 60 * 1000); // 60 seconds
  }

  /**
   * Stop the scheduler
   */
  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    this.isRunning = false;
    console.log('🛑 Campaign Scheduler stopped');
  }

  /**
   * Check and execute scheduled campaigns
   */
  private async checkScheduledCampaigns() {
    try {
      const scheduled = await campaignDB.getScheduledCampaigns();
      const now = new Date();

      for (const campaign of scheduled) {
        if (!campaign.scheduledAt) continue;

        const scheduledTime = new Date(campaign.scheduledAt);
        
        // Execute if scheduled time has passed
        if (scheduledTime <= now) {
          console.log(`\n⏰ Executing scheduled campaign: ${campaign.campaignName}`);
          await this.executeCampaign(campaign);
        }
      }
    } catch (error) {
      console.error('❌ Scheduler error:', error);
    }
  }

  /**
   * Execute a scheduled campaign
   */
  private async executeCampaign(campaign: any) {
    try {
      // Get contacts
      let contacts: any[] = [];
      
      if (campaign.recipientData?.singleContact) {
        contacts = [campaign.recipientData.singleContact];
      } else if (campaign.recipientData?.contactListId) {
        const list = await contactDB.getListById(campaign.recipientData.contactListId);
        if (list) {
          contacts = list.contacts;
        }
      }

      if (contacts.length === 0) {
        console.log('⚠️  No contacts found for scheduled campaign');
        await campaignDB.updateCampaign(campaign.id, { 
          status: 'failed',
          executedAt: new Date()
        });
        return;
      }

      // Execute the campaign
      const orchestrator = new MarketingCampaignOrchestrator();
      const results = await orchestrator.executeCampaignWithContacts(
        campaign.campaignData,
        contacts
      );

      // Update campaign with results
      await campaignDB.updateCampaign(campaign.id, {
        status: 'completed',
        executedAt: new Date(),
        results: {
          emailsSent: results.sendingResults?.emailResults?.sent || 0,
          emailsFailed: results.sendingResults?.emailResults?.failed || 0,
          smsSent: results.sendingResults?.smsResults?.sent || 0,
          smsFailed: results.sendingResults?.smsResults?.failed || 0,
          instagramPosts: results.sendingResults?.instagramResults?.feedPost?.success ? 1 : 0,
        },
      });

      console.log(`✅ Scheduled campaign executed: ${campaign.campaignName}`);

    } catch (error) {
      console.error(`❌ Failed to execute scheduled campaign: ${campaign.campaignName}`, error);
      
      await campaignDB.updateCampaign(campaign.id, { 
        status: 'failed',
        executedAt: new Date()
      });
    }
  }
}

// Singleton instance
export const scheduler = new CampaignScheduler();

// Auto-start scheduler (can be disabled if needed)
if (process.env.NODE_ENV !== 'test') {
  scheduler.start();
}
