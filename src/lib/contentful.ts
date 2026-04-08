import { createClient } from 'contentful';

export const contentfulClient = createClient({
  space: process.env.CONTENTFUL_SPACE_ID || 'dummy_space',
  accessToken: process.env.CONTENTFUL_ACCESS_TOKEN || 'dummy_token',
});
