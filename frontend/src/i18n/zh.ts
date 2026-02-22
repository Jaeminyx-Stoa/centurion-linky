import type { TranslationKey } from "./ko";

const zh: Record<TranslationKey, string> = {
  // Navigation
  "nav.dashboard": "仪表盘",
  "nav.conversations": "消息",
  "nav.customers": "客户",
  "nav.bookings": "预约",
  "nav.payments": "支付",
  "nav.procedures": "项目",
  "nav.crm": "CRM",
  "nav.analytics": "统计",
  "nav.knowledge": "知识库",
  "nav.aiLab": "AI Lab",
  "nav.settings": "设置",
  "nav.logout": "退出登录",
  "nav.mainNav": "主导航",
  "nav.openMenu": "打开菜单",
  "nav.closeMenu": "关闭菜单",
  "nav.navMenu": "导航菜单",

  // Common actions
  "common.save": "保存",
  "common.cancel": "取消",
  "common.delete": "删除",
  "common.edit": "编辑",
  "common.add": "添加",
  "common.search": "搜索",
  "common.filter": "筛选",
  "common.all": "全部",
  "common.back": "返回",
  "common.backToList": "返回列表",
  "common.loading": "加载中...",
  "common.noData": "暂无数据",
  "common.error": "发生错误",
  "common.retry": "重试",
  "common.confirm": "确认",
  "common.close": "关闭",
  "common.copy": "复制",
  "common.total": "合计",
  "common.status": "状态",

  // Auth
  "auth.login": "登录",
  "auth.register": "注册",
  "auth.email": "邮箱",
  "auth.password": "密码",
  "auth.name": "姓名",
  "auth.clinicName": "诊所名称",
  "auth.clinicSlug": "诊所标识",
  "auth.loginFailed": "邮箱或密码不正确",

  // Dashboard
  "dashboard.title": "仪表盘",
  "dashboard.totalConversations": "总对话",
  "dashboard.activeConversations": "进行中",
  "dashboard.todayMessages": "今日消息",
  "dashboard.aiHandled": "AI处理",

  // Conversations
  "conversations.title": "对话",
  "conversations.empty": "暂无对话",
  "conversations.selectConversation": "请选择对话",
  "conversations.sendMessage": "输入消息...",
  "conversations.send": "发送",
  "conversations.aiMode": "AI模式",
  "conversations.manualMode": "手动模式",
  "conversations.resolve": "解决",
  "conversations.backToList": "返回对话列表",

  // Customers
  "customers.title": "客户管理",
  "customers.empty": "暂无客户",
  "customers.detail": "客户详情",
  "customers.name": "姓名",
  "customers.phone": "电话",
  "customers.email": "邮箱",
  "customers.country": "国家",
  "customers.language": "语言",
  "customers.notes": "备注",
  "customers.totalBookings": "预约总数",
  "customers.totalPayments": "支付总数",

  // Bookings
  "bookings.title": "预约管理",
  "bookings.empty": "暂无预约",
  "bookings.status.all": "全部",
  "bookings.status.pending": "待处理",
  "bookings.status.confirmed": "已确认",
  "bookings.status.completed": "已完成",
  "bookings.status.cancelled": "已取消",
  "bookings.status.noshow": "未到",
  "bookings.complete": "完成处理",
  "bookings.cancelBooking": "取消预约",

  // Payments
  "payments.title": "支付管理",
  "payments.empty": "暂无支付记录",
  "payments.status.all": "全部",
  "payments.status.pending": "待处理",
  "payments.status.completed": "已完成",
  "payments.status.refunded": "已退款",
  "payments.status.cancelled": "已取消",
  "payments.amount": "金额",
  "payments.method": "支付方式",

  // Procedures
  "procedures.title": "项目管理",
  "procedures.tab.procedures": "项目列表",
  "procedures.tab.pricing": "价格管理",
  "procedures.empty": "暂无登记项目",
  "procedures.deletePrice": "删除价格",

  // CRM
  "crm.title": "CRM",
  "crm.tab.events": "CRM事件",
  "crm.tab.surveys": "满意度问卷",
  "crm.events.empty": "暂无CRM事件",
  "crm.events.cancel": "取消",
  "crm.events.cancelEvent": "取消事件",
  "crm.events.scheduled": "已计划",
  "crm.events.sent": "已发送",
  "crm.events.completed": "已完成",
  "crm.events.cancelled": "已取消",
  "crm.events.failed": "失败",
  "crm.surveys.empty": "暂无问卷数据",
  "crm.surveys.total": "问卷总数",
  "crm.surveys.avgOverall": "平均综合",
  "crm.surveys.service": "服务",
  "crm.surveys.result": "结果",
  "crm.surveys.nps": "NPS",
  "crm.surveys.revisit": "再访",

  // Analytics
  "analytics.title": "统计",
  "analytics.tab.overview": "概览",
  "analytics.tab.conversations": "对话分析",
  "analytics.tab.revenue": "营收分析",
  "analytics.tab.satisfaction": "满意度",
  "analytics.tab.ai": "AI表现",

  // Knowledge
  "knowledge.title": "知识库管理",
  "knowledge.tab.responses": "回复库",
  "knowledge.tab.terms": "医学术语",
  "knowledge.editAnswer": "编辑回复",
  "knowledge.deleteAnswer": "删除回复",
  "knowledge.deleteTerm": "删除术语",

  // AI Lab
  "aiLab.title": "AI Lab",
  "aiLab.tab.personas": "AI人设",
  "aiLab.tab.abTests": "A/B测试",
  "aiLab.tab.simulations": "模拟",

  // Settings
  "settings.title": "设置",
  "settings.tab.accounts": "通讯账号",
  "settings.tab.personas": "AI人设",
  "settings.tab.profile": "个人资料",
  "settings.copyWebhookUrl": "复制Webhook URL",
  "settings.editAccount": "编辑通讯账号",
  "settings.deleteAccount": "删除通讯账号",
  "settings.deletePersona": "删除AI人设",

  // Settlements
  "settlements.title": "结算管理",
  "settlements.empty": "暂无结算记录",

  // Pagination
  "pagination.showing": "{start}-{end}条 / 共{total}条",
  "pagination.prev": "上一页",
  "pagination.next": "下一页",

  // Error boundary
  "error.title": "发生错误",
  "error.retry": "重试",

  // Theme
  "theme.light": "浅色模式",
  "theme.dark": "深色模式",
  "theme.system": "系统设置",

  // Satisfaction labels (accessibility)
  "satisfaction.green": "非常满意",
  "satisfaction.yellow": "满意",
  "satisfaction.orange": "一般",
  "satisfaction.red": "不满意",

  // Command palette
  "command.title": "命令",
  "command.placeholder": "搜索页面...",
  "command.navigation": "页面导航",
  "command.actions": "快捷操作",
  "command.noResults": "无结果",

  // Notifications
  "notification.escalation": "升级提醒",
  "notification.satisfactionWarning": "满意度警告",
  "notification.deliveryFailed": "消息发送失败",
  "notification.quotaWarning": "LLM费用警告",
  "notification.quotaExceeded": "LLM费用超限",
  "notification.markAllRead": "全部已读",
  "notification.empty": "暂无通知",

  // AI Feedback
  "feedback.helpful": "有帮助",
  "feedback.notHelpful": "没帮助",
  "feedback.thanks": "感谢反馈",

  // LLM Usage
  "llmUsage.title": "LLM费用",
  "llmUsage.tab.summary": "月度汇总",
  "llmUsage.tab.daily": "每日趋势",
  "llmUsage.tab.quota": "预算管理",
  "llmUsage.totalCost": "总费用",
  "llmUsage.totalTokens": "总令牌数",
  "llmUsage.operation": "操作",
  "llmUsage.count": "调用次数",
  "llmUsage.inputTokens": "输入令牌",
  "llmUsage.outputTokens": "输出令牌",
  "llmUsage.cost": "费用 (USD)",
  "llmUsage.date": "日期",
  "llmUsage.quota": "月度预算",
  "llmUsage.currentUsage": "本月使用",
  "llmUsage.usagePercent": "使用率",
  "llmUsage.setQuota": "设置预算",
  "llmUsage.noQuota": "未设置预算",
};

export default zh;
