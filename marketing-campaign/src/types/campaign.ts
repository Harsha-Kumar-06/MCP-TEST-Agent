/**
 * Campaign Types and Interfaces
 */

export type CampaignChannel = 'email' | 'sms' | 'instagram';

export interface CampaignRequest {
  campaignId: string;
  campaignName: string;
  channels: CampaignChannel[];
  product: {
    name: string;
    description: string;
    features: string[];
    pricing?: string;
  };
  targetAudience: {
    demographics: string;
    interests: string[];
    painPoints: string[];
  };
  budget: number;
  timeline: {
    startDate: string;
    endDate: string;
  };
  goals: string[];
  brandVoice?: 'professional' | 'casual' | 'friendly' | 'authoritative';
  landingUrl?: string; // URL to include in SMS/email campaigns
  // Company/Contact Information (per campaign)
  companyInfo?: {
    companyName?: string;
    replyToEmail?: string;
    phone?: string;
    website?: string;
    bookingLink?: string;
    socialMedia?: {
      twitter?: string;
      linkedin?: string;
      facebook?: string;
      instagram?: string;
    };
  };
}

export interface SubTask {
  id: string;
  agentType: AgentType;
  taskDescription: string;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'in-progress' | 'completed' | 'failed';
  dependencies?: string[];
  result?: any;
  error?: string;
}

export type AgentType =
  | 'coordinator'
  | 'email-content'
  | 'email-design'
  | 'sms-content'
  | 'audience-segmentation'
  | 'compliance'
  | 'analytics-setup'
  | 'send-execution';

export interface AgentResult {
  success: boolean;
  agentType: AgentType;
  data?: any;
  error?: string;
  timestamp: Date;
}

export interface EmailContent {
  subjectLine: string;
  preheader: string;
  bodyHtml: string;
  bodyText: string;
  cta: {
    text: string;
    url: string;
  };
  variants?: {
    variantName: string;
    subjectLine: string;
    bodyHtml: string;
  }[];
}

export interface SMSContent {
  message: string;
  shortUrl?: string;
  characterCount: number;
  segmentCount: number;
  variants?: {
    variantName: string;
    message: string;
  }[];
}

export interface AudienceSegment {
  segmentId: string;
  segmentName: string;
  criteria: Record<string, any>;
  estimatedSize: number;
  channels: CampaignChannel[];
}

export interface ComplianceCheck {
  passed: boolean;
  issues: {
    severity: 'critical' | 'warning' | 'info';
    message: string;
    channel?: CampaignChannel;
  }[];
  recommendations: string[];
}

export interface AnalyticsSetup {
  trackingEnabled: boolean;
  utmParameters: {
    source: string;
    medium: string;
    campaign: string;
    content?: string;
  };
  conversionGoals: string[];
  dashboardUrl?: string;
}
