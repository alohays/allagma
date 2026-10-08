import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  site: 'https://alohays.github.io',
  base: '/allagma',
  trailingSlash: 'always',
  integrations: [starlight({
    title: 'Allagma',
    description: 'Research workflows for coding agents. Pin the plan, retain every attempt, and connect claims to evidence.',
    logo: { src: './src/assets/mark.svg', replacesTitle: false },
    favicon: '/favicon.svg',
    social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/alohays/allagma' }],
    customCss: ['./src/styles/allagma.css'],
    components: { Hero: './src/components/LaunchHero.astro' },
    head: [
      { tag: 'meta', attrs: { property: 'og:image', content: 'https://alohays.github.io/allagma/generated/media/social-preview.png' } },
      { tag: 'meta', attrs: { name: 'twitter:card', content: 'summary_large_image' } },
    ],
    sidebar: [
      { label: 'Start here', items: [
        { label: 'Your first study', slug: 'guides/first-study' },
        { label: 'Watch the workflow', slug: 'demo' },
        { label: 'The records behind a study', slug: 'reference/concepts' },
      ]},
      { label: 'Work with Allagma', items: [
        { label: 'Start a native study', slug: 'guides/native-study' },
        { label: 'Resume and reproduce', slug: 'guides/reproduce' },
        { label: 'Research workspaces', slug: 'guides/workspaces' },
        { label: 'Resource supervision', slug: 'guides/resources' },
        { label: 'Updates and rollback', slug: 'guides/versioning' },
        { label: 'Artifacts and downloads', slug: 'guides/artifacts' },
        { label: 'Troubleshooting', slug: 'guides/troubleshooting' },
      ]},
      { label: 'Study showcase', items: [
        { label: 'Browse the studies', slug: 'studies' },
        { label: 'Offline toy study', slug: 'studies/toy' },
        { label: 'CORE CULP reproduction', slug: 'studies/core-culp' },
        { label: 'Modular addition', slug: 'studies/modular-addition' },
        { label: 'Weight EMA', slug: 'studies/ema-schedule' },
      ]},
      { label: 'Reference', collapsed: true, items: [
        { label: 'CLI overview', slug: 'reference/cli' },
        { label: 'All command flags', slug: 'reference/commands' },
        { label: 'Architecture', slug: 'reference/architecture' },
        { label: 'Evidence contracts', slug: 'reference/contracts' },
        { label: 'Study-owned programs', slug: 'reference/study-programs' },
      ]},
      { label: 'Evidence and limits', collapsed: true, items: [
        { label: 'Host qualification', slug: 'evidence/hosts' },
        { label: 'Twelve-session comparison', slug: 'evidence/comparison' },
        { label: 'Acceptance scope', slug: 'evidence/acceptance' },
        { label: 'I1–I5 evidence', slug: 'evidence/implementation' },
        { label: 'Release 0.3.0rc2', slug: 'releases/0.3.0rc2' },
      ]},
      { label: 'Contribute', collapsed: true, items: [
        { label: 'Contribution guide', slug: 'contributing' },
        { label: 'Small contributions', slug: 'contributing/starter-tasks' },
        { label: 'Author a module', slug: 'contributing/modules' },
        { label: 'Roadmap', slug: 'project/roadmap' },
        { label: 'Support', slug: 'project/support' },
        { label: 'Security', slug: 'project/security' },
        { label: 'Licenses', slug: 'project/licenses' },
        { label: 'Governance', slug: 'project/governance' },
        { label: 'Code of conduct', slug: 'project/conduct' },
      ]},
    ],
  })],
});
