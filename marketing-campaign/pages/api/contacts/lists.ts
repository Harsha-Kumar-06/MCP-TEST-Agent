import { NextApiRequest, NextApiResponse } from 'next';
import { contactDB } from '../../../src/database/contact-database';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    // Get all contact lists
    try {
      const lists = await contactDB.getAllLists();
      res.status(200).json({ success: true, data: lists });
    } catch (error) {
      res.status(500).json({ success: false, error: 'Failed to fetch lists' });
    }
  } else if (req.method === 'POST') {
    // Create new contact list
    try {
      const list = await contactDB.createList(req.body);
      res.status(201).json({ success: true, data: list });
    } catch (error) {
      res.status(500).json({ success: false, error: 'Failed to create list' });
    }
  } else {
    res.status(405).json({ error: 'Method not allowed' });
  }
}
