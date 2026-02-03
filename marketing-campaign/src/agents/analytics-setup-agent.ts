import { AgentResult, AnalyticsSetup, CampaignRequest } from '../types/campaign';

/**
 * AnalyticsSetupAgent
 * 
 * Specialized agent for configuring campaign tracking and analytics
 */
export class AnalyticsSetupAgent {
  async execute(request: CampaignRequest): Promise<AgentResult> {
    console.log('\n📊 ANALYTICS SETUP AGENT: Configuring tracking...');

    try {
      // Generate UTM parameters
      const utmParameters = {
        source: this.determineSource(request.channels),
        medium: this.determineMedium(request.channels),
        campaign: request.campaignId,
        content: request.campaignName.toLowerCase().replace(/\s+/g, '-'),
      };

      // Define conversion goals based on campaign goals
      const conversionGoals = this.defineConversionGoals(request.goals);

      // Generate tracking URLs for each channel
      const trackingUrls = this.generateTrackingUrls(request, utmParameters);

      const analyticsSetup: AnalyticsSetup = {
        trackingEnabled: true,
        utmParameters,
        conversionGoals,
        dashboardUrl: `https://analytics.example.com/dashboard/${request.campaignId}`,
      };

      console.log('✅ Analytics configured:');
      console.log(`   • UTM Campaign: ${utmParameters.campaign}`);
      console.log(`   • UTM Source: ${utmParameters.source}`);
      console.log(`   • UTM Medium: ${utmParameters.medium}`);
      console.log(`   • Conversion Goals: ${conversionGoals.length} defined`);
      console.log(`   • Tracking URLs: ${Object.keys(trackingUrls).length} generated`);

      return {
        success: true,
        agentType: 'analytics-setup',
        data: { 
          analyticsSetup,
          trackingUrls,
          kpis: this.defineKPIs(request),
        },
        timestamp: new Date(),
      };

    } catch (error) {
      console.error('❌ ANALYTICS SETUP AGENT: Error:', error);
      return {
        success: false,
        agentType: 'analytics-setup',
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date(),
      };
    }
  }

  private determineSource(channels: string[]): string {
    if (channels.includes('email') && channels.includes('sms')) {
      return 'marketing-automation';
    }
    if (channels.includes('email')) {
      return 'email';
    }
    if (channels.includes('sms')) {
      return 'sms';
    }
    return 'unknown';
  }

  private determineMedium(channels: string[]): string {
    if (channels.length > 1) {
      return 'multi-channel';
    }
    return channels[0] || 'unknown';
  }

  private defineConversionGoals(campaignGoals: string[]): string[] {
    const goals: string[] = [];

    campaignGoals.forEach(goal => {
      if (goal.toLowerCase().includes('lead')) {
        goals.push('form_submission');
        goals.push('contact_us_click');
      }
      if (goal.toLowerCase().includes('signup') || goal.toLowerCase().includes('trial')) {
        goals.push('trial_signup');
        goals.push('account_creation');
      }
      if (goal.toLowerCase().includes('purchase') || goal.toLowerCase().includes('sale')) {
        goals.push('purchase_complete');
        goals.push('add_to_cart');
      }
      if (goal.toLowerCase().includes('awareness') || goal.toLowerCase().includes('engagement')) {
        goals.push('page_view');
        goals.push('time_on_site');
        goals.push('bounce_rate');
      }
    });

    // Default goals if none specific
    if (goals.length === 0) {
      goals.push('landing_page_view', 'cta_click', 'conversion');
    }

    return [...new Set(goals)]; // Remove duplicates
  }

  private generateTrackingUrls(
    request: CampaignRequest,
    utm: AnalyticsSetup['utmParameters']
  ): Record<string, string> {
    const baseUrl = 'https://example.com/landing';
    const utmString = `utm_source=${utm.source}&utm_medium=${utm.medium}&utm_campaign=${utm.campaign}&utm_content=${utm.content}`;

    const urls: Record<string, string> = {
      landing_page: `${baseUrl}?${utmString}`,
    };

    if (request.channels.includes('email')) {
      urls.email_cta = `${baseUrl}?${utmString}&utm_source=email&channel=email`;
      urls.email_variant_a = `${baseUrl}?${utmString}&utm_source=email&variant=a`;
      urls.email_variant_b = `${baseUrl}?${utmString}&utm_source=email&variant=b`;
    }

    if (request.channels.includes('sms')) {
      urls.sms_link = `${baseUrl}?${utmString}&utm_source=sms&channel=sms`;
      urls.sms_variant_a = `${baseUrl}?${utmString}&utm_source=sms&variant=a`;
      urls.sms_variant_b = `${baseUrl}?${utmString}&utm_source=sms&variant=b`;
    }

    return urls;
  }

  private defineKPIs(request: CampaignRequest): Record<string, any> {
    const kpis: Record<string, any> = {
      // Common KPIs for all campaigns
      impressions: {
        description: 'Total number of message deliveries',
        target: null,
      },
      reach: {
        description: 'Unique recipients',
        target: null,
      },
      cost_per_action: {
        description: 'Total cost divided by conversions',
        target: request.budget / 100, // Assume 100 conversions as baseline
      },
      roi: {
        description: 'Return on Investment',
        target: '300%', // 3x return target
      },
    };

    // Email-specific KPIs
    if (request.channels.includes('email')) {
      kpis.email_open_rate = {
        description: 'Percentage of emails opened',
        target: '20%', // Industry average
      };
      kpis.email_click_rate = {
        description: 'Percentage of emails clicked',
        target: '3%', // Industry average
      };
      kpis.email_conversion_rate = {
        description: 'Percentage of clicks that convert',
        target: '5%',
      };
      kpis.email_unsubscribe_rate = {
        description: 'Percentage of recipients who unsubscribe',
        target: '<0.5%',
      };
    }

    // SMS-specific KPIs
    if (request.channels.includes('sms')) {
      kpis.sms_delivery_rate = {
        description: 'Percentage of SMS successfully delivered',
        target: '98%',
      };
      kpis.sms_click_rate = {
        description: 'Percentage of SMS with link clicks',
        target: '8%', // SMS typically has higher engagement
      };
      kpis.sms_conversion_rate = {
        description: 'Percentage of clicks that convert',
        target: '10%',
      };
      kpis.sms_opt_out_rate = {
        description: 'Percentage of recipients who opt out',
        target: '<2%',
      };
    }

    return kpis;
  }
}
