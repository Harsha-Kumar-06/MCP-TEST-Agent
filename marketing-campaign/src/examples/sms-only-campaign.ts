import { MarketingCampaignOrchestrator } from '../index';
import { CampaignRequest } from '../types/campaign';

/**
 * Example: SMS-Only Campaign (High-urgency, time-sensitive)
 */

async function runSMSOnlyCampaign() {
  const campaignRequest: CampaignRequest = {
    campaignId: 'camp-2026-sms-flash',
    campaignName: 'Flash Sale - 24 Hour SMS Blast',
    channels: ['sms'],
    
    product: {
      name: 'CloudStorage Plus',
      description: 'Secure cloud storage with unlimited bandwidth. 24-hour flash sale: 50% off annual plans!',
      features: [
        'Unlimited bandwidth',
        'Military-grade encryption',
        'Automatic backup',
        '99.9% uptime guarantee',
      ],
      pricing: '50% OFF - Today only!',
    },
    
    targetAudience: {
      demographics: 'Existing customers and warm leads',
      interests: ['Cloud storage', 'Data security', 'Remote work'],
      painPoints: ['Expensive storage plans', 'Slow upload speeds', 'Security concerns'],
    },
    
    budget: 3000,
    
    timeline: {
      startDate: '2026-02-05',
      endDate: '2026-02-06',
    },
    
    goals: ['Drive immediate sales', 'Convert warm leads to customers'],
    
    brandVoice: 'casual',
  };

  const orchestrator = new MarketingCampaignOrchestrator();
  await orchestrator.executeCampaign(campaignRequest);
}

// Uncomment to run:
// runSMSOnlyCampaign();

export { runSMSOnlyCampaign };

