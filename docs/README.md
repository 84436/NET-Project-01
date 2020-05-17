# BT 01: Chương trình dò xổ số

-   BT cho môn `CSC10008-18CLC3`: "Mạng máy tính"
-   Họ và tên: Bùi Văn Thiện
-   MSSV: `18127221`



---



## Mô tả cây thư mục

```
./
├───dist
│       requirements.txt    :   List các thư viện ngoài (dùng cho crawler.py)
│
├───docs
│       README.md           :   File báo cáo này (bản Markdown)
│       README.pdf          :   File báo cáo này (bản PDF)
│
└───src
        server.py           :   Server
        crawler.py          :   Trình scrap trang web để lấy KQXS
        utils.py            :   Công cụ chung cho server + crawler;
                                Giá trị mặc định chung cho server + client
        client.py           :   Client
        rogue_client.py     :   Giả lập client tự động
                                (dùng để test Server)
```



## Hướng dẫn nhanh cho lần đầu chạy

File log và database được lưu trong thư mục `data` (cùng level với `src`).

1.  Chạy `crawler.py` để lấy dữ liệu về.
2.  Chạy `server.py`. `Ctrl-C` để dừng server.
3.  Chạy `client.py`. Gõ `h` (hoặc `help`) để yêu cầu hướng dẫn từ server. `Ctrl-C` để ngắt kết nối và dừng client.



---



## Mô tả chi tiết

BT này được viết bằng Python 3.8.2 trên môi trường Windows (sử dụng IDE là VSCode), có sử dụng 2 thư viện bên ngoài: `BeautifulSoup4` (parse, truy vấn và sửa đổi cây HTML/XML) và `requests` (tạo và xử lý HTTP request; thay thế cho `urllib.request`). Dữ liệu được lưu lại dưới dạng JSON (kết quả sổ xố) và plain text (log ghi lại trong quá trình chạy)

Tất cả các giao tiếp giữa 2 bên client và server đều thông qua TCP sockets được cung cấp bởi module `socket`.

Nguồn dữ liệu được cung cấp bởi [Xổ Số Đại Phát](https://xosodaiphat.com/xo-so-theo-dai.html) (kết quả xổ số) và Xổ Số Minh Ngọc (cơ cấu giải thưởng[^1] cho [Miền Bắc[^2]](https://www.minhngoc.net.vn/thong-tin/co-cau-giai-thuong-mien-bac.html), [Miền Trung](https://www.minhngoc.net.vn/thong-tin/co-cau-giai-thuong-mien-trung.html), [Miền Nam](https://www.minhngoc.net.vn/thong-tin/co-cau-giai-thuong-mien-nam.html))



### Các thành phần của Server

-   `server.py` là server chính.
    -   Mô hình xử lý của server là song song (mỗi một client kết nối tới có một process tương ứng được tạo để đáp ứng yêu cầu.)
    -   Server có 4 phần chính:
        -   Database: các hàm truy vấn file database
            -   `Province_PrintAll()` liệt kê tất cả các tỉnh (hoặc `max_count` số tỉnh, nếu có đưa thêm tham số đó vào) có mở kết quả xố số, sắp xếp theo ngày gần nhất trước
            -   `Province_PrintResult()` tra cứu và trả về kết quả xổ số của một tỉnh
            -   `PList_Search` dùng để map tên tỉnh đã được loại bỏ dấu và khoảng cách với tên tỉnh nguyên vẹn tương ứng. Dictionary này được dùng trong việc nhận yêu cầu là tên tỉnh từ phía client.
        -   Prizes: các hàm liên quan tới cơ cấu giải thưởng
            -   `Prize_Check()` kiểm tra vé của một tỉnh xác định có trúng thưởng không
            -   `Prize_Print()` định dạng kết quả nhận được từ `Prize_Check()` để cho người dùng đọc
        -   Clients: hàm làm việc với clients
            -   `client_handler()` tiếp nhận một client và bắt đầu một phiên nghe yêu cầu — đưa phản hồi
        -   main: "hàm main" của server. Xem phần **Kịch bản** để biết các bước khởi động và xử lý của server.
-   `crawler.py` là công cụ đi kèm để scrap trang web
    -   Crawler này được thiết kế để hoạt động cụ thể chỉ trên trang Xổ số Đại Phát.
    -   `PAGES` liệt kê cụ thể các trang con (và thông tin vùng miền đi kèm) tương ứng với kết quả của các tỉnh. Hiện tại có tổng cộng 41 trang con.
    -   `province_parse_site()` tải trang kết quả của một tỉnh về và trích xuất kết quả.
-   `utils.py` cung cấp những "quy ước" chung và công cụ dùng chung cho bên server liên quan đến:
    -   File:
        -   `VAR_ROOT` thống nhất chỗ các file dữ liệu được lưu
        -   `var_root_check()` tự động tạo `VAR_ROOT` nếu chưa có
        -   `DB_FILE` & `DB_LOCKFILE` chỉ tên file database và lockfile đi kèm
        -   `lockfile()` là cơ chế lockfile cơ bản để bảo vệ `db` khi có crawler chạy trong nền
        -   `LOG_FILE` chỉ tên log file
    -   Log:
        -   `log` được cài đặt để ghi log đồng thời ra log file và trên console (`stdout`)
        -   Trình ghi log này được sử dụng bởi server và crawler để thay thế cho việc `print()` các thông báo.
    -   Ngày giờ:
        -   `today` lấy thời gian hiện tại (có thể không chính xác bằng việc lấy thẳng từ `datetime.datetime.now()`, nhưng gọi `today` ở những chỗ chỉ cần thông tin ngày tháng sẽ tiện hơn)
        -   `map_weekday()` chuyển đổi quy ước weekday của Python (`0-5` là Thứ 2-7, `6` là CN) sang quy ước weekday dễ đọc hơn (`2-7` là `Thứ hai - Thứ bảy`, `1` là `Chủ nhật`)
    -   Xử lý chuỗi:
        -   `strip_accent()` được dùng để loại bỏ dấu và khoảng cách khỏi tên tỉnh (VD: `Sài Gòn` sẽ thành `SaiGon`)



### Phía client

-   `client.py` là phần giao diện (CLI) cho người dùng.
    -   Client ở đây tương đối đơn giản, chỉ có nhiệm vụ kết nối đến server và bắt đầu gửi yêu cầu — nhận kết quả
-   `rogue_client.py` giả lập client tự động để test server.
    -   Mỗi một client là một process
    -   Kịch bản của client ở đây cũng tương tự như `client.py`, nhưng client sẽ không hiện lên phản hồi của server và hành động gửi yêu cầu được thực hiện một cách ngẫu nhiên (gửi yêu cầu trợ giúp, list danh sách tỉnh, tra cứu tỉnh hoặc dò vé) với khoảng thời gian chờ giữa các yêu cầu ngẫu nhiên (từ 50ms đến 1s)
-   `utils.py` cung cấp những "quy ước" chung cho server và client:
    -   `HOST` và `PORT` chỉ định địa chỉ server bind/client kết nối đến
    -   `MSG_SIZE` chỉ định kích thước buffer nhận tin của client (`socket.socket.recv()`)



### Kịch bản

Kịch bản này là phần giải thích chi tiết của **Hướng dẫn nhanh cho lần đầu chạy**.

1.  Crawler
    -   Check coi có các crawler khác / các chương trình khác đang làm việc với file database hay không thông qua sự hiện diện của lockfile.
        -   Nếu lockfile tồn tại: dừng crawler và thông báo
        -   Nếu lockfile không tồn tại: đặt lockfile và chỉ gỡ khi crawler đã hoàn tất
    -   Kiểm tra website có truy cập được không (bằng cách thử truy cập trang chủ và xem mã của HTTP response. Nếu là `200` thì ổn; nếu không phải thì dừng lại và báo lỗi.)
    -   Gọi `province_parse_site()` đối với từng tỉnh một trong `PAGES`
    -   Lưu lại thành file dưới định dạng:
        -   Dòng đầu tiên là timestamp thời gian khi đã hoàn tất việc lấy dữ liệu
        -   Dòng thứ hai là một JSON object chứa ngày mở thưởng và kết quả xổ số tương ứng với các tỉnh
2.  Server[^3]
    -   Check sự hiện diện của lockfile
        -   Nếu lockfile tồn tại; dừng server và thông báo
        -   Trong trường hợp còn lại: server sẽ tiếp tục tới bước tiếp theo.
    -   Đọc file database
    -   Kiểm tra database có quá hạn (1 ngày) chưa: nếu có thì cảnh báo
    -   Tạo socket, bind vào địa chỉ và port có sẵn trong `utils.py`
    -   Bắt đầu vòng lặp chờ client[^4]:
        -   Server có khoảng 1 giây để nghe và accept client mới.
        -   Nếu vượt quá thời gian trên mà không có client mới, socket sẽ timeout và quay lại đầu vòng lặp
    -   Nếu có một client mới: server sẽ tạo một process là một "client handler" để tiếp nhận client mới đó
    -   Khi người dùng nhấn `Ctrl-C`: server sẽ terminate tất cả các client handlers và dừng lại.
3.  Client handler
    -   Gửi phản hồi đầu tiên cho server: địa chỉ của chính client đó
    -   Bắt đầu vòng lặp nghe yêu cầu — đưa phản hồi cho đến khi client chủ động ngắt kết nối (hoặc bản thân client handler bị terminate bởi phần main của server)
        -   Khi client yêu cầu trợ giúp (`h` hoặc `help`): gửi trợ giúp và list các tỉnh có kết quả xổ số trong 2 ngày gần đây nhất
        -   Khi client yêu cầu danh sách tất cả các tỉnh được hỗ trợ (`p` hoặc `provinces`): gửi danh sách các tỉnh nhóm và xếp theo ngày gần đây nhất trước
        -   Khi client yêu cầu  tra cứu tỉnh hoặc dò vé: thực hiện việc tra cứu và trả về kết quả như thường
4.  Client
    -   Tự động thử kết nối đến server tại địa chỉ và port có sẵn trong `utils.py`
    -   Chờ phản hồi đầu tiên của server (ở đây server sẽ trả lại chính địa chỉ của client) và đưa ra trên màn hình.
        -   Trong trường hợp nếu quá 5 giây chưa thấy server phản hồi, client sẽ tự động ngắt kết nối và dừng lại.
    -   Bắt đầu vào vòng lặp đưa yêu cầu — nghe phản hồi cho tới khi người dùng nhấn `Ctrl-C` (khi đó client sẽ ngắt kết nối và dừng lại.)



---



## Nhận xét cá nhân

-   Môi trường Linux chưa được hỗ trợ hoàn toàn do BT này chủ yếu được viết trên Windows (như đã mô tả ở trên.) Các lỗi hiện tại đã biết (đã thử trên Ubuntu 20.04 `focal` trên Python 3.7.6):
    -   Server không thể tắt được bằng `Ctrl-C`
-   Một điểm trừ của server là không có quan hệ với crawler: khi lần đầu chạy mà không có dữ liệu, server sẽ không tự động gọi crawler; khi dữ liệu đã bị hết hạn (quá 1 ngày), server chỉ cảnh báo mà không tự động gọi crawler.



[^1]: Để đơn giản hóa cách server check vé số, giải phụ đặc biệt và giải khuyến khích không được hỗ trợ. Điều này cũng đồng nghĩa kết quả trúng thưởng có được từ việc sử dụng chương trình trong BT này chỉ mang tính chất tham khảo.
[^2]: Vé số miền Bắc ngoài 6 số ngẫu nhiên còn có thêm một phần tên "kí hiệu trúng giải đặc biệt" theo định dạng `{1-2 chữ số}{2 chữ cái}`. Do đề BT không yêu cầu rõ ở điểm này nên để đơn giản hóa cách server check vé số, mã đặc biệt này sẽ bị bỏ qua.
[^3]: Thực tế phần bắt đầu của server là ở Database: server sẽ đọc file dữ liệu trước khi bắt đầu vào "main" thật sự. Việc đưa bước đọc file thành bước đầu tiên là để hỗ trợ viết/gỡ lỗi các truy vấn đến database (được thực hiện thông qua Python Interactive Console)
[^4]: Đây là một workaround (có thể là dạng busy waiting) cho việc `socket.accept()` chặn các exception như `KeyboardInterrupt` không nhận được bởi main.

