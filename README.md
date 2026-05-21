# Hướng dẫn sử dụng Pipeline Dịch PDF

Pipeline này giúp trích xuất nội dung từ file PDF và dịch sang tiếng Việt, giữ nguyên bố cục, hình ảnh và bảng biểu.

![img](img/Screenshot%202026-05-20%20214649.png)
## Yêu cầu

- MinerU desktop
- **Python 3.10** (bắt buộc)
- Kết nối internet cho bước 3.1 (Google Translate API)

### Cài đặt thư viện

```bash
pip install deep-translator tqdm transformers torch sentencepiece playwright
playwright install chromium
```

## Quy trình

### Bước 1: Trích xuất PDF bằng MinerU Desktop

1. Tải và cài đặt **MinerU Desktop** từ trang chủ.
2. Mở MinerU, nhấn vào biểu tượng **folder** để chọn thư mục đầu ra (nơi lưu kết quả phân tích PDF).  
![img](img/Screenshot%202026-05-20%20213206.png)
3. **Kéo thả file PDF** vào cửa sổ MinerU để bắt đầu quá trình trích xuất.
4. MinerU sẽ tạo ra một thư mục chứa các file đầu ra, bao gồm:
   - `layout.json` — Thông tin bố cục trang
   - `full.md` — Nội dung Markdown đã trích xuất
   - `content_list.json` / `content_list_v2.json` — Các khối nội dung
   - `model.json` — Thông tin mô hình MinerU
   - `images/` — Hình ảnh trích xuất từ PDF

### Bước 2: Đưa dữ liệu vào thư mục input

Copy toàn bộ thư mục kết quả từ MinerU vào thư mục `input/` của dự án này.

Ví dụ: thư mục `input/plw40_description.pdf-b148f754-f533-47f0-8734-14b178721d25/` chứa `layout.json`, `images/`, ...

### Bước 3: Chạy Pipeline

Chạy các script theo thứ tự:

```bash
python 1.py    # Đánh dấu nội dung text trong layout.json bằng [N]
python 2.py    # Phân loại dòng ngắn (<10 từ) và dòng dài (>=10 từ)
python 3.1.py   # Dịch dòng ngắn qua Google Translate
python 3.2.py   # Dịch dòng dài qua mô hình VietAI/envit5-translation
python 4.py    # Ghép bản dịch trở lại layout.json
python 5.py    # Xuất HTML với bố cục giữ nguyên
python 6.py    # Chuyển HTML sang PDF (Playwright Chromium)
```

Mỗi script sẽ tự động xử lý **tất cả** các thư mục con trong `input/`.

### Kết quả

Sau khi chạy xong, mỗi thư mục PDF sẽ có:

- `temp/` — Chứa các file trung gian:
  - `1.json` — Layout đã đánh dấu
  - `1.txt` — Nội dung gốc
  - `2.1.txt`, `2.2.txt`, `2.3.txt` — Dòng ngắn, dài, file theo dõi
  - `3.1.txt`, `3.2.txt` — Bản dịch dòng ngắn, dài
  - `4.json` — Layout đã dịch
- `5.html` — HTML giữ nguyên bố cục PDF, nội dung đã dịch sang tiếng Việt
	- `6.pdf` — **File PDF cuối cùng** tái tạo từ HTML qua Chromium

### Lưu ý

- Các script dùng đường dẫn tương đối, không cần chỉnh sửa gì.
- Bước 3.1 (Google Translate) cần internet và bị giới hạn tốc độ (1 giây/lần gọi).
- Bước 3.2 (mô hình T5) cần nhiều RAM; có thể chạy rất lâu trên CPU (mã code này chỉ được viết cho việc chạy trên cpu).
- Bước 6 cần chạy `playwright install chromium` lần đầu để tải trình duyệt.
- Pipeline chỉ xử lý các thư mục có chứa `layout.json`, bỏ qua thư mục `sample/`.
