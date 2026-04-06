# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Duy Hưng
- **Student ID**: 2A202600154
- **Date**: 06/04/2026

---

## I. Technical Contribution (15 Points)

Trong dự án này, tôi tham gia cùng nhóm từ giai đoạn đề xuất ý tưởng đến triển khai hệ thống Agent.

Thảo luận & đề tài: Cùng nhóm phân tích hạn chế của chatbot (hallucination, thiếu dữ liệu real-time) và đề xuất xây dựng ReAct Agent. Tôi đóng góp ý tưởng chọn đề tài Movie Assistant vì dễ kiểm chứng và có API phù hợp.
Tìm API: Tìm hiểu và đề xuất sử dụng TMDB API, xác định các endpoint cần thiết (search, details, recommendations).
Thiết kế workflow: Tham gia xây dựng pipeline: search_movies → recommend_movie → get_details, đảm bảo Agent không tự sinh kết quả mà phải gọi tool.

---

## II. Debugging Case Study (10 Points)
### Problem Description

Trong phiên bản v1, Agent không sử dụng tool recommend_movie mà tự generate danh sách phim dựa trên kiến thức có sẵn.

Ví dụ:

User: Recommend movies like Lord of the Rings
Agent: (không gọi tool) → tự generate danh sách phim
### Log Source

Trích từ logs/2026-04-06.log:

Thought: User wants recommendation based on a movie
Action: search_movies("Lord of the Rings")
Observation: movie_id = 120

Thought: I can suggest similar movies
Action: None
Final Answer: [Generated movie list without API]
### Diagnosis

Nguyên nhân chính:

Thiếu tool chuyên biệt cho recommendation
Prompt chưa đủ mạnh để “ép” LLM phải gọi tool
LLM có xu hướng “shortcut” → trả lời luôn thay vì reasoning + action

👉 Đây là hành vi phổ biến của các model như GPT-4o khi không có constraint rõ ràng.

### Solution
1. Thiết kế tool mới
Thêm recommend_movie(movie_id)
Ép workflow:
search_movies → recommend_movie → get_details
2. Cập nhật system prompt

Bắt buộc:

“If user asks for recommendation, you MUST call recommend_movie tool”

3. Thêm logging
Track toàn bộ Thought / Action / Observation

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. Reasoning

ReAct Agent có bước Thought giúp chia nhỏ bài toán (tìm phim → lấy id → recommend), trong khi Chatbot trả lời trực tiếp. Điều này giúp Agent minh bạch và dễ kiểm soát hơn.

2. Reliability

Agent không luôn tốt hơn Chatbot:

Ưu điểm: giảm hallucination nhờ gọi API
Nhược điểm: latency cao, tốn token, có thể chọn sai tool

Trong một số trường hợp, các model như Gemini Flash vẫn cho kết quả nhanh và đủ tốt.

3. Observation

Observation (kết quả từ tool) ảnh hưởng trực tiếp đến bước tiếp theo của Agent. Nếu dữ liệu trả về đúng, Agent sẽ suy luận chính xác; ngược lại có thể dẫn đến lỗi toàn bộ pipeline.

---

## IV. Future Improvements (5 Points)

### Scalability
- Sử dụng asynchronous processing cho tool calls
- Thêm caching layer (Redis) cho movie data
- Thiết kế multi-tool routing khi số lượng tool tăng
### Safety
- Thêm tool schema validation (Pydantic)
- Xây dựng Supervisor Agent để kiểm tra output
- Giới hạn input để tránh injection vào tool
### Performance
- Giảm số bước reasoning (optimize prompt)
- Dùng hybrid approach:
  + Chatbot cho câu hỏi đơn giản
  + Agent cho câu hỏi phức tạp
  + Sử dụng vector database (RAG) để giảm số lần gọi API

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
