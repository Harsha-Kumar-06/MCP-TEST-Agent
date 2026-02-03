import { NextApiRequest, NextApiResponse } from 'next';
import { campaignDB } from '../../../src/database/campaign-database';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    // Get all campaigns
    try {
      const campaigns = await campaignDB.getAllCampaigns();
      res.status(200).json({ success: true, data: campaigns });
    } catch (error) {
      res.status(500).json({ success: false, error: 'Failed to fetch campaigns' });
    }
  } else if (req.method === 'DELETE') {
    // Delete campaign by ID
    try {
      const { id } = req.query;
      if (!id || typeof id !== 'string') {
        return res.status(400).json({ success: false, error: 'Campaign ID required' });
      }
      
      const deleted = await campaignDB.deleteCampaign(id);
      if (!deleted) {
        return res.status(404).json({ success: false, error: 'Campaign not found' });
      }
      
      res.status(200).json({ success: true, message: 'Campaign deleted' });
    } catch (error) {
      res.status(500).json({ success: false, error: 'Failed to delete campaign' });
    }
  } else {
    res.status(405).json({ error: 'Method not allowed' });
  }
}
