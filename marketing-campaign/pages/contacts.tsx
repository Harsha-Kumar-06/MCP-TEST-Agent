import Head from 'next/head';
import Link from 'next/link';
import { useEffect, useState } from 'react';

export default function ContactsPage() {
  const [contacts, setContacts] = useState([]);
  const [lists, setLists] = useState([]);
  const [showUpload, setShowUpload] = useState(false);
  const [uploading, setUploading] = useState(false);

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
                      <Link
                        href={`/campaigns/create?listId=${list.id}`}
                        className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700"
                      >
                        Create Campaign
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

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
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {contacts.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
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
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
