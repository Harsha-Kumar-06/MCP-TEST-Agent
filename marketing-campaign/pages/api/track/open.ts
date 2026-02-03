import { NextApiRequest, NextApiResponse } from 'next';
import { trackingDB } from '../../../src/database/tracking-database';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { campaignId, recipientId, recipientEmail } = req.query;

    if (!campaignId || !recipientId || !recipientEmail) {
      // Still return tracking pixel even if params missing
      return send1x1Pixel(res);
    }

    // Record open event
    await trackingDB.recordEvent({
      campaignId: campaignId as string,
      recipientId: recipientId as string,
      recipientEmail: recipientEmail as string,
      eventType: 'open',
      userAgent: req.headers['user-agent'],
      ipAddress: req.headers['x-forwarded-for'] as string || req.socket.remoteAddress,
    });

    console.log(`📧 Email opened: ${recipientEmail} (Campaign: ${campaignId})`);

    // Return 1x1 transparent pixel
    return send1x1Pixel(res);

  } catch (error) {
    console.error('Tracking error:', error);
    // Always return pixel even on error
    return send1x1Pixel(res);
  }
}

function send1x1Pixel(res: NextApiResponse) {
  // 1x1 transparent GIF
  const pixel = Buffer.from(
    'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7',
    'base64'
  );
  
  res.setHeader('Content-Type', 'image/gif');
  res.setHeader('Content-Length', pixel.length.toString());
  res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate, private');
  res.status(200).send(pixel);
}
