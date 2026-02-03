import { NextApiRequest, NextApiResponse } from 'next';
import { contactDB } from '../../../src/database/contact-database';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    // Get all contacts
    try {
      const contacts = await contactDB.getAllContacts();
      res.status(200).json({ success: true, data: contacts });
    } catch (error) {
      res.status(500).json({ success: false, error: 'Failed to fetch contacts' });
    }
  } else if (req.method === 'POST') {
    // Create new contact
    try {
      const contact = await contactDB.createContact(req.body);
      res.status(201).json({ success: true, data: contact });
    } catch (error) {
      res.status(500).json({ success: false, error: 'Failed to create contact' });
    }
  } else {
    res.status(405).json({ error: 'Method not allowed' });
  }
}
