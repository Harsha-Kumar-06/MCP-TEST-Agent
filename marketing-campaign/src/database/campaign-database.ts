import * as fs from 'fs';
import * as path from 'path';

export interface CampaignRecord {
  id: string;
  campaignName: string;
  channels: string[];
  status: 'completed' | 'failed' | 'pending' | 'scheduled';
  recipientType: 'list' | 'single';
  recipientCount: number;
  recipientInfo: string; // List name or contact email
  executedAt: Date;
  scheduledAt?: Date; // For scheduled campaigns
  isTemplate?: boolean; // Mark as template
  templateName?: string; // Template display name
  results: {
    emailsSent?: number;
    emailsFailed?: number;
    smsSent?: number;
    smsFailed?: number;
    instagramPosts?: number;
  };
  campaignData: any; // Full campaign request
  // Store recipient data for resend capability
  recipientData?: {
    contactListId?: string;
    singleContact?: any;
  };
}

const DATA_DIR = path.join(process.cwd(), 'data');
const CAMPAIGNS_FILE = path.join(DATA_DIR, 'campaigns.json');

export class CampaignDatabase {
  constructor() {
    this.ensureDataDirectory();
  }

  private ensureDataDirectory(): void {
    if (!fs.existsSync(DATA_DIR)) {
      fs.mkdirSync(DATA_DIR, { recursive: true });
    }
    if (!fs.existsSync(CAMPAIGNS_FILE)) {
      fs.writeFileSync(CAMPAIGNS_FILE, JSON.stringify([], null, 2));
    }
  }

  async getAllCampaigns(): Promise<CampaignRecord[]> {
    const data = fs.readFileSync(CAMPAIGNS_FILE, 'utf-8');
    return JSON.parse(data);
  }

  async getCampaignById(id: string): Promise<CampaignRecord | null> {
    const campaigns = await this.getAllCampaigns();
    return campaigns.find(c => c.id === id) || null;
  }

  async createCampaign(campaign: Omit<CampaignRecord, 'id'>): Promise<CampaignRecord> {
    const campaigns = await this.getAllCampaigns();
    const newCampaign: CampaignRecord = {
      ...campaign,
      id: `campaign-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    };
    campaigns.push(newCampaign);
    fs.writeFileSync(CAMPAIGNS_FILE, JSON.stringify(campaigns, null, 2));
    return newCampaign;
  }

  async updateCampaign(id: string, updates: Partial<CampaignRecord>): Promise<CampaignRecord | null> {
    const campaigns = await this.getAllCampaigns();
    const index = campaigns.findIndex(c => c.id === id);
    
    if (index === -1) return null;
    
    campaigns[index] = { ...campaigns[index], ...updates };
    fs.writeFileSync(CAMPAIGNS_FILE, JSON.stringify(campaigns, null, 2));
    return campaigns[index];
  }

  async deleteCampaign(id: string): Promise<boolean> {
    const campaigns = await this.getAllCampaigns();
    const filtered = campaigns.filter(c => c.id !== id);
    
    if (filtered.length === campaigns.length) return false;
    
    fs.writeFileSync(CAMPAIGNS_FILE, JSON.stringify(filtered, null, 2));
    return true;
  }

  async getTemplates(): Promise<CampaignRecord[]> {
    const campaigns = await this.getAllCampaigns();
    return campaigns.filter(c => c.isTemplate === true);
  }

  async getScheduledCampaigns(): Promise<CampaignRecord[]> {
    const campaigns = await this.getAllCampaigns();
    return campaigns.filter(c => c.status === 'scheduled' && c.scheduledAt);
  }
}

export const campaignDB = new CampaignDatabase();
