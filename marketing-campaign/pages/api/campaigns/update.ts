import { NextApiRequest, NextApiResponse } from 'next';
import { campaignDB } from '../../../src/database/campaign-database';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'PUT') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { id } = req.query;
    const { campaignData } = req.body;

    if (!id || typeof id !== 'string') {
      return res.status(400).json({ success: false, error: 'Campaign ID required' });
    }

    if (!campaignData) {
      return res.status(400).json({ success: false, error: 'Campaign data required' });
    }

    // Update the campaign
    const updated = await campaignDB.updateCampaign(id, {
      campaignName: campaignData.campaignName,
      campaignData: campaignData,
    });

    if (!updated) {
      return res.status(404).json({ success: false, error: 'Campaign not found' });
    }

    res.status(200).json({ 
      success: true, 
      data: updated,
      message: 'Campaign updated successfully'
    });

  } catch (error) {
    console.error('Campaign update error:', error);
    res.status(500).json({ 
      success: false, 
      error: error instanceof Error ? error.message : 'Failed to update campaign' 
    });
  }
}
