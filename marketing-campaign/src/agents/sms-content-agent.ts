import { AgentResult, AudienceSegment, CampaignRequest, SMSContent } from '../types/campaign';

/**
 * SMSContentAgent
 * 
 * Specialized agent for creating SMS marketing content
 */
export class SMSContentAgent {
  private readonly MAX_SMS_LENGTH = 160;
  private readonly OPTIMAL_LENGTH = 140; // Leave room for personalization

  async execute(
    request: CampaignRequest,
    audienceData?: { segments: AudienceSegment[] }
  ): Promise<AgentResult> {
    console.log('\n📱 SMS CONTENT AGENT: Generating SMS content...');

    try {
      // In production, this would use an AI model to generate optimized SMS content
      // For now, we'll create template-based content

      const brandVoice = request.brandVoice || 'professional';
      
      // Generate main SMS content
      const smsContent: SMSContent = {
        message: this.generateSMSMessage(request, brandVoice),
        shortUrl: this.generateShortUrl(request),
        characterCount: 0, // Will be calculated
        segmentCount: 0, // Will be calculated
        variants: [
          {
            variantName: 'Variant A - Urgency Focus',
            message: this.generateSMSVariantA(request),
          },
          {
            variantName: 'Variant B - Value Focus',
            message: this.generateSMSVariantB(request),
          },
        ],
      };

      // Calculate character count and segments
      smsContent.characterCount = smsContent.message.length;
      smsContent.segmentCount = Math.ceil(smsContent.characterCount / this.MAX_SMS_LENGTH);

      // Validate length
      if (smsContent.characterCount > this.MAX_SMS_LENGTH) {
        console.warn(`⚠️  SMS exceeds ${this.MAX_SMS_LENGTH} characters. Will be sent as ${smsContent.segmentCount} messages.`);
      }

      console.log('✅ SMS content generated:');
      console.log(`   • Message: ${smsContent.message.substring(0, 50)}...`);
      console.log(`   • Length: ${smsContent.characterCount} chars (${smsContent.segmentCount} SMS)`);
      console.log(`   • Variants: ${smsContent.variants?.length} A/B test options`);

      return {
        success: true,
        agentType: 'sms-content',
        data: { smsContent },
        timestamp: new Date(),
      };

    } catch (error) {
      console.error('❌ SMS CONTENT AGENT: Error:', error);
      return {
        success: false,
        agentType: 'sms-content',
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date(),
      };
    }
  }

  private generateSMSMessage(request: CampaignRequest, voice: string): string {
    const product = request.product.name;
    const shortUrl = this.generateShortUrl(request);
    
    // Different message styles based on brand voice
    const messages = {
      professional: `${product}: ${request.product.description.substring(0, 60)}. Learn more: ${shortUrl}`,
      casual: `Hey! 👋 Check out ${product} - ${request.product.features[0]}. ${shortUrl}`,
      friendly: `We think you'll love ${product}! ${request.product.description.substring(0, 50)}... ${shortUrl}`,
      authoritative: `${product} - The solution for ${request.targetAudience.painPoints[0] || 'your needs'}. ${shortUrl}`,
    };

    let message = messages[voice as keyof typeof messages] || messages.professional;

    // Ensure it's under the optimal length
    if (message.length > this.OPTIMAL_LENGTH) {
      // Truncate description
      const maxDescLength = this.OPTIMAL_LENGTH - product.length - shortUrl.length - 20;
      const truncatedDesc = request.product.description.substring(0, maxDescLength);
      message = `${product}: ${truncatedDesc}... ${shortUrl}`;
    }

    return message;
  }

  private generateSMSVariantA(request: CampaignRequest): string {
    // Urgency-focused variant
    const product = request.product.name;
    const shortUrl = this.generateShortUrl(request);
    
    const urgentMessages = [
      `🔥 Limited time! ${product} - ${request.product.features[0]}. ${shortUrl}`,
      `⏰ Don't miss out: ${product}. ${request.product.description.substring(0, 50)}... ${shortUrl}`,
      `Act now! ${product} - Special offer. ${shortUrl}`,
    ];

    let message = urgentMessages[0];
    
    // Ensure optimal length
    if (message.length > this.OPTIMAL_LENGTH) {
      message = `🔥 ${product} - Limited offer! ${shortUrl}`;
    }

    return message;
  }

  private generateSMSVariantB(request: CampaignRequest): string {
    // Value-focused variant
    const product = request.product.name;
    const shortUrl = this.generateShortUrl(request);
    const benefit = request.product.features[0] || 'amazing features';

    let message = `💎 ${product}: Get ${benefit}. ${shortUrl}`;

    if (request.product.pricing) {
      message = `💎 ${product}: ${benefit}. ${request.product.pricing}. ${shortUrl}`;
    }

    // Ensure optimal length
    if (message.length > this.OPTIMAL_LENGTH) {
      message = `💎 ${product} - ${benefit}. ${shortUrl}`;
    }

    return message;
  }

  private generateShortUrl(request: CampaignRequest): string {
    // In production, integrate with URL shortening service (bit.ly, tinyurl, etc.)
    return `https://short.link/${request.campaignId}`;
  }

  /**
   * Calculate actual SMS segment count based on GSM-7 encoding
   */
  private calculateSMSSegments(message: string): number {
    // GSM-7 allows 160 chars for single SMS, 153 for multi-part
    const hasUnicode = /[^\x00-\x7F]/.test(message);
    
    if (hasUnicode) {
      // Unicode (UCS-2) encoding: 70 chars for single, 67 for multi-part
      return message.length <= 70 ? 1 : Math.ceil(message.length / 67);
    } else {
      // GSM-7 encoding
      return message.length <= 160 ? 1 : Math.ceil(message.length / 153);
    }
  }
}
