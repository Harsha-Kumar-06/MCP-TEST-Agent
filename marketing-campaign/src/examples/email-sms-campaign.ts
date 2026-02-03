import { MarketingCampaignOrchestrator } from '../index';
import { CampaignRequest } from '../types/campaign';

/**
 * Example: Email + SMS Marketing Campaign
 * 
 * This demonstrates the multi-agent coordinator pattern in action.
 * The coordinator will dynamically route tasks to specialized agents.
 */

async function runEmailSMSCampaign() {
  // Define campaign request
  const campaignRequest: CampaignRequest = {
    campaignId: 'camp-2026-q1-001',
    campaignName: 'Q1 Product Launch - Email & SMS',
    channels: ['email', 'sms'],
    
    product: {
      name: 'TaskFlow Pro',
      description: 'AI-powered project management tool that helps teams collaborate more effectively and ship faster. Automate workflows, track progress, and never miss a deadline.',
      features: [
        'AI-powered task prioritization',
        'Real-time team collaboration',
        'Automated workflow creation',
        'Smart deadline tracking',
        'Integration with 100+ tools',
      ],
      pricing: 'Starting at $29/month',
    },
    
    targetAudience: {
      demographics: 'Software development teams, 10-100 employees',
      interests: [
        'Project management',
        'Team productivity',
        'Agile methodologies',
        'Developer tools',
        'Automation',
      ],
      painPoints: [
        'Missed deadlines',
        'Poor team coordination',
        'Manual workflow management',
        'Lack of visibility',
        'Tool fragmentation',
      ],
    },
    
    budget: 15000,
    
    timeline: {
      startDate: '2026-02-15',
      endDate: '2026-03-15',
    },
    
    goals: [
      'Generate 1,000 qualified leads',
      'Achieve 500 trial signups',
      'Increase brand awareness in developer community',
      'Boost website traffic by 200%',
    ],
    
    brandVoice: 'friendly',
  };

  // Create orchestrator and execute campaign
  const orchestrator = new MarketingCampaignOrchestrator();
  
  try {
    await orchestrator.executeCampaign(campaignRequest);
    
    console.log('\n✅ Campaign setup complete!');
    console.log('\nNext steps:');
    console.log('1. Review generated content and make any necessary adjustments');
    console.log('2. Address any compliance issues identified');
    console.log('3. Set up tracking URLs in your email/SMS platform');
    console.log('4. Schedule campaign send times');
    console.log('5. Monitor analytics dashboard for real-time results');
    
  } catch (error) {
    console.error('Campaign execution failed:', error);
    process.exit(1);
  }
}

// Run the example
console.log('Starting Email + SMS Campaign Example...\n');
runEmailSMSCampaign();
