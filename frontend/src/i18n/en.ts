import type { TranslationKey } from "./ko";

const en: Record<TranslationKey, string> = {
  // Navigation
  "nav.dashboard": "Dashboard",
  "nav.conversations": "Messages",
  "nav.customers": "Customers",
  "nav.bookings": "Bookings",
  "nav.payments": "Payments",
  "nav.procedures": "Procedures",
  "nav.crm": "CRM",
  "nav.analytics": "Analytics",
  "nav.knowledge": "Knowledge",
  "nav.aiLab": "AI Lab",
  "nav.settings": "Settings",
  "nav.logout": "Log out",
  "nav.mainNav": "Main navigation",
  "nav.openMenu": "Open menu",
  "nav.closeMenu": "Close menu",
  "nav.navMenu": "Navigation menu",

  // Common actions
  "common.save": "Save",
  "common.cancel": "Cancel",
  "common.delete": "Delete",
  "common.edit": "Edit",
  "common.add": "Add",
  "common.search": "Search",
  "common.filter": "Filter",
  "common.all": "All",
  "common.back": "Back",
  "common.backToList": "Back to list",
  "common.loading": "Loading...",
  "common.noData": "No data available",
  "common.error": "An error occurred",
  "common.retry": "Retry",
  "common.confirm": "Confirm",
  "common.close": "Close",
  "common.copy": "Copy",
  "common.total": "Total",
  "common.status": "Status",

  // Auth
  "auth.login": "Log in",
  "auth.register": "Sign up",
  "auth.email": "Email",
  "auth.password": "Password",
  "auth.name": "Name",
  "auth.clinicName": "Clinic name",
  "auth.clinicSlug": "Clinic slug",
  "auth.loginFailed": "Invalid email or password",

  // Dashboard
  "dashboard.title": "Dashboard",
  "dashboard.totalConversations": "Total Conversations",
  "dashboard.activeConversations": "Active",
  "dashboard.todayMessages": "Today's Messages",
  "dashboard.aiHandled": "AI Handled",

  // Conversations
  "conversations.title": "Conversations",
  "conversations.empty": "No conversations",
  "conversations.selectConversation": "Select a conversation",
  "conversations.sendMessage": "Type a message...",
  "conversations.send": "Send",
  "conversations.aiMode": "AI Mode",
  "conversations.manualMode": "Manual Mode",
  "conversations.resolve": "Resolve",
  "conversations.backToList": "Back to conversation list",

  // Customers
  "customers.title": "Customer Management",
  "customers.empty": "No customers",
  "customers.detail": "Customer Detail",
  "customers.name": "Name",
  "customers.phone": "Phone",
  "customers.email": "Email",
  "customers.country": "Country",
  "customers.language": "Language",
  "customers.notes": "Notes",
  "customers.totalBookings": "Total Bookings",
  "customers.totalPayments": "Total Payments",

  // Bookings
  "bookings.title": "Booking Management",
  "bookings.empty": "No bookings",
  "bookings.status.all": "All",
  "bookings.status.pending": "Pending",
  "bookings.status.confirmed": "Confirmed",
  "bookings.status.completed": "Completed",
  "bookings.status.cancelled": "Cancelled",
  "bookings.status.noshow": "No-show",
  "bookings.complete": "Complete",
  "bookings.cancelBooking": "Cancel booking",

  // Payments
  "payments.title": "Payment Management",
  "payments.empty": "No payment records",
  "payments.status.all": "All",
  "payments.status.pending": "Pending",
  "payments.status.completed": "Completed",
  "payments.status.refunded": "Refunded",
  "payments.status.cancelled": "Cancelled",
  "payments.amount": "Amount",
  "payments.method": "Payment method",

  // Procedures
  "procedures.title": "Procedure Management",
  "procedures.tab.procedures": "Procedures",
  "procedures.tab.pricing": "Pricing",
  "procedures.empty": "No procedures registered",
  "procedures.deletePrice": "Delete price",

  // CRM
  "crm.title": "CRM",
  "crm.tab.events": "CRM Events",
  "crm.tab.surveys": "Satisfaction Surveys",
  "crm.events.empty": "No CRM events",
  "crm.events.cancel": "Cancel",
  "crm.events.cancelEvent": "Cancel event",
  "crm.events.scheduled": "Scheduled",
  "crm.events.sent": "Sent",
  "crm.events.completed": "Completed",
  "crm.events.cancelled": "Cancelled",
  "crm.events.failed": "Failed",
  "crm.surveys.empty": "No survey data",
  "crm.surveys.total": "Total Surveys",
  "crm.surveys.avgOverall": "Avg. Overall",
  "crm.surveys.service": "Service",
  "crm.surveys.result": "Result",
  "crm.surveys.nps": "NPS",
  "crm.surveys.revisit": "Revisit",

  // Analytics
  "analytics.title": "Analytics",
  "analytics.tab.overview": "Overview",
  "analytics.tab.conversations": "Conversations",
  "analytics.tab.revenue": "Revenue",
  "analytics.tab.satisfaction": "Satisfaction",
  "analytics.tab.ai": "AI Performance",

  // Knowledge
  "knowledge.title": "Knowledge Management",
  "knowledge.tab.responses": "Response Library",
  "knowledge.tab.terms": "Medical Terms",
  "knowledge.editAnswer": "Edit answer",
  "knowledge.deleteAnswer": "Delete answer",
  "knowledge.deleteTerm": "Delete term",

  // AI Lab
  "aiLab.title": "AI Lab",
  "aiLab.tab.personas": "AI Personas",
  "aiLab.tab.abTests": "A/B Tests",
  "aiLab.tab.simulations": "Simulations",

  // Settings
  "settings.title": "Settings",
  "settings.tab.accounts": "Messenger Accounts",
  "settings.tab.personas": "AI Personas",
  "settings.tab.profile": "Profile",
  "settings.copyWebhookUrl": "Copy webhook URL",
  "settings.editAccount": "Edit messenger account",
  "settings.deleteAccount": "Delete messenger account",
  "settings.deletePersona": "Delete AI persona",

  // Settlements
  "settlements.title": "Settlement Management",
  "settlements.empty": "No settlement records",

  // Pagination
  "pagination.showing": "{start}-{end} of {total}",
  "pagination.prev": "Previous",
  "pagination.next": "Next",

  // Error boundary
  "error.title": "Something went wrong",
  "error.retry": "Try again",

  // Theme
  "theme.light": "Light mode",
  "theme.dark": "Dark mode",
  "theme.system": "System default",

  // Satisfaction labels (accessibility)
  "satisfaction.green": "Very satisfied",
  "satisfaction.yellow": "Satisfied",
  "satisfaction.orange": "Neutral",
  "satisfaction.red": "Dissatisfied",

  // Command palette
  "command.title": "Command",
  "command.placeholder": "Search pages...",
  "command.navigation": "Navigation",
  "command.actions": "Quick Actions",
  "command.noResults": "No results",

  // Notifications
  "notification.escalation": "Escalation alert",
  "notification.satisfactionWarning": "Satisfaction warning",
  "notification.deliveryFailed": "Message delivery failed",
  "notification.quotaWarning": "LLM cost warning",
  "notification.quotaExceeded": "LLM cost limit exceeded",
  "notification.markAllRead": "Mark all read",
  "notification.empty": "No notifications",

  // AI Feedback
  "feedback.helpful": "Helpful",
  "feedback.notHelpful": "Not helpful",
  "feedback.thanks": "Thanks for the feedback",

  // LLM Usage
  "llmUsage.title": "LLM Costs",
  "llmUsage.tab.summary": "Monthly Summary",
  "llmUsage.tab.daily": "Daily Trend",
  "llmUsage.tab.quota": "Budget",
  "llmUsage.totalCost": "Total Cost",
  "llmUsage.totalTokens": "Total Tokens",
  "llmUsage.operation": "Operation",
  "llmUsage.count": "Calls",
  "llmUsage.inputTokens": "Input Tokens",
  "llmUsage.outputTokens": "Output Tokens",
  "llmUsage.cost": "Cost (USD)",
  "llmUsage.date": "Date",
  "llmUsage.quota": "Monthly Budget",
  "llmUsage.currentUsage": "Current Usage",
  "llmUsage.usagePercent": "Usage %",
  "llmUsage.setQuota": "Set Budget",
  "llmUsage.noQuota": "No budget set",
};

export default en;
