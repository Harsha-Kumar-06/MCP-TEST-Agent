import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';

export default function CampaignDetail() {
  const router = useRouter();
  const { id } = router.query;
  const [campaign, setCampaign] = useState<any>(null);
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [resending, setResending] = useState(false);
  const [savingTemplate, setSavingTemplate] = useState(false);

  useEffect(() => {
    if (id) {
      fetchCampaign();
      fetchAnalytics();
    }
  }, [id]);

  const fetchCampaign = async () => {
    try {
      const res = await fetch('/api/campaigns');
      const data = await res.json();
      if (data.success) {
        const found = data.data.find((c: any) => c.id === id);
        setCampaign(found || null);
      }
    } catch (error) {
      console.error('Failed to fetch campaign:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const res = await fetch(`/api/campaigns/analytics?campaignId=${id}`);
      const data = await res.json();
      if (data.success) {
        setAnalytics(data.data);
      }
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    }
  };

  const handleSaveAsTemplate = async () => {
    const templateName = prompt('Enter template name:');
    if (!templateName) return;

    setSavingTemplate(true);
    try {
      const res = await fetch('/api/campaigns/templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ campaignId: id, templateName }),
      });
      const data = await res.json();
      
      if (data.success) {
        alert('✅ Template saved successfully!');
      } else {
        alert('Failed to save template: ' + data.error);
      }
    } catch (error) {
      alert('Error saving template');
    } finally {
      setSavingTemplate(false);
    }
  };

  const handleResend = async () => {
    if (!confirm('Resend this campaign to the same recipients?')) return;

    setResending(true);
    try {
      const res = await fetch(`/api/campaigns/resend?id=${id}`, {
        method: 'POST',
      });
      const data = await res.json();
      
      if (data.success) {
        alert(`Campaign resent successfully!\n\nResults:\n- Emails sent: ${data.results.emailResults?.sent || 0}\n- SMS sent: ${data.results.smsResults?.sent || 0}\n- Instagram posts: ${data.results.instagramResults?.success ? 1 : 0}`);
        router.push('/campaigns');
      } else {
        alert('Failed to resend: ' + data.error);
      }
    } catch (error) {
      alert('Error resending campaign');
    } finally {
      setResending(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Delete this campaign?')) return;

    try {
      const res = await fetch(`/api/campaigns?id=${id}`, {
        method: 'DELETE',
      });
      const data = await res.json();
      
      if (data.success) {
        alert('Campaign deleted successfully');
        router.push('/campaigns');
      } else {
        alert('Failed to delete: ' + data.error);
      }
    } catch (error) {
      alert('Error deleting campaign');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">Loading campaign...</div>
      </div>
    );
  }

  if (!campaign) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-700 mb-4">Campaign not found</h2>
          <Link href="/campaigns" className="text-blue-600 hover:text-blue-800">
            ← Back to campaigns
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Head>
        <title>{campaign.campaignName} - Campaign Manager</title>
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
              <Link href="/campaigns" className="text-blue-600 font-medium">
                Campaigns
              </Link>              <Link href="/campaigns/templates" className="text-gray-700 hover:text-gray-900">
                📚 Templates
              </Link>              <Link href="/campaigns/create" className="text-gray-700 hover:text-gray-900">
                New Campaign
              </Link>
              <Link href="/contacts" className="text-gray-700 hover:text-gray-900">
                Contacts
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="mb-6">
          <Link href="/campaigns" className="text-blue-600 hover:text-blue-800">
            ← Back to campaigns
          </Link>
        </div>

        <div className="bg-white rounded-lg shadow overflow-hidden">
          {/* Header */}
          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{campaign.campaignName}</h1>
                <p className="text-sm text-gray-500 mt-1">
                  Executed on {new Date(campaign.executedAt).toLocaleString()}
                </p>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={handleSaveAsTemplate}
                  disabled={savingTemplate}
                  className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 disabled:bg-gray-400"
                >
                  {savingTemplate ? '⏳ Saving...' : '📚 Save as Template'}
                </button>
                <button
                  onClick={handleResend}
                  disabled={resending}
                  className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:bg-gray-400"
                >
                  {resending ? '⏳ Resending...' : '🔄 Resend'}
                </button>
                <Link
                  href={`/campaigns/edit/${campaign.id}`}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                >
                  ✏️ Edit
                </Link>
                <button
                  onClick={handleDelete}
                  className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700"
                >
                  🗑️ Delete
                </button>
              </div>
            </div>
          </div>

          {/* Details */}
          <div className="px-6 py-6 space-y-6">
            {/* Status & Recipients */}
            <div className="grid grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Status</h3>
                <span className={`px-3 py-1 inline-flex text-sm font-semibold rounded-full ${
                  campaign.status === 'completed' ? 'bg-green-100 text-green-800' :
                  campaign.status === 'failed' ? 'bg-red-100 text-red-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {campaign.status}
                </span>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Recipients</h3>
                <p className="text-lg font-semibold text-gray-900">
                  {campaign.recipientCount} contact{campaign.recipientCount !== 1 ? 's' : ''}
                </p>
                <p className="text-sm text-gray-600">{campaign.recipientInfo}</p>
              </div>
            </div>

            {/* Channels */}
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Channels</h3>
              <div className="flex gap-2">
                {campaign.channels.map((ch: string) => (
                  <span
                    key={ch}
                    className="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium bg-blue-100 text-blue-800"
                  >
                    {ch === 'email' ? '✉️ Email' : ch === 'sms' ? '📱 SMS' : '📸 Instagram'}
                  </span>
                ))}
              </div>
            </div>

            {/* Results */}
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Results</h3>
              <div className="grid grid-cols-2 gap-4">
                {campaign.results.emailsSent !== undefined && (
                  <div className="bg-green-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">
                      {campaign.results.emailsSent}
                    </div>
                    <div className="text-sm text-gray-600">Emails Sent</div>
                  </div>
                )}
                {campaign.results.emailsFailed !== undefined && campaign.results.emailsFailed > 0 && (
                  <div className="bg-red-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-red-600">
                      {campaign.results.emailsFailed}
                    </div>
                    <div className="text-sm text-gray-600">Emails Failed</div>
                  </div>
                )}
                {campaign.results.smsSent !== undefined && (
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">
                      {campaign.results.smsSent}
                    </div>
                    <div className="text-sm text-gray-600">SMS Sent</div>
                  </div>
                )}
                {campaign.results.smsFailed !== undefined && campaign.results.smsFailed > 0 && (
                  <div className="bg-red-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-red-600">
                      {campaign.results.smsFailed}
                    </div>
                    <div className="text-sm text-gray-600">SMS Failed</div>
                  </div>
                )}
                {campaign.results.instagramPosts !== undefined && campaign.results.instagramPosts > 0 && (
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600">
                      {campaign.results.instagramPosts}
                    </div>
                    <div className="text-sm text-gray-600">Instagram Posts</div>
                  </div>
                )}
              </div>
            </div>

            {/* Email Analytics */}
            {analytics && campaign.channels.includes('email') && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-3">📊 Email Analytics</h3>
                <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-lg border border-blue-200">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div>
                      <div className="text-3xl font-bold text-blue-600">{analytics.uniqueOpens}</div>
                      <div className="text-sm text-gray-600">Opens</div>
                      <div className="text-xs text-gray-500">
                        {campaign.results.emailsSent > 0 
                          ? `${Math.round((analytics.uniqueOpens / campaign.results.emailsSent) * 100)}%`
                          : '0%'} rate
                      </div>
                    </div>
                    <div>
                      <div className="text-3xl font-bold text-purple-600">{analytics.uniqueClicks}</div>
                      <div className="text-sm text-gray-600">Clicks</div>
                      <div className="text-xs text-gray-500">
                        {analytics.uniqueOpens > 0
                          ? `${Math.round((analytics.uniqueClicks / analytics.uniqueOpens) * 100)}%`
                          : '0%'} of opens
                      </div>
                    </div>
                    <div>
                      <div className="text-3xl font-bold text-green-600">{analytics.totalOpens}</div>
                      <div className="text-sm text-gray-600">Total Opens</div>
                      <div className="text-xs text-gray-500">Including repeats</div>
                    </div>
                    <div>
                      <div className="text-3xl font-bold text-indigo-600">{analytics.totalClicks}</div>
                      <div className="text-sm text-gray-600">Total Clicks</div>
                      <div className="text-xs text-gray-500">All link clicks</div>
                    </div>
                  </div>

                  {/* Top Clicked Links */}
                  {Object.keys(analytics.clicksByUrl).length > 0 && (
                    <div className="mt-4 pt-4 border-t border-blue-200">
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">🔗 Top Clicked Links:</h4>
                      <div className="space-y-2">
                        {Object.entries(analytics.clicksByUrl)
                          .sort(([, a]: any, [, b]: any) => b - a)
                          .slice(0, 5)
                          .map(([url, clicks]: any) => (
                            <div key={url} className="flex justify-between items-center bg-white px-3 py-2 rounded">
                              <span className="text-sm text-gray-600 truncate flex-1 mr-2">{url}</span>
                              <span className="text-sm font-semibold text-blue-600">{clicks} clicks</span>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Campaign Data */}
                    <div className="text-sm text-gray-600">SMS Sent</div>
                  </div>
                )}
                {campaign.results.smsFailed !== undefined && campaign.results.smsFailed > 0 && (
                  <div className="bg-red-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-red-600">
                      {campaign.results.smsFailed}
                    </div>
                    <div className="text-sm text-gray-600">SMS Failed</div>
                  </div>
                )}
                {campaign.results.instagramPosts !== undefined && campaign.results.instagramPosts > 0 && (
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600">
                      {campaign.results.instagramPosts}
                    </div>
                    <div className="text-sm text-gray-600">Instagram Posts</div>
                  </div>
                )}
              </div>
            </div>

            {/* Campaign Data */}
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Campaign Details</h3>
              <div className="bg-gray-50 p-4 rounded-lg">
                <pre className="text-xs text-gray-700 overflow-auto">
                  {JSON.stringify(campaign.campaignData, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
