import { NextApiRequest, NextApiResponse } from 'next';
import { campaignDB } from '../../../src/database/campaign-database';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { campaignId, templateName, scheduledAt, ...campaignRequest } = req.body;

    // Validate scheduled date
    if (scheduledAt) {
      const scheduleDate = new Date(scheduledAt);
      const now = new Date();

      if (scheduleDate <= now) {
        return res.status(400).json({ 
          success: false, 
          error: 'Scheduled time must be in the future' 
        });
      }
    }

    // Determine recipient type based on channels
    const channels = campaignRequest.channels || [];
    const isInstagramOnly = channels.length === 1 && channels[0] === 'instagram';
    const defaultRecipientType = isInstagramOnly ? 'none' : 'list';

    // Create scheduled campaign
    const scheduled = await campaignDB.createCampaign({
      campaignName: campaignRequest.campaignName,
      channels: campaignRequest.channels,
      status: 'scheduled',
      recipientType: campaignRequest.recipientType || defaultRecipientType,
      recipientCount: 0,
      recipientInfo: isInstagramOnly ? 'Instagram post (no recipients)' : (campaignRequest.recipientInfo || 'Scheduled'),
      executedAt: new Date(),
      scheduledAt: scheduledAt ? new Date(scheduledAt) : undefined,
      results: {},
      campaignData: campaignRequest,
      recipientData: campaignRequest.recipientData,
    });

    res.status(200).json({
      success: true,
      data: scheduled,
      message: `Campaign scheduled for ${new Date(scheduledAt).toLocaleString()}`,
    });

  } catch (error) {
    console.error('Schedule campaign error:', error);
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to schedule campaign',
    });
  }
}
