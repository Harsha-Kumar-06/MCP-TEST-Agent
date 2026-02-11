import * as fs from 'fs';
import * as path from 'path';

export interface TrackingEvent {
  id: string;
  campaignId: string;
  recipientId: string;
  recipientEmail: string;
  eventType: 'open' | 'click';
  url?: string; // For click events
  userAgent?: string;
  ipAddress?: string;
  timestamp: Date;
}

const DATA_DIR = path.join(process.cwd(), 'data');
const TRACKING_FILE = path.join(DATA_DIR, 'tracking-events.json');

export class TrackingDatabase {
  constructor() {
    this.ensureDataFile();
  }

  private ensureDataFile(): void {
    if (!fs.existsSync(DATA_DIR)) {
      fs.mkdirSync(DATA_DIR, { recursive: true });
    }
    if (!fs.existsSync(TRACKING_FILE)) {
      fs.writeFileSync(TRACKING_FILE, JSON.stringify([], null, 2));
    }
  }

  async recordEvent(event: Omit<TrackingEvent, 'id' | 'timestamp'>): Promise<TrackingEvent> {
    const events = await this.getAllEvents();
    const newEvent: TrackingEvent = {
      ...event,
      id: `event-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`,
      timestamp: new Date(),
    };
    events.push(newEvent);
    fs.writeFileSync(TRACKING_FILE, JSON.stringify(events, null, 2));
    return newEvent;
  }

  async getAllEvents(): Promise<TrackingEvent[]> {
    const data = fs.readFileSync(TRACKING_FILE, 'utf-8');
    return JSON.parse(data);
  }

  async getEventsByCampaign(campaignId: string): Promise<TrackingEvent[]> {
    const events = await this.getAllEvents();
    return events.filter(e => e.campaignId === campaignId);
  }

  async getCampaignAnalytics(campaignId: string) {
    const events = await this.getEventsByCampaign(campaignId);
    
    const opens = events.filter(e => e.eventType === 'open');
    const clicks = events.filter(e => e.eventType === 'click');
    
    // Unique recipients who opened
    const uniqueOpens = new Set(opens.map(e => e.recipientEmail)).size;
    
    // Unique recipients who clicked
    const uniqueClicks = new Set(clicks.map(e => e.recipientEmail)).size;
    
    // Click breakdown by URL
    const clicksByUrl: { [url: string]: number } = {};
    clicks.forEach(click => {
      if (click.url) {
        clicksByUrl[click.url] = (clicksByUrl[click.url] || 0) + 1;
      }
    });
    
    return {
      totalOpens: opens.length,
      uniqueOpens,
      totalClicks: clicks.length,
      uniqueClicks,
      clicksByUrl,
      events: events.sort((a, b) => 
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      ),
    };
  }

  async getRecipientEvents(campaignId: string, recipientEmail: string): Promise<TrackingEvent[]> {
    const events = await this.getEventsByCampaign(campaignId);
    return events.filter(e => e.recipientEmail === recipientEmail);
  }
}

export const trackingDB = new TrackingDatabase();
