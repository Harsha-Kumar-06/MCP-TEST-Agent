import { NextApiRequest, NextApiResponse } from 'next';
import { trackingDB } from '../../../src/database/tracking-database';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { campaignId } = req.query;

    if (!campaignId || typeof campaignId !== 'string') {
      return res.status(400).json({ success: false, error: 'Campaign ID required' });
    }

    const analytics = await trackingDB.getCampaignAnalytics(campaignId);

    res.status(200).json({
      success: true,
      data: analytics,
    });

  } catch (error) {
    console.error('Analytics error:', error);
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to get analytics',
    });
  }
}
