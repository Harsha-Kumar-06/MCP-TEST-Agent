import { NextApiRequest, NextApiResponse } from 'next';
import { campaignDB } from '../../../src/database/campaign-database';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    if (req.method === 'GET') {
      // Get all templates
      const templates = await campaignDB.getTemplates();
      return res.status(200).json({ success: true, data: templates });
    }

    if (req.method === 'POST') {
      // Save campaign as template
      const { campaignId, templateName } = req.body;

      if (!campaignId || !templateName) {
        return res.status(400).json({ 
          success: false, 
          error: 'Campaign ID and template name required' 
        });
      }

      const campaign = await campaignDB.getCampaignById(campaignId);
      if (!campaign) {
        return res.status(404).json({ success: false, error: 'Campaign not found' });
      }

      // Create template copy
      const template = await campaignDB.createCampaign({
        ...campaign,
        campaignName: templateName,
        templateName,
        isTemplate: true,
        status: 'completed',
        recipientCount: 0,
        recipientInfo: 'Template',
        results: {},
        recipientData: undefined,
      });

      return res.status(200).json({ 
        success: true, 
        data: template,
        message: 'Template saved successfully'
      });
    }

    if (req.method === 'DELETE') {
      // Delete template
      const { id } = req.query;

      if (!id || typeof id !== 'string') {
        return res.status(400).json({ success: false, error: 'Template ID required' });
      }

      const deleted = await campaignDB.deleteCampaign(id);

      if (!deleted) {
        return res.status(404).json({ success: false, error: 'Template not found' });
      }

      return res.status(200).json({ 
        success: true, 
        message: 'Template deleted successfully' 
      });
    }

    return res.status(405).json({ error: 'Method not allowed' });

  } catch (error) {
    console.error('Template API error:', error);
    res.status(500).json({ 
      success: false, 
      error: error instanceof Error ? error.message : 'Failed to process template' 
    });
  }
}
