/** Brand icon slugs — local SVGs in /static/brand-icons/ (CDN fallback). */
window.NEXUS_LOGO_SLUG = {
  hubspot: 'hubspot',
  salesforce: 'salesforce',
  zendesk: 'zendesk',
  freshdesk: 'freshdesk',
  pipedrive: 'pipedrive',
  zoho: 'zoho',
  'help-scout': 'helpscout',
  front: 'front',
  twilio: 'twilio',
  'amazon-connect': 'amazonaws',
  five9: 'five9',
  genesys: 'genesys',
  talkdesk: 'talkdesk',
  zoom: 'zoom',
  vonage: 'vonage',
  ringcentral: 'ringcentral',
  snowflake: 'snowflake',
  bigquery: 'googlebigquery',
  tableau: 'tableau',
  'power-bi': 'powerbi',
  amplitude: 'amplitude',
  workday: 'workday',
  bamboohr: 'bamboohr',
  adp: 'adp',
  gusto: 'gusto',
  jira: 'jira',
  asana: 'asana',
  monday: 'mondaydotcom',
  linear: 'linear',
  pagerduty: 'pagerduty',
  n8n: 'n8n',
  zapier: 'zapier',
  epic: 'epicgames',
  copper: 'copper',
  'azure-devops': 'azuredevops',
  slack: 'slack',
  github: 'github',
  notion: 'notion',
  stripe: 'stripe',
  shopify: 'shopify',
  intercom: 'intercom',
  servicenow: 'servicenow',
  dynamics: 'microsoft',
  meta: 'meta',
  whatsapp: 'whatsapp',
};

window.nexusLogoUrl = function (id, color = 'a0a0b8') {
  const slug = window.NEXUS_LOGO_SLUG[id] || window.NEXUS_LOGO_SLUG[id?.replace(/_/g, '-')] || null;
  if (!slug) return null;
  return `/static/brand-icons/${slug}.svg`;
};

window.nexusLogoFallback = function (id, color = 'a0a0b8') {
  const slug = window.NEXUS_LOGO_SLUG[id] || window.NEXUS_LOGO_SLUG[id?.replace(/_/g, '-')] || null;
  if (!slug) return null;
  return `https://cdn.simpleicons.org/${slug}/${color}`;
};

window.nexusLogoImg = function (id, size = 22, alt = '') {
  const src = window.nexusLogoUrl(id);
  const fb = window.nexusLogoFallback(id);
  if (!src) return '';
  const esc = (s) => s.replace(/"/g, '&quot;');
  return `<img src="${esc(src)}" data-fallback="${esc(fb || '')}" alt="${esc(alt)}" width="${size}" height="${size}" loading="lazy" onerror="if(this.dataset.fallback&&!this.dataset.tried){this.dataset.tried=1;this.src=this.dataset.fallback}else{this.style.display='none';this.nextElementSibling?.classList.add('show')}">`;
};

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('img[data-fallback]').forEach((img) => {
    img.addEventListener('error', () => {
      if (img.dataset.fallback && !img.dataset.tried) {
        img.dataset.tried = '1';
        img.src = img.dataset.fallback;
      }
    }, { once: true });
  });
});
