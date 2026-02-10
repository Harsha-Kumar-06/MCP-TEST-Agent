import { NextApiRequest, NextApiResponse } from 'next';
import { campaignDB } from '../../../src/database/campaign-database';
import { contactDB } from '../../../src/database/contact-database';
import { MarketingCampaignOrchestrator } from '../../../src/index';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { campaignRequest, contactListId, singleContact } = req.body;

    if (!campaignRequest) {
      return res.status(400).json({ error: 'Missing campaign request' });
    }

    let contacts = [];
    let recipientInfo = '';
    let recipientType: 'list' | 'single' = 'single';

    // Option 1: Single contact provided
    if (singleContact) {
      contacts = [singleContact];
      recipientInfo = singleContact.email;
      recipientType = 'single';
    } 
    // Option 2: Contact list ID provided
    else if (contactListId) {
      const contactList = await contactDB.getListById(contactListId);
      if (!contactList) {
        return res.status(404).json({ error: 'Contact list not found' });
      }
      contacts = contactList.contacts;
      recipientInfo = contactList.name;
      recipientType = 'list';
    }
    // Neither provided
    else {
      return res.status(400).json({ error: 'Must provide either contactListId or singleContact' });
    }

    // Execute campaign
    const orchestrator = new MarketingCampaignOrchestrator();
    const results = await orchestrator.executeCampaignWithContacts(
      campaignRequest,
      contacts
    );

    // Extract sending results
    const emailsSent = results.sendingResults?.emailResults?.sent || 0;
    const emailsFailed = results.sendingResults?.emailResults?.failed || 0;
    const smsSent = results.sendingResults?.smsResults?.sent || 0;
    const smsFailed = results.sendingResults?.smsResults?.failed || 0;
    const instagramPosts = results.sendingResults?.instagramResults?.feedPost?.success ? 1 : 0;

    // Save campaign to database with recipient data for resend
    const campaignRecord = await campaignDB.createCampaign({
      campaignName: campaignRequest.campaignName,
      channels: campaignRequest.channels,
      status: 'completed',
      recipientType,
      recipientCount: contacts.length,
      recipientInfo,
      executedAt: new Date(),
      results: {
        emailsSent,
        emailsFailed,
        smsSent,
        smsFailed,
        instagramPosts,
      },
      campaignData: campaignRequest,
      recipientData: {
        contactListId: recipientType === 'list' ? contactListId : undefined,
        singleContact: recipientType === 'single' ? singleContact : undefined,
      },
    });

    res.status(200).json({ 
      success: true, 
      data: results,
      campaign: campaignRecord,
      message: 'Campaign executed successfully'
    });
  } catch (error) {
    console.error('Campaign execution error:', error);
    
    // Try to save failed campaign
    try {
      const { campaignRequest, singleContact } = req.body;
      if (campaignRequest) {
        await campaignDB.createCampaign({
          campaignName: campaignRequest.campaignName,
          channels: campaignRequest.channels || [],
          status: 'failed',
          recipientType: singleContact ? 'single' : 'list',
          recipientCount: 0,
          recipientInfo: 'Execution failed',
          executedAt: new Date(),
          results: {},
          campaignData: campaignRequest,
        });
      }
    } catch (saveError) {
      console.error('Failed to save error record:', saveError);
    }

    res.status(500).json({ 
      success: false, 
      error: error instanceof Error ? error.message : 'Failed to execute campaign' 
    });
  }
}
