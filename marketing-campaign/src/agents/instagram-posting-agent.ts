/**
 * Instagram Posting Agent
 * Posts campaign content to Instagram feed and stories
 * Requires Instagram Graph API access
 */

export interface InstagramPost {
  caption: string;
  imageUrl?: string;
  hashtags: string[];
  callToAction?: string;
}

interface FacebookGraphError {
  message: string;
  type: string;
  code: number;
}

interface ContainerResponse {
  id: string;
  error?: FacebookGraphError;
}

interface PublishResponse {
  id: string;
  error?: FacebookGraphError;
}

export class InstagramPostingAgent {
  private accessToken: string;
  private instagramAccountId: string;

  constructor() {
    this.accessToken = process.env.INSTAGRAM_ACCESS_TOKEN || '';
    this.instagramAccountId = process.env.INSTAGRAM_ACCOUNT_ID || '';
  }

  /**
   * Check if Instagram is configured
   */
  isConfigured(): boolean {
    return !!(this.accessToken && this.instagramAccountId);
  }

  /**
   * Generate Instagram post content from campaign
   */
  generatePostContent(campaignData: any): InstagramPost {
    const product = campaignData.product;
    const hashtags = [
      '#marketing',
      '#business',
      '#startup',
      ...campaignData.targetAudience.interests.map((i: string) => 
        '#' + i.toLowerCase().replace(/\s+/g, '')
      )
    ].slice(0, 10); // Instagram allows max 30, we'll use 10

    const caption = `
✨ ${product.name} ✨

${product.description}

🎯 Perfect for: ${campaignData.targetAudience.demographics}

Key Features:
${product.features.slice(0, 3).map((f: string) => `✓ ${f}`).join('\n')}

${product.pricing ? `💰 ${product.pricing}` : ''}

${campaignData.companyInfo?.website ? `🔗 Link in bio: ${campaignData.companyInfo.website}` : ''}

${hashtags.join(' ')}
`.trim();

    return {
      caption,
      hashtags,
      callToAction: campaignData.goals[0],
    };
  }

  /**
   * Post to Instagram Feed
   */
  async postToFeed(content: InstagramPost): Promise<{ success: boolean; postId?: string; error?: string }> {
    if (!this.isConfigured()) {
      console.warn('⚠️  Instagram posting skipped - Not configured');
      console.log('   To enable Instagram: Set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID in .env');
      return {
        success: false,
        error: 'Instagram not configured'
      };
    }

    try {
      console.log('📸 Posting to Instagram feed...');
      console.log('📝 Caption:', content.caption.substring(0, 100) + '...');
      
      // Step 1: Create container (prepare post)
      const containerResponse = await fetch(
        `https://graph.facebook.com/v18.0/${this.instagramAccountId}/media`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            caption: content.caption,
            access_token: this.accessToken,
          })
        }
      );

      const containerData = await containerResponse.json() as ContainerResponse;

      if (!containerResponse.ok || containerData.error) {
        throw new Error(containerData.error?.message || 'Failed to create Instagram container');
      }

      const creationId = containerData.id;
      console.log(`   Container created: ${creationId}`);

      // Step 2: Publish the post
      const publishResponse = await fetch(
        `https://graph.facebook.com/v18.0/${this.instagramAccountId}/media_publish`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            creation_id: creationId,
            access_token: this.accessToken,
          })
        }
      );

      const publishData = await publishResponse.json() as PublishResponse;

      if (!publishResponse.ok || publishData.error) {
        throw new Error(publishData.error?.message || 'Failed to publish Instagram post');
      }

      console.log(`✅ Instagram post published: ${publishData.id}`);
      console.log(`   View at: https://www.instagram.com/p/${this.getShortcode(publishData.id)}`);
      
      return {
        success: true,
        postId: publishData.id,
      };

    } catch (error) {
      console.error('❌ Instagram posting failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Convert Instagram media ID to shortcode for URL
   */
  private getShortcode(mediaId: string): string {
    // Simplified - in production you'd get this from the API response
    return mediaId.split('_')[0];
  }

  /**
   * Post to Instagram Story
   */
  async postToStory(content: InstagramPost): Promise<{ success: boolean; storyId?: string; error?: string }> {
    if (!this.isConfigured()) {
      return {
        success: false,
        error: 'Instagram not configured'
      };
    }

    try {
      console.log('📱 Posting to Instagram story...');
      
      // Note: Stories require an image URL
      // For now, we'll skip story posting unless an image is provided
      console.log('   Story posting requires image URL (skipped for text-only campaigns)');
      
      return {
        success: false,
        error: 'Story posting requires image URL',
      };

    } catch (error) {
      console.error('❌ Instagram story posting failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Execute Instagram campaign (post + story)
   */
  async executeCampaign(campaignData: any): Promise<{
    feedPost?: any;
    story?: any;
  }> {
    const content = this.generatePostContent(campaignData);

    const feedPost = await this.postToFeed(content);
    const story = await this.postToStory(content);

    return {
      feedPost,
      story,
    };
  }
}
