import type { TranslationKey } from "./ko";

const vi: Record<TranslationKey, string> = {
  // Navigation
  "nav.dashboard": "Bảng điều khiển",
  "nav.conversations": "Tin nhắn",
  "nav.customers": "Khách hàng",
  "nav.bookings": "Đặt lịch",
  "nav.payments": "Thanh toán",
  "nav.procedures": "Thủ thuật",
  "nav.crm": "CRM",
  "nav.analytics": "Thống kê",
  "nav.knowledge": "Kiến thức",
  "nav.aiLab": "AI Lab",
  "nav.settings": "Cài đặt",
  "nav.logout": "Đăng xuất",
  "nav.mainNav": "Điều hướng chính",
  "nav.openMenu": "Mở menu",
  "nav.closeMenu": "Đóng menu",
  "nav.navMenu": "Menu điều hướng",

  // Common actions
  "common.save": "Lưu",
  "common.cancel": "Hủy",
  "common.delete": "Xóa",
  "common.edit": "Sửa",
  "common.add": "Thêm",
  "common.search": "Tìm kiếm",
  "common.filter": "Lọc",
  "common.all": "Tất cả",
  "common.back": "Quay lại",
  "common.backToList": "Quay lại danh sách",
  "common.loading": "Đang tải...",
  "common.noData": "Không có dữ liệu",
  "common.error": "Đã xảy ra lỗi",
  "common.retry": "Thử lại",
  "common.confirm": "Xác nhận",
  "common.close": "Đóng",
  "common.copy": "Sao chép",
  "common.total": "Tổng",
  "common.status": "Trạng thái",

  // Auth
  "auth.login": "Đăng nhập",
  "auth.register": "Đăng ký",
  "auth.email": "Email",
  "auth.password": "Mật khẩu",
  "auth.name": "Tên",
  "auth.clinicName": "Tên phòng khám",
  "auth.clinicSlug": "Mã phòng khám",
  "auth.loginFailed": "Email hoặc mật khẩu không đúng",

  // Dashboard
  "dashboard.title": "Bảng điều khiển",
  "dashboard.totalConversations": "Tổng hội thoại",
  "dashboard.activeConversations": "Đang hoạt động",
  "dashboard.todayMessages": "Tin nhắn hôm nay",
  "dashboard.aiHandled": "AI xử lý",

  // Conversations
  "conversations.title": "Hội thoại",
  "conversations.empty": "Không có hội thoại",
  "conversations.selectConversation": "Chọn hội thoại",
  "conversations.sendMessage": "Nhập tin nhắn...",
  "conversations.send": "Gửi",
  "conversations.aiMode": "Chế độ AI",
  "conversations.manualMode": "Chế độ thủ công",
  "conversations.resolve": "Giải quyết",
  "conversations.backToList": "Quay lại danh sách hội thoại",

  // Customers
  "customers.title": "Quản lý khách hàng",
  "customers.empty": "Không có khách hàng",
  "customers.detail": "Chi tiết khách hàng",
  "customers.name": "Tên",
  "customers.phone": "Số điện thoại",
  "customers.email": "Email",
  "customers.country": "Quốc gia",
  "customers.language": "Ngôn ngữ",
  "customers.notes": "Ghi chú",
  "customers.totalBookings": "Tổng đặt lịch",
  "customers.totalPayments": "Tổng thanh toán",

  // Bookings
  "bookings.title": "Quản lý đặt lịch",
  "bookings.empty": "Không có đặt lịch",
  "bookings.status.all": "Tất cả",
  "bookings.status.pending": "Chờ xử lý",
  "bookings.status.confirmed": "Đã xác nhận",
  "bookings.status.completed": "Hoàn thành",
  "bookings.status.cancelled": "Đã hủy",
  "bookings.status.noshow": "Vắng mặt",
  "bookings.complete": "Hoàn thành",
  "bookings.cancelBooking": "Hủy đặt lịch",

  // Payments
  "payments.title": "Quản lý thanh toán",
  "payments.empty": "Không có giao dịch",
  "payments.status.all": "Tất cả",
  "payments.status.pending": "Chờ xử lý",
  "payments.status.completed": "Hoàn thành",
  "payments.status.refunded": "Hoàn tiền",
  "payments.status.cancelled": "Đã hủy",
  "payments.amount": "Số tiền",
  "payments.method": "Phương thức",

  // Procedures
  "procedures.title": "Quản lý thủ thuật",
  "procedures.tab.procedures": "Danh sách thủ thuật",
  "procedures.tab.pricing": "Quản lý giá",
  "procedures.empty": "Chưa có thủ thuật",
  "procedures.deletePrice": "Xóa giá",

  // CRM
  "crm.title": "CRM",
  "crm.tab.events": "Sự kiện CRM",
  "crm.tab.surveys": "Khảo sát hài lòng",
  "crm.events.empty": "Không có sự kiện CRM",
  "crm.events.cancel": "Hủy",
  "crm.events.cancelEvent": "Hủy sự kiện",
  "crm.events.scheduled": "Đã lên lịch",
  "crm.events.sent": "Đã gửi",
  "crm.events.completed": "Hoàn thành",
  "crm.events.cancelled": "Đã hủy",
  "crm.events.failed": "Thất bại",
  "crm.surveys.empty": "Không có dữ liệu khảo sát",
  "crm.surveys.total": "Tổng khảo sát",
  "crm.surveys.avgOverall": "Trung bình chung",
  "crm.surveys.service": "Dịch vụ",
  "crm.surveys.result": "Kết quả",
  "crm.surveys.nps": "NPS",
  "crm.surveys.revisit": "Tái khám",

  // Analytics
  "analytics.title": "Thống kê",
  "analytics.tab.overview": "Tổng quan",
  "analytics.tab.conversations": "Phân tích hội thoại",
  "analytics.tab.revenue": "Phân tích doanh thu",
  "analytics.tab.satisfaction": "Hài lòng",
  "analytics.tab.ai": "Hiệu suất AI",

  // Knowledge
  "knowledge.title": "Quản lý kiến thức",
  "knowledge.tab.responses": "Thư viện câu trả lời",
  "knowledge.tab.terms": "Thuật ngữ y khoa",
  "knowledge.editAnswer": "Sửa câu trả lời",
  "knowledge.deleteAnswer": "Xóa câu trả lời",
  "knowledge.deleteTerm": "Xóa thuật ngữ",

  // AI Lab
  "aiLab.title": "AI Lab",
  "aiLab.tab.personas": "AI Persona",
  "aiLab.tab.abTests": "A/B Test",
  "aiLab.tab.simulations": "Mô phỏng",

  // Settings
  "settings.title": "Cài đặt",
  "settings.tab.accounts": "Tài khoản nhắn tin",
  "settings.tab.personas": "AI Persona",
  "settings.tab.profile": "Hồ sơ",
  "settings.copyWebhookUrl": "Sao chép Webhook URL",
  "settings.editAccount": "Sửa tài khoản nhắn tin",
  "settings.deleteAccount": "Xóa tài khoản nhắn tin",
  "settings.deletePersona": "Xóa AI Persona",

  // Settlements
  "settlements.title": "Quản lý thanh toán",
  "settlements.empty": "Không có lịch sử thanh toán",

  // Pagination
  "pagination.showing": "{start}-{end} / tổng {total}",
  "pagination.prev": "Trước",
  "pagination.next": "Tiếp",

  // Error boundary
  "error.title": "Đã xảy ra lỗi",
  "error.retry": "Thử lại",

  // Theme
  "theme.light": "Chế độ sáng",
  "theme.dark": "Chế độ tối",
  "theme.system": "Theo hệ thống",

  // Satisfaction labels (accessibility)
  "satisfaction.green": "Rất hài lòng",
  "satisfaction.yellow": "Hài lòng",
  "satisfaction.orange": "Bình thường",
  "satisfaction.red": "Không hài lòng",

  // Command palette
  "command.title": "Lệnh",
  "command.placeholder": "Tìm trang...",
  "command.navigation": "Điều hướng",
  "command.actions": "Thao tác nhanh",
  "command.noResults": "Không có kết quả",

  // Notifications
  "notification.escalation": "Cảnh báo chuyển tiếp",
  "notification.satisfactionWarning": "Cảnh báo hài lòng",
  "notification.deliveryFailed": "Gửi tin nhắn thất bại",
  "notification.quotaWarning": "Cảnh báo chi phí LLM",
  "notification.quotaExceeded": "Vượt hạn mức LLM",
  "notification.markAllRead": "Đánh dấu đã đọc",
  "notification.empty": "Không có thông báo",

  // AI Feedback
  "feedback.helpful": "Hữu ích",
  "feedback.notHelpful": "Không hữu ích",
  "feedback.thanks": "Cảm ơn phản hồi",

  // LLM Usage
  "llmUsage.title": "Chi phí LLM",
  "llmUsage.tab.summary": "Tổng hợp tháng",
  "llmUsage.tab.daily": "Xu hướng ngày",
  "llmUsage.tab.quota": "Ngân sách",
  "llmUsage.totalCost": "Tổng chi phí",
  "llmUsage.totalTokens": "Tổng token",
  "llmUsage.operation": "Thao tác",
  "llmUsage.count": "Số lần gọi",
  "llmUsage.inputTokens": "Token đầu vào",
  "llmUsage.outputTokens": "Token đầu ra",
  "llmUsage.cost": "Chi phí (USD)",
  "llmUsage.date": "Ngày",
  "llmUsage.quota": "Ngân sách tháng",
  "llmUsage.currentUsage": "Sử dụng tháng này",
  "llmUsage.usagePercent": "Tỷ lệ sử dụng",
  "llmUsage.setQuota": "Đặt ngân sách",
  "llmUsage.noQuota": "Chưa đặt ngân sách",
};

export default vi;
