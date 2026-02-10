import { AgentResult, AudienceSegment, CampaignRequest, EmailContent } from '../types/campaign';

/**
 * EmailContentAgent
 * 
 * Specialized agent for creating email marketing content
 */
export class EmailContentAgent {
  async execute(
    request: CampaignRequest,
    audienceData?: { segments: AudienceSegment[] }
  ): Promise<AgentResult> {
    console.log('\n✉️  EMAIL CONTENT AGENT: Generating email content...');

    try {
      // In production, this would use an AI model (GPT-4, Claude, etc.) to generate content
      // For now, we'll create template-based content

      const primarySegment = audienceData?.segments[0];
      const brandVoice = request.brandVoice || 'professional';

      // Generate main email content
      const emailContent: EmailContent = {
        subjectLine: this.generateSubjectLine(request, brandVoice),
        preheader: this.generatePreheader(request),
        bodyHtml: this.generateBodyHtml(request, brandVoice),
        bodyText: this.generateBodyText(request, brandVoice),
        cta: {
          text: this.generateCTA(request.goals[0]),
          url: `https://example.com/campaign/${request.campaignId}?utm_source=email&utm_campaign=${request.campaignId}`,
        },
        variants: [
          {
            variantName: 'Variant A - Feature Focus',
            subjectLine: this.generateSubjectLineVariantA(request),
            bodyHtml: this.generateBodyHtmlVariantA(request),
          },
          {
            variantName: 'Variant B - Benefit Focus',
            subjectLine: this.generateSubjectLineVariantB(request),
            bodyHtml: this.generateBodyHtmlVariantB(request),
          },
        ],
      };

      console.log('✅ Email content generated:');
      console.log(`   • Subject: ${emailContent.subjectLine}`);
      console.log(`   • CTA: ${emailContent.cta.text}`);
      console.log(`   • Variants: ${emailContent.variants?.length} A/B test options`);

      return {
        success: true,
        agentType: 'email-content',
        data: { emailContent },
        timestamp: new Date(),
      };

    } catch (error) {
      console.error('❌ EMAIL CONTENT AGENT: Error:', error);
      return {
        success: false,
        agentType: 'email-content',
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date(),
      };
    }
  }

  private generateSubjectLine(request: CampaignRequest, voice: string): string {
    const product = request.product.name;
    const voiceMap = {
      professional: `Introducing ${product}: Transform Your Workflow`,
      casual: `Hey! Check out ${product} 🚀`,
      friendly: `We think you'll love ${product}!`,
      authoritative: `The definitive solution: ${product}`,
    };
    return voiceMap[voice as keyof typeof voiceMap] || voiceMap.professional;
  }

  private generateSubjectLineVariantA(request: CampaignRequest): string {
    return `${request.product.features[0]} - See How ${request.product.name} Works`;
  }

  private generateSubjectLineVariantB(request: CampaignRequest): string {
    const painPoint = request.targetAudience.painPoints[0] || 'your challenges';
    return `Solve ${painPoint} with ${request.product.name}`;
  }

  private generatePreheader(request: CampaignRequest): string {
    return `${request.product.description.substring(0, 100)}...`;
  }

  private generateBodyHtml(request: CampaignRequest, voice: string, recipientEmail?: string): string {
    // Use campaign-specific info or fall back to .env defaults
    const replyEmail = request.companyInfo?.replyToEmail || process.env.GMAIL_USER || 'contact@example.com';
    const companyPhone = request.companyInfo?.phone || process.env.COMPANY_PHONE || '+1-555-0100';
    const companyWebsite = request.companyInfo?.website || process.env.COMPANY_WEBSITE || 'https://example.com';
    const bookingLink = request.companyInfo?.bookingLink || process.env.BOOKING_LINK || `https://calendly.com/company/demo`;
    const companyName = request.companyInfo?.companyName || request.product.name;
    const social = request.companyInfo?.socialMedia || {};
    
    // Generate tracking URLs
    const campaignId = request.campaignId;
    const recipientId = recipientEmail ? Buffer.from(recipientEmail).toString('base64') : 'unknown';
    const trackingPixel = `${process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000'}/api/track/open?campaignId=${campaignId}&recipientId=${recipientId}&recipientEmail=${encodeURIComponent(recipientEmail || '')}`;
    
    // Function to wrap URLs with click tracking
    const trackLink = (url: string) => {
      if (!recipientEmail) return url;
      return `${process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000'}/api/track/click?campaignId=${campaignId}&recipientId=${recipientId}&recipientEmail=${encodeURIComponent(recipientEmail)}&url=${encodeURIComponent(url)}`;
    };
    
    const ctaUrl = trackLink(`https://example.com/campaign/${request.campaignId}?utm_source=email&utm_campaign=${request.campaignId}`);
    const websiteUrl = trackLink(companyWebsite);
    const bookingUrl = trackLink(bookingLink);
    
    return `
<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; background: #fff; }
    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center; border-radius: 10px 10px 0 0; }
    .content { padding: 30px 20px; }
    .features { background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #667eea; }
    .cta-button { 
      display: inline-block; 
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white !important; 
      padding: 15px 40px; 
      text-decoration: none; 
      border-radius: 50px; 
      margin: 20px 0;
      font-weight: bold;
      box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
      transition: all 0.3s ease;
    }
    .cta-button:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    .secondary-cta {
      display: inline-block;
      background: white;
      color: #667eea !important;
      padding: 12px 30px;
      text-decoration: none;
      border: 2px solid #667eea;
      border-radius: 50px;
      margin: 10px 5px;
      font-weight: bold;
    }
    .contact-section {
      background: #f8f9fa;
      padding: 25px;
      margin: 30px 0;
      border-radius: 8px;
      text-align: center;
    }
    .contact-item {
      display: inline-block;
      margin: 10px 15px;
      color: #667eea;
      text-decoration: none;
      font-weight: 500;
    }
    .contact-item:hover {
      color: #764ba2;
    }
    .social-links {
      margin: 20px 0;
    }
    .social-links a {
      display: inline-block;
      margin: 0 10px;
      padding: 10px;
      background: #667eea;
      color: white;
      border-radius: 50%;
      width: 40px;
      height: 40px;
      text-align: center;
      text-decoration: none;
      line-height: 20px;
    }
    .footer { text-align: center; font-size: 12px; color: #666; padding: 20px; border-top: 1px solid #e0e0e0; margin-top: 30px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1 style="margin:0; font-size: 28px;">✨ ${request.product.name}</h1>
      <p style="margin: 10px 0 0 0; opacity: 0.9;">${request.product.description.substring(0, 80)}...</p>
    </div>
    <div class="content">
      <h2 style="color: #667eea;">Hello {{firstName}}!</h2>
      <p style="font-size: 16px;">${request.product.description}</p>
      
      <div class="features">
        <h3 style="color: #667eea; margin-top: 0;">🚀 Why Choose Us:</h3>
        <ul style="margin: 0; padding-left: 20px;">
          ${request.product.features.map(f => `<li style="margin: 8px 0;">${f}</li>`).join('')}
        </ul>
      </div>
      
      <p style="font-size: 16px;">Join thousands of <strong>${request.targetAudience.demographics}</strong> who are already transforming their workflow with ${request.product.name}.</p>
      
      <div style="text-align: center; margin: 30px 0;">
        <a href="${ctaUrl}" class="cta-button">🎯 ${this.generateCTA(request.goals[0])}</a>
      </div>
      
      ${request.product.pricing ? `<p style="text-align: center; font-size: 24px; color: #667eea; font-weight: bold; margin: 20px 0;">${request.product.pricing}</p>` : ''}
      
      <!-- Interactive Contact Section -->
      <div class="contact-section">
        <h3 style="color: #667eea; margin-top: 0;">💬 Let's Connect!</h3>
        <p style="margin: 15px 0;">Have questions? We're here to help!</p>
        
        <div style="margin: 20px 0;">
          <a href="${bookingUrl}" class="secondary-cta">📅 Book a Demo</a>
          <a href="mailto:${replyEmail}" class="secondary-cta">✉️ Email Us</a>
        </div>
        
        <div class="contact-item">
          📞 <a href="tel:${companyPhone}" style="color: #667eea; text-decoration: none;">${companyPhone}</a>
        </div>
        <div class="contact-item">
          🌐 <a href="${websiteUrl}" style="color: #667eea; text-decoration: none;">Visit Website</a>
        </div>
        
        <div class="social-links">
          ${social.twitter ? `<a href="${trackLink(social.twitter)}" title="Twitter">𝕏</a>` : ''}
          ${social.linkedin ? `<a href="${trackLink(social.linkedin)}" title="LinkedIn">in</a>` : ''}
          ${social.facebook ? `<a href="${trackLink(social.facebook)}" title="Facebook">f</a>` : ''}
          ${social.instagram ? `<a href="${trackLink(social.instagram)}" title="Instagram">📷</a>` : ''}
        </div>
      </div>
      
      <p style="text-align: center; color: #666; font-size: 14px; margin-top: 30px;">
        <strong>💡 Quick Tip:</strong> Reply directly to this email - we read every message!
      </p>
    </div>
    <div class="footer">
      <p><strong>Stay in Touch</strong></p>
      <p>📧 Reply to this email or call us at ${companyPhone}</p>
      <p style="margin: 15px 0;">You're receiving this because you subscribed to our mailing list.</p>
      <p><a href="{{UNSUBSCRIBE_URL}}" style="color: #667eea;">Unsubscribe</a> | <a href="{{PREFERENCES_URL}}" style="color: #667eea;">Update Preferences</a></p>
      <p>&copy; 2026 ${companyName}. All rights reserved.</p>
    </div>
    <!-- Tracking Pixel -->
    <img src="${trackingPixel}" width="1" height="1" style="display:none;" alt="" />
  </div>
</body>
</html>
    `;
  }

  private generateBodyHtmlVariantA(request: CampaignRequest): string {
    // Variant A focuses on features
    return this.generateBodyHtml(request, 'professional').replace(
      'Join thousands',
      `Featuring ${request.product.features[0]} and more. Join thousands`
    );
  }

  private generateBodyHtmlVariantB(request: CampaignRequest): string {
    // Variant B focuses on benefits/pain points
    const painPoint = request.targetAudience.painPoints[0] || 'your challenges';
    return this.generateBodyHtml(request, 'professional').replace(
      request.product.description,
      `Tired of ${painPoint}? ${request.product.description}`
    );
  }

  private generateBodyText(request: CampaignRequest, voice: string): string {
    const replyEmail = request.companyInfo?.replyToEmail || process.env.GMAIL_USER || 'contact@example.com';
    const companyPhone = request.companyInfo?.phone || process.env.COMPANY_PHONE || '+1-555-0100';
    const bookingLink = request.companyInfo?.bookingLink || process.env.BOOKING_LINK || 'https://calendly.com/company/demo';
    const companyWebsite = request.companyInfo?.website || process.env.COMPANY_WEBSITE || 'https://example.com';
    const companyName = request.companyInfo?.companyName || request.product.name;
    
    const features = request.product.features.map((f, i) => `${i + 1}. ${f}`).join('\n');
    const pricing = request.product.pricing || '';
    const websiteUrl = process.env.COMPANY_WEBSITE || 'https://example.com';
    
    return [
      request.product.name,
      '',
      'Hello {{firstName}}!',
      '',
      request.product.description,
      '',
      'Key Features:',
      features,
      '',
      `Join thousands of ${request.targetAudience.demographics} who are already benefiting from ${request.product.name}.`,
      '',
      'Get Started Today: {{CTA_URL}}',
      '',
      pricing,
      '',
      '========================================',
      'LET\'S CONNECT!',
      '========================================',
      '',
      'Have questions? We\'re here to help!',
      '',
      `Book a Demo: ${bookingLink}`,
      `Email: ${replyEmail}`,
      `Phone: ${companyPhone}`,
      `Website: ${websiteUrl}`,
      '',
      'Quick Tip: Reply directly to this email - we read every message!',
      '',
      '========================================',
      '',
      'You\'re receiving this email because you subscribed to our mailing list.',
      '',
      'Unsubscribe: {{UNSUBSCRIBE_URL}}',
      'Update Preferences: {{PREFERENCES_URL}}',
      '',
      `(c) 2026 ${request.product.name}. All rights reserved.`
    ].join('\n').trim();
  }

  private generateCTA(goal: string): string {
    const ctaMap: { [key: string]: string } = {
      'generate leads': 'Start Your Free Trial',
      'increase awareness': 'Learn More',
      'drive signups': 'Sign Up Now',
      'boost sales': 'Buy Now',
    };

    for (const [key, value] of Object.entries(ctaMap)) {
      if (goal.toLowerCase().includes(key)) {
        return value;
      }
    }

    return 'Get Started';
  }
}
