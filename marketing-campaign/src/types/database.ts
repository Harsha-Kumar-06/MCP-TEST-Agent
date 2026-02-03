/**
 * Database Schema for Contacts and Campaigns
 */

export interface Contact {
  id: string;
  email?: string;
  phone?: string;
  firstName?: string;
  lastName?: string;
  company?: string;
  tags: string[];
  optInEmail: boolean;
  optInSMS: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface ContactList {
  id: string;
  name: string;
  description?: string;
  contacts: Contact[];
  createdAt: Date;
  updatedAt: Date;
}

export interface Campaign {
  id: string;
  name: string;
  status: 'draft' | 'scheduled' | 'running' | 'completed' | 'failed';
  request: any; // CampaignRequest
  contactListId: string;
  results?: {
    emailsSent: number;
    smsSent: number;
    emailsDelivered: number;
    smsDelivered: number;
    emailsFailed: number;
    smsFailed: number;
    opens: number;
    clicks: number;
  };
  createdAt: Date;
  updatedAt: Date;
  scheduledAt?: Date;
  completedAt?: Date;
}
