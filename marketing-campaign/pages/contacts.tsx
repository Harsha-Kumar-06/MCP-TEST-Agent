import Head from 'next/head';
import Link from 'next/link';
import { useEffect, useState } from 'react';

export default function ContactsPage() {
  const [contacts, setContacts] = useState([]);
  const [lists, setLists] = useState([]);
  const [showUpload, setShowUpload] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [editingContact, setEditingContact] = useState<any>(null);
  const [editingList, setEditingList] = useState<any>(null);

  useEffect(() => {
    fetchContacts();
    fetchLists();
  }, []);

  const fetchContacts = async () => {
    try {
      const res = await fetch('/api/contacts');
      const data = await res.json();
      if (data.success) {
        setContacts(data.data);
      }
    } catch (error) {
      console.error('Failed to fetch contacts:', error);
    }
  };

  const fetchLists = async () => {
    try {
      const res = await fetch('/api/contacts/lists');
      const data = await res.json();
      if (data.success) {
        setLists(data.data);
      }
    } catch (error) {
      console.error('Failed to fetch lists:', error);
    }
  };

  const handleDeleteList = async (listId: string, listName: string) => {
    if (!confirm(`Delete list "${listName}"? This cannot be undone.`)) return;
    
    try {
      const res = await fetch(`/api/contacts/lists?id=${listId}`, {
        method: 'DELETE',
      });
      const data = await res.json();
      if (data.success) {
        alert('List deleted successfully');
        fetchLists();
      } else {
        alert('Failed to delete: ' + data.error);
      }
    } catch (error) {
      alert('Failed to delete list');
    }
  };

  const handleDeleteContact = async (contactId: string) => {
    if (!confirm('Delete this contact?')) return;
    
    try {
      const res = await fetch(`/api/contacts?id=${contactId}`, {
        method: 'DELETE',
      });
      const data = await res.json();
      if (data.success) {
        fetchContacts();
        fetchLists(); // Refresh lists too as they contain contacts
      } else {
        alert('Failed to delete: ' + data.error);
      }
    } catch (error) {
      alert('Failed to delete contact');
    }
  };

  const handleUpdateContact = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!editingContact) return;

    const formData = new FormData(e.currentTarget);
    const updates = {
      firstName: formData.get('firstName'),
      lastName: formData.get('lastName'),
      email: formData.get('email'),
      phone: formData.get('phone'),
      company: formData.get('company'),
      optInEmail: formData.get('optInEmail') === 'on',
      optInSMS: formData.get('optInSMS') === 'on',
    };

    try {
      const res = await fetch(`/api/contacts?id=${editingContact.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      const data = await res.json();
      if (data.success) {
        setEditingContact(null);
        fetchContacts();
        fetchLists();
      } else {
        alert('Failed to update: ' + data.error);
      }
    } catch (error) {
      alert('Failed to update contact');
    }
  };

  const handleUpdateList = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!editingList) return;

    const formData = new FormData(e.currentTarget);
    const updates = {
      name: formData.get('name'),
      description: formData.get('description'),
    };

    try {
      const res = await fetch(`/api/contacts/lists?id=${editingList.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      const data = await res.json();
      if (data.success) {
        setEditingList(null);
        fetchLists();
      } else {
        alert('Failed to update: ' + data.error);
      }
    } catch (error) {
      alert('Failed to update list');
    }
  };

  const handleFileUpload = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setUploading(true);

    const formData = new FormData(e.currentTarget);

    try {
      const res = await fetch('/api/contacts/upload-csv', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (data.success) {
        alert(data.message);
        setShowUpload(false);
        fetchContacts();
        fetchLists();
      } else {
        alert('Upload failed: ' + data.error);
      }
    } catch (error) {
      alert('Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Head>
        <title>Contacts - Campaign Manager</title>
      </Head>

      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link href="/" className="text-xl font-bold text-gray-900 hover:text-blue-600">
                🤖 Campaign Coordinator
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/" className="text-gray-700 hover:text-gray-900">
                🏠 Home
              </Link>
              <Link href="/campaigns" className="text-gray-700 hover:text-gray-900">
                Campaigns
              </Link>
              <Link href="/campaigns/create" className="text-gray-700 hover:text-gray-900">
                New Campaign
              </Link>
              <Link href="/contacts" className="text-blue-600 font-medium">
                Contacts
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Contacts</h1>
          <button
            onClick={() => setShowUpload(!showUpload)}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            {showUpload ? 'Cancel' : '📤 Upload CSV'}
          </button>
        </div>

        {/* CSV Upload Form */}
        {showUpload && (
          <div className="bg-white p-6 rounded-lg shadow mb-8">
            <h2 className="text-xl font-semibold mb-4">Upload CSV File</h2>
            <form onSubmit={handleFileUpload}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  List Name
                </label>
                <input
                  type="text"
                  name="listName"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="e.g., Q1 2026 Leads"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  CSV File
                </label>
                <input
                  type="file"
                  name="file"
                  accept=".csv"
                  required
                  className="w-full"
                />
                <p className="text-xs text-gray-500 mt-2">
                  CSV should include: email, phone, firstName, lastName, company, optInEmail, optInSMS
                </p>
              </div>
              <button
                type="submit"
                disabled={uploading}
                className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 disabled:bg-gray-400"
              >
                {uploading ? 'Uploading...' : 'Upload'}
              </button>
            </form>
          </div>
        )}

        {/* Contact Lists */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold">Contact Lists</h2>
          </div>
          <div className="p-6">
            {lists.length === 0 ? (
              <p className="text-gray-500">No contact lists yet. Upload a CSV to get started.</p>
            ) : (
              <div className="space-y-4">
                {lists.map((list: any) => (
                  <div key={list.id} className="border border-gray-200 rounded p-4 hover:bg-gray-50">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-medium text-gray-900">{list.name}</h3>
                        <p className="text-sm text-gray-600">{list.description}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {list.contacts.length} contacts • Created {new Date(list.createdAt).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => setEditingList(list)}
                          className="text-blue-600 hover:text-blue-800 px-3 py-1 text-sm border border-blue-600 rounded"
                        >
                          ✏️ Edit
                        </button>
                        <button
                          onClick={() => handleDeleteList(list.id, list.name)}
                          className="text-red-600 hover:text-red-800 px-3 py-1 text-sm border border-red-600 rounded"
                        >
                          🗑️ Delete
                        </button>
                        <Link
                          href={`/campaigns/create?listId=${list.id}`}
                          className="bg-blue-600 text-white px-4 py-1 rounded text-sm hover:bg-blue-700"
                        >
                          Create Campaign
                        </Link>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Edit List Modal */}
        {editingList && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
              <h2 className="text-xl font-semibold mb-4">Edit List</h2>
              <form onSubmit={handleUpdateList}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                  <input
                    type="text"
                    name="name"
                    defaultValue={editingList.name}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <input
                    type="text"
                    name="description"
                    defaultValue={editingList.description}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
                <div className="flex justify-end space-x-2">
                  <button
                    type="button"
                    onClick={() => setEditingList(null)}
                    className="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                  >
                    Save Changes
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* All Contacts */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold">All Contacts ({contacts.length})</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Phone</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Company</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Opt-In</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {contacts.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                      No contacts yet
                    </td>
                  </tr>
                ) : (
                  contacts.map((contact: any) => (
                    <tr key={contact.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {contact.firstName} {contact.lastName}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {contact.email}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {contact.phone}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {contact.company}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {contact.optInEmail && <span className="text-green-600">✉️ </span>}
                        {contact.optInSMS && <span className="text-green-600">📱</span>}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button
                          onClick={() => setEditingContact(contact)}
                          className="text-blue-600 hover:text-blue-800 mr-3"
                        >
                          ✏️ Edit
                        </button>
                        <button
                          onClick={() => handleDeleteContact(contact.id)}
                          className="text-red-600 hover:text-red-800"
                        >
                          🗑️ Delete
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Edit Contact Modal */}
        {editingContact && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
              <h2 className="text-xl font-semibold mb-4">Edit Contact</h2>
              <form onSubmit={handleUpdateContact}>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
                    <input
                      type="text"
                      name="firstName"
                      defaultValue={editingContact.firstName}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
                    <input
                      type="text"
                      name="lastName"
                      defaultValue={editingContact.lastName}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                </div>
                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input
                    type="email"
                    name="email"
                    defaultValue={editingContact.email}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                  <input
                    type="text"
                    name="phone"
                    defaultValue={editingContact.phone}
                    placeholder="+1234567890"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Company</label>
                  <input
                    type="text"
                    name="company"
                    defaultValue={editingContact.company}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
                <div className="mt-4 flex space-x-6">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      name="optInEmail"
                      defaultChecked={editingContact.optInEmail}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">Email Opt-In</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      name="optInSMS"
                      defaultChecked={editingContact.optInSMS}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">SMS Opt-In</span>
                  </label>
                </div>
                <div className="flex justify-end space-x-2 mt-6">
                  <button
                    type="button"
                    onClick={() => setEditingContact(null)}
                    className="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                  >
                    Save Changes
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
