# Quy định làm việc với Autodesk Revit qua Revit MCP

Khi người dùng yêu cầu thao tác, mô hình hóa, kiểm tra dữ liệu, trích xuất thông số, hoặc tự động hóa công việc trong **Autodesk Revit**:
1. **Ưu tiên kích hoạt và sử dụng Skill `revit-mcp`**:
   - Sử dụng các công cụ MCP từ `mcp-server-for-revit` để kết nối trực tiếp với Revit đang mở qua WebSocket.
   - Truy vấn thông tin Document (`get_current_document`), kiểm tra các phần tử hiện có (`get_elements`), đọc/ghi tham số (`get_parameters`, `set_parameter`), hoặc đặt đối tượng Family/Wall/Floor/Line (`create_element`).
2. **Khi cần chạy Transaction hoặc thuật toán hình học phức tạp**:
   - Sử dụng tool `execute_code` của MCP server để thực thi script trực tiếp vào không gian bộ nhớ của Revit.
   - Kết hợp với script Dynamo (`.dyn`) và Python (`Import_ATGT_To_Revit.py`) khi xử lý rải đối tượng hạ tầng giao thông (DPC, Tôn sóng, Hàng rào).
3. **Đảm bảo tính toàn vẹn của mô hình**:
   - Kiểm tra kỹ cao độ $Z$, hướng xoay tiếp tuyến của đối tượng so với tim đường trước khi commit.
