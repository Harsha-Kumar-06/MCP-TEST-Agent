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
      const message = error instanceof Error ? error.message : 'Failed to create contact';
      res.status(400).json({ success: false, error: message });
    }
  } else if (req.method === 'PUT') {
    // Update contact
    try {
      const { id } = req.query;
      if (!id || typeof id !== 'string') {
        return res.status(400).json({ success: false, error: 'Contact ID required' });
      }
      const updated = await contactDB.updateContact(id, req.body);
      if (!updated) {
        return res.status(404).json({ success: false, error: 'Contact not found' });
      }
      res.status(200).json({ success: true, data: updated });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to update contact';
      res.status(400).json({ success: false, error: message });
    }
  } else if (req.method === 'DELETE') {
    // Delete contact
    try {
      const { id } = req.query;
      if (!id || typeof id !== 'string') {
        return res.status(400).json({ success: false, error: 'Contact ID required' });
      }
      const deleted = await contactDB.deleteContact(id);
      if (!deleted) {
        return res.status(404).json({ success: false, error: 'Contact not found' });
      }
      res.status(200).json({ success: true, message: 'Contact deleted successfully' });
    } catch (error) {
      res.status(500).json({ success: false, error: 'Failed to delete contact' });
    }
  } else {
    res.status(405).json({ error: 'Method not allowed' });
  }
}
