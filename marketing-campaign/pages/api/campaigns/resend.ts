import { NextApiRequest, NextApiResponse } from 'next';
import { campaignDB } from '../../../src/database/campaign-database';
import { contactDB } from '../../../src/database/contact-database';
import { executeCampaignWithContacts } from '../../../src/index';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { id } = req.query;

    if (!id || typeof id !== 'string') {
      return res.status(400).json({ success: false, error: 'Campaign ID required' });
    }

    // Get original campaign
    const campaign = await campaignDB.getCampaignById(id);
    if (!campaign) {
      return res.status(404).json({ success: false, error: 'Campaign not found' });
    }

    // Check if we have recipient data
    if (!campaign.recipientData) {
      return res.status(400).json({ 
        success: false, 
        error: 'Campaign does not have recipient data stored for resending' 
      });
    }

    // Get contacts based on recipient type
    let contacts: any[] = [];
    if (campaign.recipientData.singleContact) {
      contacts = [campaign.recipientData.singleContact];
    } else if (campaign.recipientData.contactListId) {
      const list = await contactDB.getListById(campaign.recipientData.contactListId);
      if (!list) {
        return res.status(404).json({ success: false, error: 'Contact list not found' });
      }
      contacts = list.contacts;
    }

    if (contacts.length === 0) {
      return res.status(400).json({ success: false, error: 'No contacts found to resend' });
    }

    console.log(`\n🔄 RESENDING CAMPAIGN: ${campaign.campaignName}`);
    console.log(`   Recipients: ${contacts.length}`);
    console.log(`   Channels: ${campaign.channels.join(', ')}`);

    // Execute the campaign with original data
    const result = await executeCampaignWithContacts(
      campaign.campaignData,
      contacts
    );

    // Create new campaign record for the resend
    const newCampaign = await campaignDB.createCampaign({
      campaignName: `${campaign.campaignName} (Resent)`,
      channels: campaign.channels,
      status: result.success ? 'completed' : 'failed',
      recipientType: campaign.recipientType,
      recipientCount: contacts.length,
      recipientInfo: campaign.recipientInfo,
      executedAt: new Date(),
      results: {
        emailsSent: result.results.emailResults?.sent || 0,
        emailsFailed: result.results.emailResults?.failed || 0,
        smsSent: result.results.smsResults?.sent || 0,
        smsFailed: result.results.smsResults?.failed || 0,
        instagramPosts: result.results.instagramResults?.success ? 1 : 0,
      },
      campaignData: campaign.campaignData,
      recipientData: campaign.recipientData,
    });

    res.status(200).json({ 
      success: true, 
      data: newCampaign,
      message: 'Campaign resent successfully',
      results: result.results
    });

  } catch (error) {
    console.error('Campaign resend error:', error);
    res.status(500).json({ 
      success: false, 
      error: error instanceof Error ? error.message : 'Failed to resend campaign' 
    });
  }
}
