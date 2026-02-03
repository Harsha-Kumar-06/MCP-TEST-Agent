import { NextApiRequest, NextApiResponse } from 'next';
import { trackingDB } from '../../../src/database/tracking-database';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { campaignId, recipientId, recipientEmail, url } = req.query;

    if (!url) {
      return res.status(400).json({ error: 'URL parameter required' });
    }

    // Record click event
    if (campaignId && recipientId && recipientEmail) {
      await trackingDB.recordEvent({
        campaignId: campaignId as string,
        recipientId: recipientId as string,
        recipientEmail: recipientEmail as string,
        eventType: 'click',
        url: url as string,
        userAgent: req.headers['user-agent'],
        ipAddress: req.headers['x-forwarded-for'] as string || req.socket.remoteAddress,
      });

      console.log(`🔗 Link clicked: ${recipientEmail} → ${url}`);
    }

    // Redirect to actual URL
    res.redirect(302, url as string);

  } catch (error) {
    console.error('Click tracking error:', error);
    // Still redirect even on error
    const { url } = req.query;
    if (url) {
      res.redirect(302, url as string);
    } else {
      res.status(500).json({ error: 'Failed to track click' });
    }
  }
}
