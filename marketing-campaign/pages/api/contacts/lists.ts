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
  } else if (req.method === 'PUT') {
    // Update contact list
    try {
      const { id } = req.query;
      if (!id || typeof id !== 'string') {
        return res.status(400).json({ success: false, error: 'List ID required' });
      }
      const updated = await contactDB.updateList(id, req.body);
      if (!updated) {
        return res.status(404).json({ success: false, error: 'List not found' });
      }
      res.status(200).json({ success: true, data: updated });
    } catch (error) {
      res.status(500).json({ success: false, error: 'Failed to update list' });
    }
  } else if (req.method === 'DELETE') {
    // Delete contact list
    try {
      const { id } = req.query;
      if (!id || typeof id !== 'string') {
        return res.status(400).json({ success: false, error: 'List ID required' });
      }
      const deleted = await contactDB.deleteList(id);
      if (!deleted) {
        return res.status(404).json({ success: false, error: 'List not found' });
      }
      res.status(200).json({ success: true, message: 'List deleted successfully' });
    } catch (error) {
      res.status(500).json({ success: false, error: 'Failed to delete list' });
    }
  } else {
    res.status(405).json({ error: 'Method not allowed' });
  }
}
