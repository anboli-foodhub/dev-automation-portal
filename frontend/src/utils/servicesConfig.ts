import { ServiceItem } from '../types';

export const SERVICES: ServiceItem[] = [
  // JIRA
  {
    id: 'jira-view-ticket',
    title: 'View JIRA Ticket',
    description: 'Retrieve detailed information, assignee, comments, and sprint status for a ticket.',
    category: 'jira',
    icon: 'Ticket',
    path: '/service/jira-view-ticket',
  },
  {
    id: 'jira-open-tickets',
    title: 'Open JIRA Tickets',
    description: 'List Backlog, To Do, and Dev In Progress tickets assigned to you.',
    category: 'jira',
    icon: 'ListChecks',
    path: '/service/jira-open-tickets',
  },
  {
    id: 'jira-time-tracker',
    title: 'Time Tracker Dashboard',
    description: 'View daily, weekly, and monthly logged hours and remaining time totals.',
    category: 'jira',
    icon: 'Clock',
    path: '/service/jira-time-tracker',
  },
  {
    id: 'jira-add-worklog',
    title: 'Add JIRA Worklog',
    description: 'Log hours worked against a specific ticket with custom comments.',
    category: 'jira',
    icon: 'CalendarPlus',
    path: '/service/jira-add-worklog',
  },
  {
    id: 'jira-delete-worklog',
    title: 'Delete JIRA Worklog',
    description: 'View and remove existing worklog hours from a ticket.',
    category: 'jira',
    icon: 'CalendarX',
    path: '/service/jira-delete-worklog',
  },
  {
    id: 'jira-sprint-board',
    title: 'Sprint Board Analytics',
    description: 'Check active sprint progression, backlog, and sprint burndown summary.',
    category: 'jira',
    icon: 'BarChart4',
    path: '/service/jira-sprint-board',
  },
  {
    id: 'jira-push-to-qa',
    title: 'Push to QA',
    description: 'Comment, reassign to Omprakash, and notify Code Red - Internal on Cliq.',
    category: 'jira',
    icon: 'Rocket',
    path: '/service/jira-push-to-qa',
  },

  // ITSM
  {
    id: 'itsm-dashboard',
    title: 'ITSM Ticket Hub',
    description: 'Browse recent ITSM tickets and approve or comment directly from the list.',
    category: 'itsm',
    icon: 'ShieldAlert',
    path: '/itsm/tickets',
  },
  {
    id: 'itsm-raise-request',
    title: 'Raise ITSM Request',
    description: 'Submit technical service tickets with dynamic categorization and file attachments.',
    category: 'itsm',
    icon: 'FilePlus2',
    path: '/service/itsm-raise-request',
  },
  {
    id: 'itsm-release-ticket',
    title: 'Release Ticket',
    description: 'File a Release Management request for MS, MSWEB, or FALCON-BOBCRM.',
    category: 'itsm',
    icon: 'Rocket',
    path: '/itsm/release-ticket',
  },

  // GITHUB
  {
    id: 'github-view-pr',
    title: 'View Pull Request',
    description: 'Lookup open pull request details, file changes, and review status.',
    category: 'github',
    icon: 'GitPullRequest',
    path: '/service/github-view-pr',
  },
  {
    id: 'github-approve-pr',
    title: 'Approve Pull Request',
    description: 'View the Files Changed diff and submit a line-commented approval, comment, or request-changes review.',
    category: 'github',
    icon: 'CheckSquare',
    path: '/github/pr',
  },
  {
    id: 'github-create-branch',
    title: 'Create Branch',
    description: 'Suggest a branch name from a JIRA ticket and create it on any accessible repo.',
    category: 'github',
    icon: 'FolderPlus',
    path: '/github/create-branch',
  },
  {
    id: 'github-tag-creator',
    title: 'Create Release Tag',
    description: 'Auto-suggests the next SIT/main tag from your repo\'s own convention.',
    category: 'github',
    icon: 'Tag',
    path: '/github/create-tag',
  },
  {
    id: 'github-compare-tags',
    title: 'Compare Tags',
    description: 'Diff two real tags on any accessible repo to review the commit delta.',
    category: 'github',
    icon: 'Diff',
    path: '/github/compare-tags',
  },

  // DEVOPS
  {
    id: 'jenkins-jobs',
    title: 'Jenkins Jobs Panel',
    description: 'Browse Jenkins job folders and build statuses (read-only).',
    category: 'devops',
    icon: 'Cpu',
    path: '/devops/jenkins',
  },
  {
    id: 'octopus-deploy',
    title: 'Octopus Deployments',
    description: 'Browse project groups, environments, and release/environment deployment status.',
    category: 'devops',
    icon: 'Activity',
    path: '/octopus',
  },

  // CRM
  {
    id: 'crm-franchise-creation',
    title: 'Franchise Creation',
    description: 'Initialize a new franchise location with validated input fields.',
    category: 'crm',
    icon: 'Store',
    path: '/service/crm-franchise-creation',
  },
  {
    id: 'crm-order-lookup',
    title: 'CRM Order Lookup',
    description: 'Search single or multiple orders via numeric IDs or bulk CSV parsing.',
    category: 'crm',
    icon: 'SearchCode',
    path: '/service/crm-order-lookup',
  },
  {
    id: 'crm-reseller-creation',
    title: 'Reseller Onboarding',
    description: 'Onboard commercial resellers checking against duplication of Tax IDs.',
    category: 'crm',
    icon: 'UserPlus',
    path: '/service/crm-reseller-creation',
  },
  {
    id: 'crm-social-post',
    title: 'Raise Social Media Post',
    description: 'Schedule marketing posts with media attachments and scheduling parameters.',
    category: 'crm',
    icon: 'Share2',
    path: '/service/crm-social-post',
  },

  // REPORTS
  {
    id: 'weekly-report',
    title: 'Weekly Report',
    description: 'Browse the foodhub weekly report sheet and its recent tabs.',
    category: 'reports',
    icon: 'FileBarChart',
    path: '/service/weekly-report',
  },
];

export const CATEGORIES = [
  { id: 'all', title: 'All Services', icon: 'Layers' },
  { id: 'jira', title: 'JIRA Integration', icon: 'Ticket' },
  { id: 'github', title: 'GitHub Ops', icon: 'GitPullRequest' },
  { id: 'itsm', title: 'ITSM Portal', icon: 'ShieldAlert' },
  { id: 'crm', title: 'BOB CRM', icon: 'Store' },
  { id: 'devops', title: 'DevOps & CI/CD', icon: 'Cpu' },
  { id: 'reports', title: 'Reports', icon: 'FileBarChart' },
];
