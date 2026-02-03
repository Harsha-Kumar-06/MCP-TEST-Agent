import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';

export default function EditCampaign() {
  const router = useRouter();
  const { id } = router.query;

  const [campaign, setCampaign] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [resendAfterEdit, setResendAfterEdit] = useState(false);

  const [formData, setFormData] = useState({
    campaignName: '',
    channels: [] as string[],
    productName: '',
    productDescription: '',
    features: '',
    pricing: '',
    targetDemographics: '',
    targetInterests: '',
    painPoints: '',
    budget: '',
    startDate: '',
    endDate: '',
    goals: '',
    brandVoice: 'professional',
    // Company info
    companyName: '',
    replyToEmail: '',
    companyPhone: '',
    companyWebsite: '',
    bookingLink: '',
    twitter: '',
    linkedin: '',
    facebook: '',
    instagram: '',
  });

  useEffect(() => {
    if (id) {
      fetchCampaign();
    }
  }, [id]);

  const fetchCampaign = async () => {
    try {
      const res = await fetch('/api/campaigns');
      const data = await res.json();
      if (data.success) {
        const found = data.data.find((c: any) => c.id === id);
        if (found) {
          setCampaign(found);
          populateForm(found);
        }
      }
    } catch (error) {
      console.error('Failed to fetch campaign:', error);
    } finally {
      setLoading(false);
    }
  };

  const populateForm = (campaignRecord: any) => {
    const data = campaignRecord.campaignData;
    setFormData({
      campaignName: data.campaignName || '',
      channels: data.channels || [],
      productName: data.product?.name || '',
      productDescription: data.product?.description || '',
      features: data.product?.features?.join('\n') || '',
      pricing: data.product?.pricing || '',
      targetDemographics: data.targetAudience?.demographics || '',
      targetInterests: data.targetAudience?.interests?.join(', ') || '',
      painPoints: data.targetAudience?.painPoints?.join(', ') || '',
      budget: data.budget?.toString() || '',
      startDate: data.timeline?.startDate || '',
      endDate: data.timeline?.endDate || '',
      goals: data.goals?.join('\n') || '',
      brandVoice: data.brandVoice || 'professional',
      companyName: data.companyInfo?.companyName || '',
      replyToEmail: data.companyInfo?.replyToEmail || '',
      companyPhone: data.companyInfo?.phone || '',
      companyWebsite: data.companyInfo?.website || '',
      bookingLink: data.companyInfo?.bookingLink || '',
      twitter: data.companyInfo?.socialMedia?.twitter || '',
      linkedin: data.companyInfo?.socialMedia?.linkedin || '',
      facebook: data.companyInfo?.socialMedia?.facebook || '',
      instagram: data.companyInfo?.socialMedia?.instagram || '',
    });
  };

  const handleChannelToggle = (channel: string) => {
    setFormData(prev => ({
      ...prev,
      channels: prev.channels.includes(channel)
        ? prev.channels.filter(c => c !== channel)
        : [...prev.channels, channel]
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setExecuting(true);

    try {
      // Build updated campaign request
      const campaignRequest: any = {
        campaignId: campaign.campaignData.campaignId,
        campaignName: formData.campaignName,
        channels: formData.channels,
        product: {
          name: formData.productName,
          description: formData.productDescription,
          features: formData.features.split('\n').filter(f => f.trim()),
          pricing: formData.pricing,
        },
        targetAudience: {
          demographics: formData.targetDemographics,
          interests: formData.targetInterests.split(',').map(i => i.trim()),
          painPoints: formData.painPoints.split(',').map(p => p.trim()),
        },
        budget: parseFloat(formData.budget),
        timeline: {
          startDate: formData.startDate,
          endDate: formData.endDate,
        },
        goals: formData.goals.split('\n').filter(g => g.trim()),
        brandVoice: formData.brandVoice,
      };

      // Add company info if provided
      if (formData.companyName || formData.replyToEmail || formData.companyPhone) {
        campaignRequest.companyInfo = {
          companyName: formData.companyName || undefined,
          replyToEmail: formData.replyToEmail || undefined,
          phone: formData.companyPhone || undefined,
          website: formData.companyWebsite || undefined,
          bookingLink: formData.bookingLink || undefined,
          socialMedia: {
            twitter: formData.twitter || undefined,
            linkedin: formData.linkedin || undefined,
            facebook: formData.facebook || undefined,
            instagram: formData.instagram || undefined,
          },
        };
      }

      // Update campaign
      const updateRes = await fetch(`/api/campaigns/update?id=${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ campaignData: campaignRequest }),
      });

      const updateData = await updateRes.json();

      if (!updateData.success) {
        throw new Error(updateData.error);
      }

      // If resend is checked, re-execute the campaign
      if (resendAfterEdit) {
        console.log('Resending campaign...');
        const resendRes = await fetch(`/api/campaigns/resend?id=${id}`, {
          method: 'POST',
        });

        const resendData = await resendRes.json();
        
        if (resendData.success) {
          alert(`Campaign updated and resent successfully!\n\nResults:\n- Emails sent: ${resendData.results.emailResults?.sent || 0}\n- SMS sent: ${resendData.results.smsResults?.sent || 0}\n- Instagram posts: ${resendData.results.instagramResults?.success ? 1 : 0}`);
          router.push('/campaigns');
        } else {
          alert(`Campaign updated, but resend failed: ${resendData.error}\n\nYou can manually resend from the campaign details page.`);
          router.push(`/campaigns/${id}`);
        }
      } else {
        alert('Campaign updated successfully!');
        router.push(`/campaigns/${id}`);
      }

    } catch (error) {
      console.error('Update failed:', error);
      alert('Failed to update campaign: ' + (error instanceof Error ? error.message : 'Unknown error'));
    } finally {
      setExecuting(false);
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
        <title>Edit Campaign - {campaign.campaignName}</title>
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
              <Link href={`/campaigns/${id}`} className="text-blue-600 font-medium">
                View Campaign
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="mb-6">
          <Link href={`/campaigns/${id}`} className="text-blue-600 hover:text-blue-800">
            ← Back to campaign details
          </Link>
        </div>

        <h1 className="text-3xl font-bold text-gray-900 mb-2">Edit Campaign</h1>
        <p className="text-gray-600 mb-8">Update campaign details and optionally resend to recipients</p>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Info */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Basic Information</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Campaign Name*</label>
                <input
                  type="text"
                  required
                  value={formData.campaignName}
                  onChange={(e) => setFormData({...formData, campaignName: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Channels*</label>
                <div className="flex space-x-4">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.channels.includes('email')}
                      onChange={() => handleChannelToggle('email')}
                      className="mr-2"
                    />
                    ✉️ Email
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.channels.includes('sms')}
                      onChange={() => handleChannelToggle('sms')}
                      className="mr-2"
                    />
                    📱 SMS
                  </label>
                </div>
              </div>
            </div>
          </div>

          {/* Product Info */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Product Information</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Product Name*</label>
                <input
                  type="text"
                  required
                  value={formData.productName}
                  onChange={(e) => setFormData({...formData, productName: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Description*</label>
                <textarea
                  required
                  value={formData.productDescription}
                  onChange={(e) => setFormData({...formData, productDescription: e.target.value})}
                  rows={3}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Features (one per line)*</label>
                <textarea
                  required
                  value={formData.features}
                  onChange={(e) => setFormData({...formData, features: e.target.value})}
                  rows={4}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Pricing</label>
                <input
                  type="text"
                  value={formData.pricing}
                  onChange={(e) => setFormData({...formData, pricing: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                />
              </div>
            </div>
          </div>

          {/* Target Audience */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Target Audience</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Demographics*</label>
                <input
                  type="text"
                  required
                  value={formData.targetDemographics}
                  onChange={(e) => setFormData({...formData, targetDemographics: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Interests (comma-separated)*</label>
                <input
                  type="text"
                  required
                  value={formData.targetInterests}
                  onChange={(e) => setFormData({...formData, targetInterests: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Pain Points (comma-separated)*</label>
                <input
                  type="text"
                  required
                  value={formData.painPoints}
                  onChange={(e) => setFormData({...formData, painPoints: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                />
              </div>
            </div>
          </div>

          {/* Campaign Details */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Campaign Details</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Budget ($)*</label>
                <input
                  type="number"
                  required
                  value={formData.budget}
                  onChange={(e) => setFormData({...formData, budget: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Start Date*</label>
                  <input
                    type="date"
                    required
                    value={formData.startDate}
                    onChange={(e) => setFormData({...formData, startDate: e.target.value})}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">End Date*</label>
                  <input
                    type="date"
                    required
                    value={formData.endDate}
                    onChange={(e) => setFormData({...formData, endDate: e.target.value})}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Goals (one per line)*</label>
                <textarea
                  required
                  value={formData.goals}
                  onChange={(e) => setFormData({...formData, goals: e.target.value})}
                  rows={3}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                />
              </div>
            </div>
          </div>

          {/* Company Contact Info - same as create page */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">📞 Contact Information (Optional)</h2>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Company Name</label>
                  <input
                    type="text"
                    value={formData.companyName}
                    onChange={(e) => setFormData({...formData, companyName: e.target.value})}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Reply-To Email</label>
                  <input
                    type="email"
                    value={formData.replyToEmail}
                    onChange={(e) => setFormData({...formData, replyToEmail: e.target.value})}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Phone</label>
                  <input
                    type="tel"
                    value={formData.companyPhone}
                    onChange={(e) => setFormData({...formData, companyPhone: e.target.value})}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Website</label>
                  <input
                    type="url"
                    value={formData.companyWebsite}
                    onChange={(e) => setFormData({...formData, companyWebsite: e.target.value})}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Booking Link</label>
                <input
                  type="url"
                  value={formData.bookingLink}
                  onChange={(e) => setFormData({...formData, bookingLink: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                />
              </div>
            </div>
          </div>

          {/* Resend Option */}
          <div className="bg-blue-50 p-6 rounded-lg border-2 border-blue-200">
            <label className="flex items-start">
              <input
                type="checkbox"
                checked={resendAfterEdit}
                onChange={(e) => setResendAfterEdit(e.target.checked)}
                className="mt-1 mr-3"
              />
              <div>
                <span className="font-medium text-gray-900">Resend campaign after updating</span>
                <p className="text-sm text-gray-600 mt-1">
                  Check this to re-execute the campaign with updated content and send to original recipients
                </p>
              </div>
            </label>
          </div>

          <div className="flex justify-end space-x-4">
            <Link
              href={`/campaigns/${id}`}
              className="px-6 py-3 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={executing}
              className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
            >
              {executing ? 'Updating...' : resendAfterEdit ? 'Update & Resend' : 'Update Campaign'}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
