import { MarketingCampaignOrchestrator } from '../index';
import { CampaignRequest } from '../types/campaign';

/**
 * Example: Email-Only Campaign
 */

async function runEmailOnlyCampaign() {
  const campaignRequest: CampaignRequest = {
    campaignId: 'camp-2026-email-only',
    campaignName: 'Email Newsletter - Product Update',
    channels: ['email'],
    
    product: {
      name: 'DataViz Studio',
      description: 'Create stunning data visualizations in minutes. No coding required. Perfect for analysts, marketers, and business professionals.',
      features: [
        'Drag-and-drop chart builder',
        'Real-time data connections',
        'Interactive dashboards',
        'Export to any format',
        'Collaboration features',
      ],
      pricing: 'Free trial, then $19/month',
    },
    
    targetAudience: {
      demographics: 'Data analysts, marketing professionals, ages 25-45',
      interests: ['Data visualization', 'Business intelligence', 'Analytics'],
      painPoints: ['Complex charting tools', 'Time-consuming report creation', 'Static visualizations'],
    },
    
    budget: 5000,
    
    timeline: {
      startDate: '2026-02-10',
      endDate: '2026-02-28',
    },
    
    goals: ['Generate 500 trial signups', 'Increase newsletter engagement'],
    
    brandVoice: 'professional',
  };

  const orchestrator = new MarketingCampaignOrchestrator();
  await orchestrator.executeCampaign(campaignRequest);
}

// Uncomment to run:
// runEmailOnlyCampaign();

export { runEmailOnlyCampaign };

