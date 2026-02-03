import { AgentResult, CampaignRequest, ComplianceCheck } from '../types/campaign';

/**
 * ComplianceAgent
 * 
 * Specialized agent for checking campaign compliance with regulations
 * - CAN-SPAM Act (Email)
 * - TCPA (SMS)
 * - GDPR
 * - CCPA
 */
export class ComplianceAgent {
  async execute(
    request: CampaignRequest,
    previousResults: Map<string, AgentResult>
  ): Promise<AgentResult> {
    console.log('\n⚖️  COMPLIANCE AGENT: Reviewing campaign compliance...');

    try {
      const issues: ComplianceCheck['issues'] = [];
      const recommendations: string[] = [];

      // Email compliance checks
      if (request.channels.includes('email')) {
        this.checkEmailCompliance(request, previousResults, issues, recommendations);
      }

      // SMS compliance checks
      if (request.channels.includes('sms')) {
        this.checkSMSCompliance(request, previousResults, issues, recommendations);
      }

      // General compliance checks
      this.checkGeneralCompliance(request, issues, recommendations);

      const passed = issues.filter(i => i.severity === 'critical').length === 0;

      const complianceCheck: ComplianceCheck = {
        passed,
        issues,
        recommendations,
      };

      console.log(`${passed ? '✅' : '⚠️'} Compliance check ${passed ? 'passed' : 'has issues'}:`);
      console.log(`   • Issues: ${issues.length} (${issues.filter(i => i.severity === 'critical').length} critical)`);
      console.log(`   • Recommendations: ${recommendations.length}`);

      if (issues.length > 0) {
        console.log('\n   Issues found:');
        issues.forEach(issue => {
          console.log(`     [${issue.severity.toUpperCase()}] ${issue.message}`);
        });
      }

      return {
        success: true,
        agentType: 'compliance',
        data: { complianceCheck },
        timestamp: new Date(),
      };

    } catch (error) {
      console.error('❌ COMPLIANCE AGENT: Error:', error);
      return {
        success: false,
        agentType: 'compliance',
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date(),
      };
    }
  }

  private checkEmailCompliance(
    request: CampaignRequest,
    previousResults: Map<string, AgentResult>,
    issues: ComplianceCheck['issues'],
    recommendations: string[]
  ): void {
    const emailContent = previousResults.get('email-content')?.data?.emailContent;

    if (!emailContent) {
      issues.push({
        severity: 'critical',
        message: 'Email content not found for compliance review',
        channel: 'email',
      });
      return;
    }

    // CAN-SPAM Act checks
    
    // 1. Check for unsubscribe link
    if (!emailContent.bodyHtml.includes('UNSUBSCRIBE_URL') && !emailContent.bodyHtml.includes('unsubscribe')) {
      issues.push({
        severity: 'critical',
        message: 'Missing unsubscribe link - Required by CAN-SPAM Act',
        channel: 'email',
      });
    } else {
      recommendations.push('Ensure unsubscribe mechanism is functional and processes requests within 10 days');
    }

    // 2. Check for physical address
    if (!emailContent.bodyHtml.includes('Company Name') && !emailContent.bodyHtml.includes('address')) {
      issues.push({
        severity: 'warning',
        message: 'Missing physical postal address - Required by CAN-SPAM Act',
        channel: 'email',
      });
    }

    // 3. Check subject line accuracy (basic check)
    if (emailContent.subjectLine.toLowerCase().includes('free') && !request.product.description.toLowerCase().includes('free')) {
      issues.push({
        severity: 'warning',
        message: 'Subject line may be misleading - Ensure it accurately represents email content',
        channel: 'email',
      });
    }

    // GDPR checks
    recommendations.push('Ensure recipients have provided explicit consent (GDPR)');
    recommendations.push('Include clear data processing information in privacy policy');
    recommendations.push('Provide easy access to data deletion requests');

    // Best practices
    recommendations.push('Test all email links before sending');
    recommendations.push('Include a "View in browser" link for HTML emails');
  }

  private checkSMSCompliance(
    request: CampaignRequest,
    previousResults: Map<string, AgentResult>,
    issues: ComplianceCheck['issues'],
    recommendations: string[]
  ): void {
    const smsContent = previousResults.get('sms-content')?.data?.smsContent;

    if (!smsContent) {
      issues.push({
        severity: 'critical',
        message: 'SMS content not found for compliance review',
        channel: 'sms',
      });
      return;
    }

    // TCPA (Telephone Consumer Protection Act) checks

    // 1. Check message length (warnings for multiple segments = higher cost)
    if (smsContent.segmentCount > 1) {
      issues.push({
        severity: 'info',
        message: `SMS will be sent as ${smsContent.segmentCount} messages - Consider shortening to reduce costs`,
        channel: 'sms',
      });
    }

    // 2. Opt-out mechanism
    if (!smsContent.message.toLowerCase().includes('stop') && !smsContent.message.toLowerCase().includes('reply stop')) {
      issues.push({
        severity: 'critical',
        message: 'Missing opt-out instructions - Required by TCPA. Add "Reply STOP to unsubscribe"',
        channel: 'sms',
      });
    }

    // 3. Time restrictions
    recommendations.push('Only send SMS between 8 AM - 9 PM recipient local time (TCPA requirement)');
    
    // 4. Consent requirements
    issues.push({
      severity: 'critical',
      message: 'Verify all recipients have provided prior express written consent (TCPA requirement)',
      channel: 'sms',
    });

    recommendations.push('Include company name in SMS to identify sender');
    recommendations.push('Keep records of opt-in consent for all recipients');
    recommendations.push('Process opt-out requests immediately');
    recommendations.push('Include customer service contact information');
  }

  private checkGeneralCompliance(
    request: CampaignRequest,
    issues: ComplianceCheck['issues'],
    recommendations: string[]
  ): void {
    // CCPA (California Consumer Privacy Act)
    recommendations.push('Provide "Do Not Sell My Personal Information" link for California recipients');

    // Accessibility
    recommendations.push('Ensure email templates are accessible (WCAG 2.1 AA)');
    recommendations.push('Use alt text for all images');

    // General best practices
    recommendations.push('Maintain a suppression list for unsubscribed users');
    recommendations.push('Implement rate limiting to avoid being marked as spam');
    recommendations.push('Use authenticated email (SPF, DKIM, DMARC)');

    // Budget considerations
    if (request.budget < 1000 && request.channels.includes('sms')) {
      issues.push({
        severity: 'info',
        message: `Budget of $${request.budget} may be insufficient for SMS campaigns (avg cost: $0.01-0.05 per message)`,
      });
    }
  }
}
