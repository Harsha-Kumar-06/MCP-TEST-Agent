import * as fs from 'fs';
import * as path from 'path';
import { Contact, ContactList } from '../types/database';

/**
 * Simple file-based database for contacts
 * In production, replace with PostgreSQL, MongoDB, etc.
 */

const DATA_DIR = path.join(process.cwd(), 'data');
const CONTACTS_FILE = path.join(DATA_DIR, 'contacts.json');
const LISTS_FILE = path.join(DATA_DIR, 'contact-lists.json');

export class ContactDatabase {
  constructor() {
    this.ensureDataDirectory();
  }

  private ensureDataDirectory(): void {
    if (!fs.existsSync(DATA_DIR)) {
      fs.mkdirSync(DATA_DIR, { recursive: true });
    }
    if (!fs.existsSync(CONTACTS_FILE)) {
      fs.writeFileSync(CONTACTS_FILE, JSON.stringify([], null, 2));
    }
    if (!fs.existsSync(LISTS_FILE)) {
      fs.writeFileSync(LISTS_FILE, JSON.stringify([], null, 2));
    }
  }

  // Contacts
  async getAllContacts(): Promise<Contact[]> {
    const data = fs.readFileSync(CONTACTS_FILE, 'utf-8');
    return JSON.parse(data);
  }

  async getContactById(id: string): Promise<Contact | null> {
    const contacts = await this.getAllContacts();
    return contacts.find(c => c.id === id) || null;
  }

  async createContact(contact: Omit<Contact, 'id' | 'createdAt' | 'updatedAt'>): Promise<Contact> {
    const contacts = await this.getAllContacts();
    const newContact: Contact = {
      ...contact,
      id: `contact-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    contacts.push(newContact);
    fs.writeFileSync(CONTACTS_FILE, JSON.stringify(contacts, null, 2));
    return newContact;
  }

  async updateContact(id: string, updates: Partial<Contact>): Promise<Contact | null> {
    const contacts = await this.getAllContacts();
    const index = contacts.findIndex(c => c.id === id);
    if (index === -1) return null;

    contacts[index] = {
      ...contacts[index],
      ...updates,
      updatedAt: new Date(),
    };
    fs.writeFileSync(CONTACTS_FILE, JSON.stringify(contacts, null, 2));
    
    // Sync update to contact lists
    const lists = await this.getAllLists();
    let listsUpdated = false;
    for (const list of lists) {
      const contactIndex = list.contacts.findIndex(c => c.id === id);
      if (contactIndex !== -1) {
        list.contacts[contactIndex] = contacts[index];
        list.updatedAt = new Date();
        listsUpdated = true;
      }
    }
    if (listsUpdated) {
      fs.writeFileSync(LISTS_FILE, JSON.stringify(lists, null, 2));
    }
    
    return contacts[index];
  }

  async deleteContact(id: string): Promise<boolean> {
    const contacts = await this.getAllContacts();
    const filtered = contacts.filter(c => c.id !== id);
    if (filtered.length === contacts.length) return false;
    fs.writeFileSync(CONTACTS_FILE, JSON.stringify(filtered, null, 2));
    
    // Remove contact from all lists
    const lists = await this.getAllLists();
    let listsUpdated = false;
    for (const list of lists) {
      const originalLength = list.contacts.length;
      list.contacts = list.contacts.filter(c => c.id !== id);
      if (list.contacts.length !== originalLength) {
        list.updatedAt = new Date();
        listsUpdated = true;
      }
    }
    if (listsUpdated) {
      fs.writeFileSync(LISTS_FILE, JSON.stringify(lists, null, 2));
    }
    
    return true;
  }

  // Contact Lists
  async getAllLists(): Promise<ContactList[]> {
    const data = fs.readFileSync(LISTS_FILE, 'utf-8');
    return JSON.parse(data);
  }

  async getListById(id: string): Promise<ContactList | null> {
    const lists = await this.getAllLists();
    return lists.find(l => l.id === id) || null;
  }

  async createList(list: Omit<ContactList, 'id' | 'createdAt' | 'updatedAt'>): Promise<ContactList> {
    const lists = await this.getAllLists();
    const newList: ContactList = {
      ...list,
      id: `list-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    lists.push(newList);
    fs.writeFileSync(LISTS_FILE, JSON.stringify(lists, null, 2));
    return newList;
  }

  async updateList(id: string, updates: Partial<ContactList>): Promise<ContactList | null> {
    const lists = await this.getAllLists();
    const index = lists.findIndex(l => l.id === id);
    if (index === -1) return null;

    lists[index] = {
      ...lists[index],
      ...updates,
      updatedAt: new Date(),
    };
    fs.writeFileSync(LISTS_FILE, JSON.stringify(lists, null, 2));
    return lists[index];
  }

  async deleteList(id: string): Promise<boolean> {
    const lists = await this.getAllLists();
    const filtered = lists.filter(l => l.id !== id);
    if (filtered.length === lists.length) return false;
    fs.writeFileSync(LISTS_FILE, JSON.stringify(filtered, null, 2));
    return true;
  }

  // CSV Import
  async importFromCSV(csvContent: string, listName: string): Promise<ContactList> {
    const lines = csvContent.split('\n').filter(line => line.trim());
    const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
    
    const contacts: Contact[] = [];
    
    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim());
      const row: any = {};
      
      headers.forEach((header, index) => {
        row[header] = values[index];
      });

      const contact: Omit<Contact, 'id' | 'createdAt' | 'updatedAt'> = {
        email: row.email || undefined,
        phone: row.phone || undefined,
        firstName: row.firstname || row.first_name || undefined,
        lastName: row.lastname || row.last_name || undefined,
        company: row.company || undefined,
        tags: row.tags ? row.tags.split(';') : [],
        optInEmail: row.optin_email !== 'false' && row.optin_email !== '0',
        optInSMS: row.optin_sms !== 'false' && row.optin_sms !== '0',
      };

      // Create contact and add to list
      const createdContact = await this.createContact(contact);
      contacts.push(createdContact);
    }

    // Create list
    return await this.createList({
      name: listName,
      description: `Imported from CSV - ${contacts.length} contacts`,
      contacts,
    });
  }
}

export const contactDB = new ContactDatabase();
