```text
High-level plan

I’d do these in four phases, highest SEO value first. Each is independent, so you can reorder them.

Phase 1: SEO foundation (biggest local-search impact)

Per-page head template. Every page gets a unique title (about 60 characters), a meta description, a canonical URL, Open Graph and Twitter tags, and one <h1>. The Gold Coast suburb names go into the visible copy where they’re true, not just into tags.

LocalBusiness schema. One JSON-LD block on the home and About pages:

HQ: Robina.
Service areas: Burleigh Heads, Varsity Lakes, Miami, Broadbeach, Mermaid Beach, Southport and Greater Gold Coast.
Also listed: phone, hours, logo, and your LinkedIn, YouTube and Facebook URLs.

ITServices.html would also get Service schema. Blog posts would get Article schema.

sitemap.xml and robots.txt. The menu is built by JavaScript, so the sitemap is how Google reliably discovers every page. I’d write a tiny local script that builds the sitemap from your five JSON files, with no build framework.

Off-site, which matters as much as the code:

Claim your Google Business Profile. It is the biggest lever for appearing in the local map results.
Verify the site in Google Search Console and Bing Webmaster Tools.

Content note. I’d avoid creating one thin page per suburb, which Google tends to treat as doorway pages. Either write a few substantial local pages or mention suburbs naturally on the existing pages.

Phase 2: Shared site layer

Create site.css and site.js holding the canvas background, vignette, grain overlay, scroll-reveal and the right-hand dot nav. The dots would be built automatically from each page’s sections.

Each page then carries only its content. Today every page copies about 25 KB of identical CSS and script. I’d do this before you add the blog, projects and industries pages, so they start lean.

Phase 3: GA4, GTM and ad pixels
PostHog: keep it as is.
GA4: add it as one PROVIDERS block. It’s worth having for Google Ads and the Search Console link.
LinkedIn, Meta, YouTube ads: either direct pixels in PROVIDERS or one GTM container. Direct is simpler. GTM is better if marketing will manage tags without touching code.
Conversions: mark cta_click, email_click and phone_click as your conversion events, since those are already tracked.
Consent: ad pixels set cookies, so we’d add a small consent gate in analytics.js and a privacy policy page before switching them on.
Phase 4: Site search

“Google and other site searches” can mean two things:

Being found by search engines. Phase 1 covers this.
A search box on the site. I’d recommend Pagefind. It’s static, free, has no backend, and adds a search icon to the menu. It needs a one-line indexing command whenever content changes, which can be automated later.
What I’d need from you
Business details: legal name, ABN, phone, opening hours, and whether to show a street address or list the business as service-area only.
Logo and social URLs: a logo file and your LinkedIn, YouTube and Facebook links.
Phase 3 IDs: GA4, GTM, Meta, LinkedIn and Google Ads, only when you’re ready.
Contact email: which of hello@unitycloud.com and hello@unitycloud.ai is correct.

Send the business details and I’ll start Phase 1.

```
